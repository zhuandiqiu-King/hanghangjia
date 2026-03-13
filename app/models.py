from __future__ import annotations

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import Integer, String, Text, Date, DateTime, Boolean, ForeignKey, UniqueConstraint
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


class Plant(Base):
    __tablename__ = "plants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    watering_interval: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(20), default="indoor")
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_watering_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
    # 旧字段，保留兼容
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    # 新字段：植物归属家庭
    family_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("families.id"), nullable=True
    )
    # 谁添加的这棵植物
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", use_alter=True, name="fk_plant_created_by"),
        nullable=True,
    )

    # 关联
    owner: Mapped[Optional["User"]] = relationship(
        back_populates="plants", foreign_keys=[user_id]
    )
    family: Mapped[Optional["Family"]] = relationship(
        back_populates="plants", foreign_keys=[family_id]
    )
    watering_records: Mapped[List["WateringRecord"]] = relationship(
        back_populates="plant", cascade="all, delete-orphan"
    )


class WateringRecord(Base):
    __tablename__ = "watering_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.id"), nullable=False)
    operator_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )  # 谁浇的水
    watered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    plant: Mapped["Plant"] = relationship(back_populates="watering_records")
    operator: Mapped[Optional["User"]] = relationship(foreign_keys=[operator_id])
