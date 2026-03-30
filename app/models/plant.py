from __future__ import annotations

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


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
