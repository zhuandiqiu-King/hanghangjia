"""后台 OCR 任务处理逻辑"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select

from app.database import SessionLocal
from app.models import OCRTask

logger = logging.getLogger(__name__)

PROMPT_TEXT = (
    "请识别这张图片中的单词列表，提取每个单词的英文和中文释义。\n"
    "返回 JSON 数组格式（不要用 markdown 代码块包裹），每个元素包含：\n"
    '- \"english\": 英文单词或短语\n'
    '- \"chinese\": 中文释义\n'
    '- \"phonetic\": 音标（如果图片中有，没有则为 null）\n'
    "只返回 JSON 数组，不要其他内容。示例：\n"
    '[{\"english\": \"apple\", \"chinese\": \"苹果\", \"phonetic\": \"/ˈæp.əl/\"}]'
)

DEFAULT_BATCH_SIZE = int(os.getenv("OCR_TASK_BATCH_SIZE", "1"))
PROCESSING_TTL = int(os.getenv("OCR_TASK_TTL_SECONDS", "120"))


def _prepare_image_payload(image_url: Optional[str], image_data: Optional[str]) -> str:
    if image_url:
        return image_url
    if not image_data:
        raise ValueError("任务缺少图片")
    if not image_data.startswith("data:"):
        return f"data:image/jpeg;base64,{image_data}"
    return image_data


def _run_ocr(image_payload: str) -> List[dict]:
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("未配置 DASHSCOPE_API_KEY")

    from openai import OpenAI

    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    resp = client.chat.completions.create(
        model=os.getenv("OCR_MODEL", "qwen-vl-plus"),
        timeout=int(os.getenv("OCR_MODEL_TIMEOUT", "30")),
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_payload}},
                    {"type": "text", "text": PROMPT_TEXT},
                ],
            }
        ],
    )
    content = resp.choices[0].message.content.strip()
    json_match = re.search(r"\[.*\]", content, re.DOTALL)
    if not json_match:
        raise ValueError(f"AI 返回内容无法解析: {content}")
    words = json.loads(json_match.group())

    # 规范化
    result = []
    for w in words:
        en = (w.get("english") or "").strip()
        cn = (w.get("chinese") or "").strip()
        if en and cn:
            result.append({
                "english": en,
                "chinese": cn,
                "phonetic": (w.get("phonetic") or "").strip() or None,
            })
    return result


def process_pending_ocr_tasks(batch_size: Optional[int] = None):
    """扫描待处理 OCR 任务并执行，避免阻塞前端请求"""
    db = SessionLocal()
    try:
        size = batch_size or DEFAULT_BATCH_SIZE
        stmt = (
            select(OCRTask)
            .where(OCRTask.status.in_(("pending", "processing")))
            .order_by(OCRTask.created_at)
            .limit(size)
        )
        tasks = list(db.scalars(stmt).all())

        now = datetime.now()
        for task in tasks:
            # 已在处理且未超时，则跳过，避免重复执行
            if task.status == "processing" and task.updated_at:
                if now - task.updated_at < timedelta(seconds=PROCESSING_TTL):
                    continue

            try:
                task.status = "processing"
                task.updated_at = datetime.now()
                db.add(task)
                db.commit()
                db.refresh(task)

                payload = _prepare_image_payload(task.image_url, task.image_data)
                words = _run_ocr(payload)
                task.status = "success"
                task.result = json.dumps(words, ensure_ascii=False)
                task.error = None
                task.image_data = None  # 释放存储
            except Exception as exc:  # noqa: BLE001
                task.status = "error"
                task.error = str(exc)[:500]
                logger.warning("OCR 任务 %s 失败: %s", task.id, exc)
            finally:
                task.updated_at = datetime.now()
                db.add(task)
                db.commit()
    finally:
        db.close()
