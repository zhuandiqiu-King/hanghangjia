from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ChildCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, examples=["小明"])
    avatar: str = Field(default="👦", max_length=10)


class ChildOut(BaseModel):
    id: int
    name: str
    avatar: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WordCreate(BaseModel):
    english: str = Field(..., min_length=1, max_length=200)
    chinese: str = Field(..., min_length=1, max_length=200)
    phonetic: Optional[str] = None


class WordOut(BaseModel):
    id: int
    english: str
    chinese: str
    phonetic: Optional[str]

    model_config = {"from_attributes": True}


class WordBookCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["Unit 1"])


class WordBookOut(BaseModel):
    id: int
    name: str
    word_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class WordBookDetailOut(WordBookOut):
    words: List[WordOut] = []


class BatchWordCreate(BaseModel):
    words: List[WordCreate] = Field(..., min_length=1)


class DictationStartRequest(BaseModel):
    mode: str = Field(..., pattern="^(text|voice|photo)$")
    direction: str = Field(..., pattern="^(en2cn|cn2en)$")
    word_ids: List[int] = Field(default=[], description="指定单词ID列表，为空则全部")
    count: Optional[int] = Field(default=None, gt=0, le=100, description="随机抽取数量")
    mistakes_only: bool = Field(default=False, description="仅错题")


class DictationResultSubmit(BaseModel):
    word_id: int
    answer: str = ""
    is_correct: bool = False


class DictationSubmitRequest(BaseModel):
    results: List[DictationResultSubmit]


class DictationSessionOut(BaseModel):
    id: int
    mode: str
    direction: str
    total: int
    correct: int
    created_at: datetime
    results: List[dict] = []

    model_config = {"from_attributes": True}


class MistakeOut(BaseModel):
    id: int
    word: WordOut
    wrong_count: int
    last_wrong_at: datetime

    model_config = {"from_attributes": True}
