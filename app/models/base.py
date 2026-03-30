from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Integer, String, Text, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    openid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    nickname: Mapped[str] = mapped_column(String(100), default="")
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    preferences: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: AI 对话偏好
    current_family_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("families.id", use_alter=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # 用户拥有的植物（保留向后兼容，新逻辑走 family_id）
    plants: Mapped[List["Plant"]] = relationship(
        back_populates="owner", foreign_keys="Plant.user_id"
    )
    # 家庭成员关系
    family_memberships: Mapped[List["FamilyMember"]] = relationship(
        back_populates="user", foreign_keys="FamilyMember.user_id"
    )


class Family(Base):
    """家庭组"""
    __tablename__ = "families"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    invite_code: Mapped[Optional[str]] = mapped_column(String(32), unique=True, nullable=True)
    invite_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_personal: Mapped[bool] = mapped_column(Boolean, default=False)  # 个人家庭不可解散
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # 关联
    members: Mapped[List["FamilyMember"]] = relationship(
        back_populates="family", cascade="all, delete-orphan"
    )
    plants: Mapped[List["Plant"]] = relationship(
        back_populates="family", foreign_keys="Plant.family_id"
    )


class FamilyMember(Base):
    """家庭成员关系（多对多）"""
    __tablename__ = "family_members"
    __table_args__ = (
        UniqueConstraint("family_id", "user_id", name="uq_family_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="member")  # admin / member
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    family: Mapped["Family"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="family_memberships")
