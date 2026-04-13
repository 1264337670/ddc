# -*- coding: utf-8 -*-
"""
Process XiaoHongShu crawled data under red_data/ into MMIM-compatible features,
then optionally run binary inference with a trained checkpoint.

Input CSV expected columns:
- 帖子ID
- 帖子标题
- 作者
- 发帖时间 (YYYY-MM-DD HH:MM:SS)
- 帖子内容
- 图片路径 (relative path under red_data)

Output:
- processed_features_red_data.pkl
- red_data_prediction.json (if inference enabled)
"""

import os
import csv
import json
import pickle
import argparse
from datetime import datetime
from collections import defaultdict

import numpy as np
import torch
from PIL import Image
from transformers import AutoTokenizer, AutoModel, AutoImageProcessor

# Make local imports work when running from project root.
import sys
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.insert(0, SCRIPT_DIR)

from models import MMIMTemporalModel


def parse_args():
    parser = argparse.ArgumentParser(description="Process red_data for MMIM inference")
    parser.add_argument(
        "--csv-path",
        type=str,
        default=os.path.join(PROJECT_ROOT, "red_data", "user_636d16a6000000001f017f93_posts.csv"),
    )
    parser.add_argument(
        "--data-root",
        type=str,
        default=os.path.join(PROJECT_ROOT, "red_data"),
    )
    parser.add_argument(
        "--output-pkl",
        type=str,
        default=os.path.join(PROJECT_ROOT, "red_data", "processed_features_red_data.pkl"),
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=os.path.join(PROJECT_ROOT, "red_data", "red_data_prediction.json"),
    )
    parser.add_argument(
        "--checkpoint-path",
        type=str,
        default=os.path.join(PROJECT_ROOT, "MISA", "checkpoints", "task1", "best_full_model.pth"),
    )
    parser.add_argument("--text-model", type=str, default="bert-base-chinese")
    parser.add_argument("--image-model", type=str, default="google/vit-base-patch16-224-in21k")
    parser.add_argument("--max-text-len", type=int, default=256)
    parser.add_argument("--no-inference", action="store_true", help="Only build pkl, skip model prediction")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    return parser.parse_args()


def parse_datetime(dt_text):
    return datetime.strptime(dt_text.strip(), "%Y-%m-%d %H:%M:%S")


def week_id_of(dt_obj):
    iso = dt_obj.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def load_posts(csv_path):
    posts = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            posts.append(row)
    if not posts:
        raise ValueError(f"No rows found in CSV: {csv_path}")
    return posts


@torch.no_grad()
def encode_text(texts, tokenizer, model, device, max_len):
    embs = []
    model.eval()
    for text in texts:
        t = (text or "").strip()
        if not t:
            embs.append(np.zeros(768, dtype=np.float32))
            continue
        tokens = tokenizer(
            t,
            return_tensors="pt",
            truncation=True,
            max_length=max_len,
            padding=False,
        )
        tokens = {k: v.to(device) for k, v in tokens.items()}
        out = model(**tokens)
        hidden = out.last_hidden_state  # [1, L, H]
        mask = tokens["attention_mask"].unsqueeze(-1).float()
        pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1.0)
        embs.append(pooled[0].detach().cpu().numpy().astype(np.float32))
    return embs


@torch.no_grad()
def encode_images(image_paths, processor, model, device):
    embs = []
    model.eval()
    for path in image_paths:
        if not path or (not os.path.exists(path)):
            embs.append(np.zeros(768, dtype=np.float32))
            continue
        try:
            img = Image.open(path).convert("RGB")
            inputs = processor(images=img, return_tensors="pt")
            inputs = {k: v.to(device) for k, v in inputs.items()}
            out = model(**inputs)
            cls = out.last_hidden_state[:, 0, :]  # [1, H]
            embs.append(cls[0].detach().cpu().numpy().astype(np.float32))
        except Exception:
            embs.append(np.zeros(768, dtype=np.float32))
    return embs


def build_timeline_features(posts, data_root, text_tokenizer, text_model, image_processor, image_model, device, max_text_len):
    # Group posts by ISO week.
    weekly = defaultdict(list)
    for p in posts:
        dt = parse_datetime(p["发帖时间"])
        key = week_id_of(dt)
        weekly[key].append((dt, p))

    timeline = []
    for week_key in sorted(weekly.keys()):
        items = sorted(weekly[week_key], key=lambda x: x[0])

        texts = []
        image_abs_paths = []
        char_lens = []
        hours = []

        for dt, p in items:
            title = (p.get("帖子标题") or "").strip()
            body = (p.get("帖子内容") or "").strip()
            merged = f"{title} {body}".strip()
            texts.append(merged)
            char_lens.append(float(len(merged)))
            hours.append(float(dt.hour))

            rel_img = (p.get("图片路径") or "").strip()
            abs_img = os.path.join(data_root, rel_img) if rel_img else ""
            image_abs_paths.append(abs_img)

        text_embs = encode_text(texts, text_tokenizer, text_model, device, max_text_len)
        image_embs = encode_images(image_abs_paths, image_processor, image_model, device)

        text_feat = np.mean(np.vstack(text_embs), axis=0).astype(np.float32)
        image_feat = np.mean(np.vstack(image_embs), axis=0).astype(np.float32)

        # 4-dim behavior features aligned to existing training format scale.
        # [sum_text_chars, avg_text_chars, post_count, avg_post_hour]
        behavior_feat = np.asarray([
            float(np.sum(char_lens)),
            float(np.mean(char_lens) if char_lens else 0.0),
            float(len(items)),
            float(np.mean(hours) if hours else 0.0),
        ], dtype=np.float32)

        timeline.append(
            {
                "week_id": week_key,
                "text_feat": text_feat,
                "image_feat": image_feat,
                "behavior_feat": behavior_feat,
            }
        )

    return timeline


def save_features_pkl(username, timeline_features, output_pkl):
    os.makedirs(os.path.dirname(output_pkl), exist_ok=True)
    data = [{"username": username, "timeline_features": timeline_features}]
    with open(output_pkl, "wb") as f:
        pickle.dump(data, f)
    return data


class InferenceConfig:
    def __init__(self, acoustic_size=4, num_classes=2):
        self.embedding_size = 768
        self.visual_size = 768
        self.acoustic_size = acoustic_size
        self.hidden_size = 64
        self.dropout = 0.3
        self.num_classes = num_classes


def run_inference(processed_data, checkpoint_path, device):
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

    user = processed_data[0]
    timeline = user["timeline_features"]
    T = len(timeline)
    if T == 0:
        raise ValueError("Empty timeline features")

    text_seq = torch.tensor(np.stack([w["text_feat"] for w in timeline]), dtype=torch.float32).unsqueeze(0).to(device)
    image_seq = torch.tensor(np.stack([w["image_feat"] for w in timeline]), dtype=torch.float32).unsqueeze(0).to(device)
    behavior_seq = torch.tensor(np.stack([w["behavior_feat"] for w in timeline]), dtype=torch.float32).unsqueeze(0).to(device)
    lengths = torch.tensor([T], dtype=torch.long)

    cfg = InferenceConfig(acoustic_size=behavior_seq.shape[-1], num_classes=2)
    model = MMIMTemporalModel(cfg, use_residual=False).to(device)

    state = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(state, strict=True)
    model.eval()

    with torch.no_grad():
        out = model(text_seq, image_seq, behavior_seq, lengths=lengths)
        logits = out["future_risk"]
        probs = torch.softmax(logits, dim=-1)[0].detach().cpu().numpy().tolist()

    pred = int(np.argmax(probs))
    return {
        "pred_label": pred,
        "pred_name": "Clinical" if pred == 1 else "Non-Clinical",
        "prob_non_clinical": float(probs[0]),
        "prob_clinical": float(probs[1]),
    }


def main():
    args = parse_args()
    device = torch.device(args.device)

    posts = load_posts(args.csv_path)
    username = (posts[0].get("作者") or "xhs_user").strip() or "xhs_user"

    text_tokenizer = AutoTokenizer.from_pretrained(args.text_model)
    text_model = AutoModel.from_pretrained(args.text_model).to(device)
    image_processor = AutoImageProcessor.from_pretrained(args.image_model)
    image_model = AutoModel.from_pretrained(args.image_model).to(device)

    timeline_features = build_timeline_features(
        posts=posts,
        data_root=args.data_root,
        text_tokenizer=text_tokenizer,
        text_model=text_model,
        image_processor=image_processor,
        image_model=image_model,
        device=device,
        max_text_len=args.max_text_len,
    )

    processed_data = save_features_pkl(username, timeline_features, args.output_pkl)
    print(f"[OK] Saved features: {args.output_pkl}")
    print(f"[Info] user={username}, weeks={len(timeline_features)}")

    if args.no_inference:
        return

    pred = run_inference(processed_data, args.checkpoint_path, device)
    result = {
        "username": username,
        "checkpoint_path": os.path.abspath(args.checkpoint_path),
        "output_pkl": os.path.abspath(args.output_pkl),
        "prediction": pred,
    }

    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"[OK] Saved prediction json: {args.output_json}")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
