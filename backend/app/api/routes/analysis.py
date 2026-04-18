import os
import pickle
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.show_config import get_demo_result
from app.db.models import User
from app.db.schemas import AnalysisPrediction, AnalysisRunResponse

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CHECKPOINT_PATH = os.path.join(BACKEND_ROOT, "best_full_model.pth")
PKL_DIR = os.path.join(BACKEND_ROOT, "pkl")
FRONT_PUBLIC_DIR = os.path.abspath(os.path.join(BACKEND_ROOT, "..", "dczzq", "public"))
MAX_TEXT_LEN = 256

_RUNTIME_CACHE: Dict[str, Any] = {}


def _collect_user_analysis_assets(user_id: int) -> Dict[str, Any]:
    show_dir = os.path.join(FRONT_PUBLIC_DIR, "show", str(user_id))
    word_dir = os.path.join(FRONT_PUBLIC_DIR, "word", str(user_id))

    images: List[str] = []
    if os.path.isdir(show_dir):
        candidates = []
        for name in os.listdir(show_dir):
            lower = name.lower()
            if lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
                candidates.append(name)
        for name in sorted(candidates):
            images.append(f"/show/{user_id}/{name}")

    wordcloud_url = ""
    if os.path.isdir(word_dir):
        candidates = []
        for name in os.listdir(word_dir):
            lower = name.lower()
            if lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
                candidates.append(name)
        if candidates:
            wordcloud_url = f"/word/{user_id}/{sorted(candidates)[0]}"

    return {
        "show_images": images,
        "wordcloud_url": wordcloud_url,
        "has_assets": bool(images or wordcloud_url),
    }


def _get_runtime() -> Dict[str, Any]:
    if _RUNTIME_CACHE:
        return _RUNTIME_CACHE

    if not os.path.exists(CHECKPOINT_PATH):
        raise HTTPException(status_code=500, detail="缺少 best_full_model.pth 权重文件")

    try:
        import numpy as np
        import torch
        from models import MMIMTemporalModel
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"推理依赖加载失败: {exc}")

    try:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        text_tokenizer = None
        text_model = None
        image_processor = None
        image_model = None
        image_module = None

        if settings.analysis_use_hf_encoders:
            from PIL import Image
            from transformers import AutoImageProcessor, AutoModel, AutoTokenizer

            text_model_source = settings.analysis_text_model_dir.strip() or settings.analysis_text_model_name
            image_model_source = settings.analysis_image_model_dir.strip() or settings.analysis_image_model_name
            local_files_only = settings.analysis_hf_local_files_only

            text_tokenizer = AutoTokenizer.from_pretrained(text_model_source, local_files_only=local_files_only)
            text_model = AutoModel.from_pretrained(text_model_source, local_files_only=local_files_only).to(device)
            text_model.eval()

            image_processor = AutoImageProcessor.from_pretrained(image_model_source, local_files_only=local_files_only)
            image_model = AutoModel.from_pretrained(image_model_source, local_files_only=local_files_only).to(device)
            image_model.eval()
            image_module = Image

        cfg = {
            "embedding_size": 768,
            "visual_size": 768,
            "acoustic_size": 4,
            "hidden_size": 64,
            "dropout": 0.3,
            "num_classes": 2,
        }
        mmim_model = MMIMTemporalModel(cfg, use_residual=False).to(device)
        state = torch.load(CHECKPOINT_PATH, map_location=device)
        mmim_model.load_state_dict(state, strict=True)
        mmim_model.eval()
    except Exception as exc:
        detail = f"模型初始化失败: {exc}"
        if settings.analysis_use_hf_encoders and settings.analysis_hf_local_files_only:
            detail += "。当前已启用本地离线模式，请确认本地模型目录已下载并配置 ANALYSIS_TEXT_MODEL_DIR / ANALYSIS_IMAGE_MODEL_DIR。"
        raise HTTPException(status_code=500, detail=detail)

    _RUNTIME_CACHE.update(
        {
            "np": np,
            "torch": torch,
            "Image": image_module,
            "device": device,
            "text_tokenizer": text_tokenizer,
            "text_model": text_model,
            "image_processor": image_processor,
            "image_model": image_model,
            "mmim_model": mmim_model,
        }
    )
    return _RUNTIME_CACHE


def _resolve_image_path(image_path: str) -> str:
    raw = str(image_path or "").strip()
    if not raw:
        return ""
    if os.path.isabs(raw) and os.path.exists(raw):
        return raw
    candidates = [
        os.path.join(BACKEND_ROOT, raw),
        os.path.join(os.path.dirname(BACKEND_ROOT), raw),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return ""


def _encode_texts(texts: List[str], runtime: Dict[str, Any]) -> List[Any]:
    torch = runtime["torch"]
    np = runtime["np"]
    tokenizer = runtime["text_tokenizer"]
    model = runtime["text_model"]
    device = runtime["device"]

    if tokenizer is None or model is None:
        return [np.zeros(768, dtype=np.float32) for _ in texts]

    embeddings: List[Any] = []

    with torch.no_grad():
        for text in texts:
            value = (text or "").strip()
            if not value:
                embeddings.append(np.zeros(768, dtype=np.float32))
                continue
            tokens = tokenizer(
                value,
                return_tensors="pt",
                truncation=True,
                max_length=MAX_TEXT_LEN,
                padding=False,
            )
            tokens = {k: v.to(device) for k, v in tokens.items()}
            out = model(**tokens)
            hidden = out.last_hidden_state
            mask = tokens["attention_mask"].unsqueeze(-1).float()
            pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1.0)
            embeddings.append(pooled[0].detach().cpu().numpy().astype(np.float32))

    return embeddings


def _encode_images(image_paths: List[str], runtime: Dict[str, Any]) -> List[Any]:
    torch = runtime["torch"]
    np = runtime["np"]
    image = runtime["Image"]
    processor = runtime["image_processor"]
    model = runtime["image_model"]
    device = runtime["device"]

    if image is None or processor is None or model is None:
        return [np.zeros(768, dtype=np.float32) for _ in image_paths]

    embeddings: List[Any] = []

    with torch.no_grad():
        for path in image_paths:
            if not path or not os.path.exists(path):
                embeddings.append(np.zeros(768, dtype=np.float32))
                continue
            try:
                img = image.open(path).convert("RGB")
                inputs = processor(images=img, return_tensors="pt")
                inputs = {k: v.to(device) for k, v in inputs.items()}
                out = model(**inputs)
                cls = out.last_hidden_state[:, 0, :]
                embeddings.append(cls[0].detach().cpu().numpy().astype(np.float32))
            except Exception:
                embeddings.append(np.zeros(768, dtype=np.float32))

    return embeddings


def _normalize_timeline_from_pkl(raw_data: Any, runtime: Dict[str, Any]) -> List[Dict[str, Any]]:
    np = runtime["np"]

    if isinstance(raw_data, list) and raw_data and isinstance(raw_data[0], dict) and "timeline_features" in raw_data[0]:
        timeline = raw_data[0]["timeline_features"]
    elif isinstance(raw_data, dict) and "timeline_features" in raw_data:
        timeline = raw_data["timeline_features"]
    elif isinstance(raw_data, list):
        timeline = raw_data
    else:
        raise HTTPException(status_code=400, detail="pkl格式不正确，需包含 timeline_features")

    normalized: List[Dict[str, Any]] = []
    for index, item in enumerate(timeline):
        if not isinstance(item, dict):
            continue

        text_feat = item.get("text_feat")
        image_feat = item.get("image_feat")
        behavior_feat = item.get("behavior_feat")

        if text_feat is None or image_feat is None or behavior_feat is None:
            raise HTTPException(status_code=400, detail=f"pkl中第{index + 1}条数据缺少 text_feat/image_feat/behavior_feat")

        normalized.append(
            {
                "week_id": str(item.get("week_id") or f"W{index + 1:02d}"),
                "text_feat": np.asarray(text_feat, dtype=np.float32),
                "image_feat": np.asarray(image_feat, dtype=np.float32),
                "behavior_feat": np.asarray(behavior_feat, dtype=np.float32),
            }
        )

    if not normalized:
        raise HTTPException(status_code=400, detail="pkl中没有可用的 timeline_features")
    return normalized


def _run_inference(timeline_features: List[Dict[str, Any]], runtime: Dict[str, Any]) -> AnalysisPrediction:
    torch = runtime["torch"]
    np = runtime["np"]
    device = runtime["device"]
    model = runtime["mmim_model"]

    if not timeline_features:
        raise HTTPException(status_code=400, detail="帖子时间线为空，无法推理")

    text_seq = torch.tensor(np.stack([w["text_feat"] for w in timeline_features]), dtype=torch.float32).unsqueeze(0).to(device)
    image_seq = torch.tensor(np.stack([w["image_feat"] for w in timeline_features]), dtype=torch.float32).unsqueeze(0).to(device)
    behavior_seq = torch.tensor(np.stack([w["behavior_feat"] for w in timeline_features]), dtype=torch.float32).unsqueeze(0).to(device)
    lengths = torch.tensor([len(timeline_features)], dtype=torch.long)

    with torch.no_grad():
        out = model(text_seq, image_seq, behavior_seq, lengths=lengths)
        probs = torch.softmax(out["future_risk"], dim=-1)[0].detach().cpu().numpy().tolist()

    pred_label = int(np.argmax(probs))
    return AnalysisPrediction(
        pred_label=pred_label,
        pred_name="Clinical" if pred_label == 1 else "Non-Clinical",
        prob_non_clinical=float(probs[0]),
        prob_clinical=float(probs[1]),
    )


@router.post("/run", response_model=AnalysisRunResponse)
def run_user_analysis(
    current_user: User = Depends(get_current_user),
) -> AnalysisRunResponse:
    demo_result = get_demo_result(int(current_user.id))
    if demo_result is not None:
        return AnalysisRunResponse(
            user_id=demo_result.user_id,
            post_count=demo_result.post_count,
            health_score=demo_result.health_score,
            prediction=AnalysisPrediction(
                pred_label=demo_result.pred_label,
                pred_name=demo_result.pred_name,
                prob_non_clinical=demo_result.prob_non_clinical,
                prob_clinical=demo_result.prob_clinical,
            ),
            source="show_config",
        )

    runtime = _get_runtime()

    pkl_path = os.path.join(PKL_DIR, f"{current_user.id}.pkl")
    if not os.path.exists(pkl_path):
        raise HTTPException(status_code=400, detail="小红书数据还未审核完成，请耐心等待")

    try:
        with open(pkl_path, "rb") as fp:
            raw_data = pickle.load(fp)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"读取pkl失败: {exc}")

    timeline_features = _normalize_timeline_from_pkl(raw_data, runtime)
    prediction = _run_inference(timeline_features, runtime)

    score = round(float(prediction.prob_non_clinical) * 100.0, 2)
    return AnalysisRunResponse(
        user_id=int(current_user.id),
        post_count=len(timeline_features),
        health_score=score,
        prediction=prediction,
        source="model",
    )


@router.get("/assets/me")
def get_my_analysis_assets(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    assets = _collect_user_analysis_assets(int(current_user.id))
    return {
        "user_id": int(current_user.id),
        "show_images": assets["show_images"],
        "wordcloud_url": assets["wordcloud_url"],
        "has_assets": assets["has_assets"],
    }
