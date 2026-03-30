from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Integer, String, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Child(Base):
    """家庭中的小朋友"""
    __tablename__ = "children"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    avatar: Mapped[str] = mapped_column(String(10), default="👦")  # emoji头像
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    wordbooks: Mapped[List["WordBook"]] = relationship(
        back_populates="child", cascade="all, delete-orphan"
    )


class WordBook(Base):
    """单词本"""
    __tablename__ = "wordbooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    child: Mapped["Child"] = relationship(back_populates="wordbooks")
    words: Mapped[List["Word"]] = relationship(
        back_populates="wordbook", cascade="all, delete-orphan"
    )


class Word(Base):
    """单词"""
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("wordbooks.id"), nullable=False)
    english: Mapped[str] = mapped_column(String(200), nullable=False)
    chinese: Mapped[str] = mapped_column(String(200), nullable=False)
    phonetic: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    wordbook: Mapped["WordBook"] = relationship(back_populates="words")


class DictationSession(Base):
    """听写记录"""
    __tablename__ = "dictation_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id"), nullable=False)
    book_id: Mapped[int] = mapped_column(ForeignKey("wordbooks.id"), nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False)  # text / voice / photo
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # en2cn / cn2en
    total: Mapped[int] = mapped_column(Integer, default=0)
    correct: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    results: Mapped[List["DictationResult"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class DictationResult(Base):
    """听写每道题的结果"""
    __tablename__ = "dictation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("dictation_sessions.id"), nullable=False)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id"), nullable=False)
    answer: Mapped[str] = mapped_column(String(200), default="")
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)

    session: Mapped["DictationSession"] = relationship(back_populates="results")
    word: Mapped["Word"] = relationship()


class MistakeRecord(Base):
    """错题本"""
    __tablename__ = "mistake_records"
    __table_args__ = (
        UniqueConstraint("child_id", "word_id", name="uq_child_word_mistake"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id"), nullable=False)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id"), nullable=False)
    wrong_count: Mapped[int] = mapped_column(Integer, default=1)
    last_wrong_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    word: Mapped["Word"] = relationship()
