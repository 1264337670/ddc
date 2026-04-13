import json
from typing import Iterator, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import requests

from app.core.config import settings
from app.db.schemas import ChatStreamRequest

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _normalized_base_url() -> str:
    base_url = settings.siliconflow_base_url.strip().rstrip("/")
    if base_url.endswith("/chat/completions"):
        base_url = base_url[: -len("/chat/completions")]
    return base_url


def _chat_completion_url() -> str:
    return _normalized_base_url() + "/chat/completions"


@router.post("/stream")
def stream_chat(
    payload: ChatStreamRequest,
):
    if not settings.siliconflow_api_key.strip():
        raise HTTPException(status_code=500, detail="后端未配置 SILICONFLOW_API_KEY")

    history_messages: List[dict] = []
    for item in payload.history[-8:]:
        history_messages.append({"role": item.role, "content": item.content})

    messages = [
        {
            "role": "system",
            "content": settings.siliconflow_system_prompt,
        },
        *history_messages,
        {
            "role": "user",
            "content": payload.message,
        },
    ]

    def event_stream() -> Iterator[str]:
        try:
            response = requests.post(
                _chat_completion_url(),
                headers={
                    "accept": "application/json",
                    "content-type": "application/json",
                    "authorization": f"Bearer {settings.siliconflow_api_key.strip()}",
                },
                json={
                    "model": settings.siliconflow_model,
                    "messages": messages,
                    "stream": True,
                },
                stream=True,
                timeout=(15, 300),
            )
            if response.status_code != 200:
                err_text = response.text[:500]
                yield "data: " + json.dumps(
                    {
                        "type": "error",
                        "message": f"模型服务返回错误({response.status_code}): {err_text}",
                    },
                    ensure_ascii=False,
                ) + "\n\n"
                yield "data: [DONE]\n\n"
                return

            for line in response.iter_lines():
                if not line:
                    continue
                chunk_str = line.decode("utf-8").strip()
                if chunk_str.startswith("data:"):
                    chunk_str = chunk_str[5:].strip()

                if chunk_str == "[DONE]":
                    continue

                try:
                    chunk_data = json.loads(chunk_str)
                except Exception:
                    continue

                choices = chunk_data.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                content = delta.get("content")
                reasoning_content = delta.get("reasoning_content")

                if content:
                    yield "data: " + json.dumps(
                        {"type": "delta", "content": content},
                        ensure_ascii=False,
                    ) + "\n\n"
                if reasoning_content:
                    yield "data: " + json.dumps(
                        {"type": "delta", "content": reasoning_content},
                        ensure_ascii=False,
                    ) + "\n\n"

            yield "data: " + json.dumps({"type": "done"}, ensure_ascii=False) + "\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:
            yield "data: " + json.dumps(
                {"type": "error", "message": f"模型流式响应失败: {exc}"},
                ensure_ascii=False,
            ) + "\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
