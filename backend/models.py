import numpy as np
import random
import math

import torch
import torch.nn as nn
from torch.autograd import Function
from torch.nn.utils.rnn import pad_sequence, pack_padded_sequence, pad_packed_sequence
from transformers import BertModel, BertConfig

import torch.nn.functional as F



# ════════════════════════════════════════════════════════════════════
# MMIM: MultiModal InfoMax (Han et al., EMNLP 2021)
# Adapted for our task: pre-extracted features + temporal LSTM
# Key change: replaces MISA's private/shared disentanglement with
# CPC-based MI maximization between fusion result Z and each modality.
# Reference: https://github.com/declare-lab/Multimodal-Infomax
# ════════════════════════════════════════════════════════════════════

class MMIMFusion(nn.Module):
    """Per-week multimodal fusion with CPC MI maximization and Gated Attention.

    Architecture:
      1. Project each modality to unified H-dim space (with LayerNorm)
      2. Compute modality gates: learn importance weights from data quality
      3. Fuse via MLP: [g_t*h_t, g_v*h_v, g_a*h_a] → Z  (gated fusion)
      4. CPC reverse predictors: G_m(Z) ≈ h_m  (InfoNCE contrastive loss)

    Gated Attention: dynamically weights modalities based on their 
    estimated reliability, allowing the model to down-weight noisy inputs.
    """
    def __init__(self, config):
        super().__init__()
        # 支持字典和对象两种形式
        if isinstance(config, dict):
            H = config.get('hidden_size', 64)
            self.embedding_size = config.get('embedding_size', 768)
            self.visual_size = config.get('visual_size', 768)
            self.acoustic_size = config.get('acoustic_size', 4)
            self.dropout = config.get('dropout', 0.3)
        else:
            H = config.hidden_size   # 64
            self.embedding_size = config.embedding_size
            self.visual_size = config.visual_size
            self.acoustic_size = config.acoustic_size
            self.dropout = config.dropout

        # Per-modality encoders → unified H-dim
        self.enc_t = nn.Sequential(
            nn.Linear(self.embedding_size, H), nn.LayerNorm(H), nn.ReLU())
        self.enc_v = nn.Sequential(
            nn.Linear(self.visual_size, H), nn.LayerNorm(H), nn.ReLU())
        self.enc_a = nn.Sequential(
            nn.LayerNorm(self.acoustic_size),
            nn.Linear(self.acoustic_size, H), nn.LayerNorm(H), nn.ReLU())

        # ═══════════════════════════════════════════════════════════════
        # GATED ATTENTION MECHANISM (创新点：自适应模态选择)
        # ═══════════════════════════════════════════════════════════════
        # Learn gates from modality features + cross-modal interaction
        self.gate_t = nn.Sequential(
            nn.Linear(H * 3, H), nn.ReLU(), nn.Linear(H, 1), nn.Sigmoid())
        self.gate_v = nn.Sequential(
            nn.Linear(H * 3, H), nn.ReLU(), nn.Linear(H, 1), nn.Sigmoid())
        self.gate_a = nn.Sequential(
            nn.Linear(H * 3, H), nn.ReLU(), nn.Linear(H, 1), nn.Sigmoid())

        # Fusion network: concat(gated features) → Z  [N, H*3]
        self.fusion_net = nn.Sequential(
            nn.Linear(H * 3, H * 3), nn.ReLU(), nn.Dropout(self.dropout),
            nn.Linear(H * 3, H * 3))

        # CPC reverse predictors G_m: Z → ĥ_m  (instance-level MI, MMIM §3.1)
        self.cpc_t = nn.Linear(H * 3, H)
        self.cpc_v = nn.Linear(H * 3, H)
        self.cpc_a = nn.Linear(H * 3, H)

        # Inter-modality Bimodal Alignment networks  (MMIM §3.2, Eq.4)
        # Z_xy = tanh(W_xy * [h_x; h_y] + b)  for each pair
        self.ba_tv = nn.Sequential(nn.Linear(H * 2, H), nn.Tanh())  # text-visual
        self.ba_ta = nn.Sequential(nn.Linear(H * 2, H), nn.Tanh())  # text-acoustic
        self.ba_va = nn.Sequential(nn.Linear(H * 2, H), nn.Tanh())  # visual-acoustic

    def forward(self, text_vec, image_vec, behavior_vec):
        """Forward pass with gated attention fusion.
        
        Returns:
            z: fused representation [N, 3H]
            ht, hv, ha: modality-specific features (before gating)
            gates: tuple of (gate_t, gate_v, gate_a) for analysis
        """
        # Encode each modality
        ht_raw = self.enc_t(text_vec)        # [N, H]
        hv_raw = self.enc_v(image_vec)       # [N, H]
        ha_raw = self.enc_a(behavior_vec)    # [N, H]
        
        # ═══════════════════════════════════════════════════════════════
        # GATED ATTENTION: Adaptive modality weighting
        # ═══════════════════════════════════════════════════════════════
        # Concatenate all modalities for cross-modal interaction
        concat_all = torch.cat([ht_raw, hv_raw, ha_raw], dim=-1)  # [N, 3H]
        
        # Compute gates: each gate sees all modalities to make informed decision
        gate_t = self.gate_t(concat_all)  # [N, 1]
        gate_v = self.gate_v(concat_all)  # [N, 1]
        gate_a = self.gate_a(concat_all)  # [N, 1]
        
        # Apply gates (element-wise scaling)
        ht = ht_raw * gate_t
        hv = hv_raw * gate_v
        ha = ha_raw * gate_a
        
        # Fuse gated features
        z = self.fusion_net(torch.cat([ht, hv, ha], dim=-1))  # [N, 3H]
        
        return z, ht_raw, hv_raw, ha_raw  # Return raw features for CPC loss

    @staticmethod
    def _nce(pred, target, temperature=0.1):
        """InfoNCE contrastive loss.  pred[i] should match target[i]."""
        pred_n   = F.normalize(pred,   dim=-1)
        target_n = F.normalize(target, dim=-1)
        logits   = pred_n @ target_n.T / temperature   # [N, N]
        labels   = torch.arange(logits.size(0), device=logits.device)
        return F.cross_entropy(logits, labels)

    def cpc_loss(self, z, ht, hv, ha):
        """Instance-level MI: fusion Z predicts each modality (MMIM §3.1, Eq.1-3)."""
        return (self._nce(self.cpc_t(z), ht) +
                self._nce(self.cpc_v(z), hv) +
                self._nce(self.cpc_a(z), ha))

    def ba_loss(self, ht, hv, ha):
        """Inter-modality Bimodal Alignment loss (MMIM §3.2, Eq.4-9).

        For each pair of modalities, a bimodal representation Z_xy is built
        by a small MLP over the concatenated unimodal encodings (Eq.4).
        MI between Z_xy and each constituent modality is then maximized via
        InfoNCE (Eq.5), yielding 2 terms per pair → 6 terms total:

          L_BA = I_NCE(Z_tv, h_t) + I_NCE(Z_tv, h_v)
               + I_NCE(Z_ta, h_t) + I_NCE(Z_ta, h_a)
               + I_NCE(Z_va, h_v) + I_NCE(Z_va, h_a)
        """
        z_tv = self.ba_tv(torch.cat([ht, hv], dim=-1))  # [N, H]
        z_ta = self.ba_ta(torch.cat([ht, ha], dim=-1))  # [N, H]
        z_va = self.ba_va(torch.cat([hv, ha], dim=-1))  # [N, H]
        return (self._nce(z_tv, ht) + self._nce(z_tv, hv) +
                self._nce(z_ta, ht) + self._nce(z_ta, ha) +
                self._nce(z_va, hv) + self._nce(z_va, ha))


class MMIMTemporalModel(nn.Module):
    """Temporal mental health risk model using MMIM-based per-week fusion.

    Architecture mirrors TemporalMISA but replaces MISA's disentanglement
    module with MMIMFusion.  The temporal LSTM and global-text-residual
    shortcut are kept identical for fair comparison.
    """
    def __init__(self, config, text_only=False, image_only=False, behavior_only=False,
                 use_cpc=True, use_lstm=True, use_attention=True, use_residual=True):
        super().__init__()
        # 支持字典和对象两种形式
        if isinstance(config, dict):
            self.config = config
            self.hidden_size = config.get('hidden_size', 64)
            self.embedding_size = config.get('embedding_size', 768)
            self.visual_size = config.get('visual_size', 768)
            self.acoustic_size = config.get('acoustic_size', 4)
            self.dropout = config.get('dropout', 0.3)
            self.num_classes = config.get('num_classes', 4)
        else:
            self.config = config
            self.hidden_size = config.hidden_size
            self.embedding_size = config.embedding_size
            self.visual_size = config.visual_size
            self.acoustic_size = config.acoustic_size
            self.dropout = config.dropout
            self.num_classes = config.num_classes
        
        self.text_only = text_only
        self.image_only = image_only
        self.behavior_only = behavior_only
        self.use_cpc = use_cpc
        self.use_lstm = use_lstm
        self.use_attention = use_attention
        self.use_residual = use_residual
        
        self.fusion = MMIMFusion(config)

        self.temporal_input_size  = self.hidden_size * 3   # 192
        self.temporal_hidden_size = 32

        if use_lstm:
            self.temporal_rnn = nn.LSTM(
                self.temporal_input_size, self.temporal_hidden_size,
                num_layers=1, batch_first=True)
        self.temporal_dropout = nn.Dropout(self.dropout)

        # Global text residual shortcut (same as TemporalMISA)
        if use_residual:
            self.global_text_residual = nn.Linear(
                self.embedding_size, self.temporal_hidden_size)

        self.future_predictor = nn.Linear(
            self.temporal_hidden_size if use_lstm else self.temporal_input_size, 
            self.num_classes)

    def forward(self, text_seq, image_seq, behavior_seq, lengths=None):
        B, T, _ = text_seq.shape
        
        # 单模态消融：只使用指定模态
        if self.text_only:
            image_seq = torch.zeros_like(image_seq)
            behavior_seq = torch.zeros_like(behavior_seq)
        elif self.image_only:
            text_seq = torch.zeros_like(text_seq)
            behavior_seq = torch.zeros_like(behavior_seq)
        elif self.behavior_only:
            text_seq = torch.zeros_like(text_seq)
            image_seq = torch.zeros_like(image_seq)

        # 1. Per-week MMIM fusion (flattened)
        z, ht, hv, ha = self.fusion(
            text_seq.reshape(B * T, -1),
            image_seq.reshape(B * T, -1),
            behavior_seq.reshape(B * T, -1))
        week_seq = z.view(B, T, -1)   # [B, T, 3H]

        # 2. Global text residual (masked mean over valid weeks)
        if self.use_residual:
            if lengths is not None:
                arange = torch.arange(T, device=text_seq.device).unsqueeze(0)
                mask   = (arange < lengths.to(text_seq.device).unsqueeze(1)).unsqueeze(-1).float()
                global_text = (text_seq * mask).sum(1) / lengths.float().to(text_seq.device).unsqueeze(-1).clamp(min=1)
            else:
                global_text = text_seq.mean(1)
            global_res = torch.tanh(self.global_text_residual(global_text))  # [B, 32]
        else:
            global_res = 0

        # 3. Temporal LSTM
        if self.use_lstm:
            if lengths is not None:
                lengths_sorted, sorted_idx = lengths.sort(descending=True)
                week_sorted = week_seq[sorted_idx]
                packed = pack_padded_sequence(
                    week_sorted, lengths_sorted.cpu(), batch_first=True, enforce_sorted=True)
                _, (h_n, _) = self.temporal_rnn(packed)
                last_sorted = h_n[-1]
                _, unsort_idx = sorted_idx.sort()
                last_hidden = last_sorted[unsort_idx]
            else:
                _, (h_n, _) = self.temporal_rnn(week_seq)
                last_hidden = h_n[-1]
        else:
            # 不使用 LSTM 时，使用均值池化
            if lengths is not None:
                arange = torch.arange(T, device=text_seq.device).unsqueeze(0)
                mask   = (arange < lengths.to(text_seq.device).unsqueeze(1)).unsqueeze(-1).float()
                last_hidden = (week_seq * mask).sum(1) / lengths.float().to(text_seq.device).unsqueeze(-1).clamp(min=1)
            else:
                last_hidden = week_seq.mean(1)

        # 4. Classification with global text residual
        if self.use_lstm:
            last_hidden = self.temporal_dropout(last_hidden + global_res)
        else:
            last_hidden = self.temporal_dropout(last_hidden)
        
        future_risk = self.future_predictor(last_hidden)

        return {
            'future_risk': future_risk,
            '_z': z, '_ht': ht, '_hv': hv, '_ha': ha,
        }

    def cpc_loss(self, outputs):
        """Instance-level MI loss (MMIM §3.1)."""
        if self.use_cpc:
            return self.fusion.cpc_loss(
                outputs['_z'], outputs['_ht'], outputs['_hv'], outputs['_ha'])
        else:
            return torch.tensor(0.0, device=outputs['_z'].device)

    def ba_loss(self, outputs):
        """Inter-modality Bimodal Alignment loss (MMIM §3.2, Eq.4-9)."""
        return self.fusion.ba_loss(
            outputs['_ht'], outputs['_hv'], outputs['_ha'])
