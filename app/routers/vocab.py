"""背单词模块：小朋友管理、单词本 CRUD、听写、错题本、拍照录入"""
from __future__ import annotations

import json
import os
import re
import random
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import (
    User, Child, WordBook, Word,
    DictationSession, DictationResult, MistakeRecord,
    OCRTask,
)
from app.schemas import (
    ChildCreate, ChildOut,
    WordBookCreate, WordBookOut, WordBookDetailOut,
    WordCreate, WordOut, BatchWordCreate,
    DictationStartRequest, DictationSubmitRequest, DictationSessionOut,
    MistakeOut,
    OCRTaskCreateRequest, OCRTaskOut,
)

router = APIRouter(tags=["vocab"])


def _get_family_id(user: User) -> int:
    if not user.current_family_id:
        raise HTTPException(400, "请先加入一个家庭")
    return user.current_family_id


# ===== 小朋友管理 =====

@router.get("/api/children", response_model=List[ChildOut])
def list_children(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    family_id = _get_family_id(current_user)
    stmt = select(Child).where(Child.family_id == family_id).order_by(Child.created_at)
    return list(db.scalars(stmt).all())


@router.post("/api/children", response_model=ChildOut)
def create_child(
    data: ChildCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    family_id = _get_family_id(current_user)
    child = Child(family_id=family_id, name=data.name, avatar=data.avatar)
    db.add(child)
    db.commit()
    db.refresh(child)
    return child


@router.put("/api/children/{child_id}", response_model=ChildOut)
def update_child(
    child_id: int,
    data: ChildCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    family_id = _get_family_id(current_user)
    child = db.get(Child, child_id)
    if not child or child.family_id != family_id:
        raise HTTPException(404, "小朋友不存在")
    child.name = data.name
    child.avatar = data.avatar
    db.commit()
    db.refresh(child)
    return child


@router.delete("/api/children/{child_id}")
def delete_child(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    family_id = _get_family_id(current_user)
    child = db.get(Child, child_id)
    if not child or child.family_id != family_id:
        raise HTTPException(404, "小朋友不存在")
    db.delete(child)
    db.commit()
    return {"ok": True}


# ===== 单词本管理 =====

@router.get("/api/children/{child_id}/wordbooks", response_model=List[WordBookOut])
def list_wordbooks(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    family_id = _get_family_id(current_user)
    child = db.get(Child, child_id)
    if not child or child.family_id != family_id:
        raise HTTPException(404, "小朋友不存在")

    # 查单词本 + 单词数量
    stmt = (
        select(WordBook, func.count(Word.id).label("word_count"))
        .outerjoin(Word, Word.book_id == WordBook.id)
        .where(WordBook.child_id == child_id)
        .group_by(WordBook.id)
        .order_by(WordBook.created_at.desc())
    )
    results = []
    for book, count in db.execute(stmt).all():
        results.append(WordBookOut(
            id=book.id, name=book.name,
            word_count=count, created_at=book.created_at,
        ))
    return results


@router.post("/api/children/{child_id}/wordbooks", response_model=WordBookOut)
def create_wordbook(
    child_id: int,
    data: WordBookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    family_id = _get_family_id(current_user)
    child = db.get(Child, child_id)
    if not child or child.family_id != family_id:
        raise HTTPException(404, "小朋友不存在")
    book = WordBook(child_id=child_id, name=data.name)
    db.add(book)
    db.commit()
    db.refresh(book)
    return WordBookOut(id=book.id, name=book.name, word_count=0, created_at=book.created_at)


@router.delete("/api/wordbooks/{book_id}")
def delete_wordbook(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    family_id = _get_family_id(current_user)
    book = db.get(WordBook, book_id)
    if not book:
        raise HTTPException(404, "单词本不存在")
    child = db.get(Child, book.child_id)
    if not child or child.family_id != family_id:
        raise HTTPException(403, "无权操作")
    db.delete(book)
    db.commit()
    return {"ok": True}


# ===== 单词管理 =====

@router.get("/api/wordbooks/{book_id}", response_model=WordBookDetailOut)
def get_wordbook_detail(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    family_id = _get_family_id(current_user)
    book = db.get(WordBook, book_id)
    if not book:
        raise HTTPException(404, "单词本不存在")
    child = db.get(Child, book.child_id)
    if not child or child.family_id != family_id:
        raise HTTPException(403, "无权查看")
    words = list(db.scalars(
        select(Word).where(Word.book_id == book_id).order_by(Word.id)
    ).all())
    return WordBookDetailOut(
        id=book.id, name=book.name,
        word_count=len(words), created_at=book.created_at,
        words=[WordOut.model_validate(w) for w in words],
    )


@router.post("/api/wordbooks/{book_id}/words", response_model=WordOut)
def add_word(
    book_id: int,
    data: WordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    family_id = _get_family_id(current_user)
    book = db.get(WordBook, book_id)
    if not book:
        raise HTTPException(404, "单词本不存在")
    child = db.get(Child, book.child_id)
    if not child or child.family_id != family_id:
        raise HTTPException(403, "无权操作")
    word = Word(book_id=book_id, english=data.english, chinese=data.chinese, phonetic=data.phonetic)
    db.add(word)
    db.commit()
    db.refresh(word)
    return word


@router.post("/api/wordbooks/{book_id}/words/batch", response_model=List[WordOut])
def batch_add_words(
    book_id: int,
    data: BatchWordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量添加单词（拍照识别后调用）"""
    family_id = _get_family_id(current_user)
    book = db.get(WordBook, book_id)
    if not book:
        raise HTTPException(404, "单词本不存在")
    child = db.get(Child, book.child_id)
    if not child or child.family_id != family_id:
        raise HTTPException(403, "无权操作")
    results = []
    for w in data.words:
        word = Word(book_id=book_id, english=w.english, chinese=w.chinese, phonetic=w.phonetic)
        db.add(word)
        results.append(word)
    db.commit()
    for w in results:
        db.refresh(w)
    return results


@router.put("/api/words/{word_id}", response_model=WordOut)
def update_word(
    word_id: int,
    data: WordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    family_id = _get_family_id(current_user)
    word = db.get(Word, word_id)
    if not word:
        raise HTTPException(404, "单词不存在")
    book = db.get(WordBook, word.book_id)
    child = db.get(Child, book.child_id) if book else None
    if not child or child.family_id != family_id:
        raise HTTPException(403, "无权操作")
    word.english = data.english
    word.chinese = data.chinese
    word.phonetic = data.phonetic
    db.commit()
    db.refresh(word)
    return word


@router.delete("/api/words/{word_id}")
def delete_word(
    word_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    family_id = _get_family_id(current_user)
    word = db.get(Word, word_id)
    if not word:
        raise HTTPException(404, "单词不存在")
    book = db.get(WordBook, word.book_id)
    child = db.get(Child, book.child_id) if book else None
    if not child or child.family_id != family_id:
        raise HTTPException(403, "无权操作")
    db.delete(word)
    db.commit()
    return {"ok": True}


# ===== 听写 =====

@router.post("/api/children/{child_id}/dictation/start", response_model=dict)
def start_dictation(
    child_id: int,
    data: DictationStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """开始听写：返回本次听写的单词列表"""
    family_id = _get_family_id(current_user)
    child = db.get(Child, child_id)
    if not child or child.family_id != family_id:
        raise HTTPException(404, "小朋友不存在")

    # 收集候选单词
    if data.mistakes_only:
        # 仅错题
        stmt = (
            select(Word)
            .join(MistakeRecord, MistakeRecord.word_id == Word.id)
            .where(MistakeRecord.child_id == child_id)
        )
        candidates = list(db.scalars(stmt).all())
    elif data.word_ids:
        # 指定范围
        candidates = list(db.scalars(
            select(Word).where(Word.id.in_(data.word_ids))
        ).all())
    else:
        # 需要一个 book_id，从第一个单词本取（前端应传 word_ids）
        raise HTTPException(400, "请指定单词范围")

    if not candidates:
        raise HTTPException(400, "没有可听写的单词")

    # 随机抽取
    if data.count and data.count < len(candidates):
        candidates = random.sample(candidates, data.count)
    else:
        random.shuffle(candidates)

    words_out = [
        {"id": w.id, "english": w.english, "chinese": w.chinese, "phonetic": w.phonetic}
        for w in candidates
    ]
    return {"words": words_out, "total": len(words_out)}


@router.post("/api/children/{child_id}/dictation/submit", response_model=DictationSessionOut)
def submit_dictation(
    child_id: int,
    book_id: int,
    data: DictationSubmitRequest,
    mode: str = "text",
    direction: str = "en2cn",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交听写结果"""
    family_id = _get_family_id(current_user)
    child = db.get(Child, child_id)
    if not child or child.family_id != family_id:
        raise HTTPException(404, "小朋友不存在")

    correct_count = sum(1 for r in data.results if r.is_correct)

    session = DictationSession(
        child_id=child_id,
        book_id=book_id,
        mode=mode,
        direction=direction,
        total=len(data.results),
        correct=correct_count,
    )
    db.add(session)
    db.flush()

    result_details = []
    for r in data.results:
        dr = DictationResult(
            session_id=session.id,
            word_id=r.word_id,
            answer=r.answer,
            is_correct=r.is_correct,
        )
        db.add(dr)

        # 更新错题本
        if not r.is_correct:
            mistake = db.scalars(
                select(MistakeRecord).where(
                    MistakeRecord.child_id == child_id,
                    MistakeRecord.word_id == r.word_id,
                )
            ).first()
            if mistake:
                mistake.wrong_count += 1
                mistake.last_wrong_at = datetime.now()
            else:
                db.add(MistakeRecord(
                    child_id=child_id, word_id=r.word_id,
                ))

        # 查单词原文
        word = db.get(Word, r.word_id)
        result_details.append({
            "word_id": r.word_id,
            "english": word.english if word else "",
            "chinese": word.chinese if word else "",
            "answer": r.answer,
            "is_correct": r.is_correct,
        })

    db.commit()
    db.refresh(session)

    return DictationSessionOut(
        id=session.id, mode=session.mode, direction=session.direction,
        total=session.total, correct=session.correct,
        created_at=session.created_at, results=result_details,
    )


# ===== 错题本 =====

@router.get("/api/children/{child_id}/mistakes", response_model=List[MistakeOut])
def list_mistakes(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    family_id = _get_family_id(current_user)
    child = db.get(Child, child_id)
    if not child or child.family_id != family_id:
        raise HTTPException(404, "小朋友不存在")

    stmt = (
        select(MistakeRecord)
        .where(MistakeRecord.child_id == child_id)
        .order_by(MistakeRecord.wrong_count.desc())
    )
    mistakes = list(db.scalars(stmt).all())
    results = []
    for m in mistakes:
        word = db.get(Word, m.word_id)
        if not word:
            continue
        results.append(MistakeOut(
            id=m.id,
            word=WordOut.model_validate(word),
            wrong_count=m.wrong_count,
            last_wrong_at=m.last_wrong_at,
        ))
    return results


@router.delete("/api/children/{child_id}/mistakes/{mistake_id}")
def delete_mistake(
    child_id: int,
    mistake_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    family_id = _get_family_id(current_user)
    child = db.get(Child, child_id)
    if not child or child.family_id != family_id:
        raise HTTPException(404, "小朋友不存在")
    mistake = db.get(MistakeRecord, mistake_id)
    if not mistake or mistake.child_id != child_id:
        raise HTTPException(404, "记录不存在")
    db.delete(mistake)
    db.commit()
    return {"ok": True}


# ===== 听写历史 =====

@router.get("/api/children/{child_id}/dictation/history", response_model=List[DictationSessionOut])
def dictation_history(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    family_id = _get_family_id(current_user)
    child = db.get(Child, child_id)
    if not child or child.family_id != family_id:
        raise HTTPException(404, "小朋友不存在")

    stmt = (
        select(DictationSession)
        .where(DictationSession.child_id == child_id)
        .order_by(DictationSession.created_at.desc())
        .limit(20)
    )
    sessions = list(db.scalars(stmt).all())
    return [
        DictationSessionOut(
            id=s.id, mode=s.mode, direction=s.direction,
            total=s.total, correct=s.correct, created_at=s.created_at,
        )
        for s in sessions
    ]


# ===== 拍照批改 =====

class PhotoCheckRequest(BaseModel):
    image: str  # base64 图片
    words: list  # 本次听写的单词列表 [{id, english, chinese}]
    direction: str = "en2cn"  # en2cn: 用户写中文; cn2en: 用户写英文


@router.post("/api/vocab/photo-check")
def photo_check(
    req: PhotoCheckRequest,
    current_user: User = Depends(get_current_user),
):
    """拍照批改：识别用户手写内容，与正确答案对比"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise HTTPException(500, "未配置 DASHSCOPE_API_KEY")

    from openai import OpenAI

    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    image_data = req.image
    if not image_data.startswith("data:"):
        image_data = f"data:image/jpeg;base64,{image_data}"

    # 构建正确答案列表
    if req.direction == "en2cn":
        answer_list = [{"序号": i + 1, "题目": w["english"], "正确答案": w["chinese"]}
                       for i, w in enumerate(req.words)]
        user_writes = "中文"
    else:
        answer_list = [{"序号": i + 1, "题目": w["chinese"], "正确答案": w["english"]}
                       for i, w in enumerate(req.words)]
        user_writes = "英文"

    prompt = (
        f"这是一份听写批改任务。用户听到单词后在纸上写了{user_writes}答案，请识别图片中的手写内容并批改。\n\n"
        f"正确答案列表：\n{json.dumps(answer_list, ensure_ascii=False)}\n\n"
        "请按顺序识别图片中用户写的每个答案，与正确答案对比。\n"
        "返回 JSON 数组格式（不要用 markdown 代码块包裹），每个元素包含：\n"
        '- "index": 序号（从1开始）\n'
        '- "user_answer": 用户写的内容（识别结果）\n'
        '- "correct_answer": 正确答案\n'
        '- "is_correct": 布尔值，是否正确\n'
        "只返回 JSON 数组，不要其他内容。"
    )

    try:
        resp = client.chat.completions.create(
            model="qwen-vl-plus",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_data}},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
        content = resp.choices[0].message.content.strip()
        json_match = re.search(r"\[.*\]", content, re.DOTALL)
        if not json_match:
            raise ValueError(f"AI 返回无法解析: {content}")
        check_results = json.loads(json_match.group())

        # 合并单词信息
        results = []
        for i, w in enumerate(req.words):
            cr = check_results[i] if i < len(check_results) else {}
            results.append({
                "word_id": w.get("id"),
                "english": w.get("english", ""),
                "chinese": w.get("chinese", ""),
                "user_answer": cr.get("user_answer", ""),
                "correct_answer": cr.get("correct_answer", ""),
                "is_correct": cr.get("is_correct", False),
            })

        correct_count = sum(1 for r in results if r["is_correct"])
        return {
            "results": results,
            "total": len(results),
            "correct": correct_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"批改失败：{str(e)}")


def _load_task_words(task: OCRTask) -> Optional[List[dict]]:
    if not task.result:
        return None
    try:
        return json.loads(task.result)
    except json.JSONDecodeError:
        return None


@router.post("/api/vocab/ocr-tasks", response_model=dict)
def create_ocr_task(
    req: OCRTaskCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not req.image and not req.image_url:
        raise HTTPException(400, "请提供图片")

    task = OCRTask(
        user_id=current_user.id,
        status="pending",
        image_url=req.image_url,
        image_data=req.image,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"task_id": task.id}


@router.get("/api/vocab/ocr-tasks/{task_id}", response_model=OCRTaskOut)
def get_ocr_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.get(OCRTask, task_id)
    if not task or task.user_id != current_user.id:
        raise HTTPException(404, "任务不存在")

    return OCRTaskOut(
        id=task.id,
        status=task.status,
        words=_load_task_words(task),
        error=task.error,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )
