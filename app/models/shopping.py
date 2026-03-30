from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Integer, String, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ShoppingList(Base):
    """购物清单"""
    __tablename__ = "shopping_lists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), default="购物清单")
    status: Mapped[str] = mapped_column(String(20), default="active")  # active / archived
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    items: Mapped[List["ShoppingItem"]] = relationship(
        back_populates="shopping_list", cascade="all, delete-orphan"
    )


class ShoppingItem(Base):
    """购物项"""
    __tablename__ = "shopping_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    list_id: Mapped[int] = mapped_column(ForeignKey("shopping_lists.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 如 "2斤"
    price: Mapped[Optional[float]] = mapped_column(nullable=True)
    category: Mapped[str] = mapped_column(String(20), default="other")  # fresh/meat/grain/snack/daily/other
    note: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_bought: Mapped[bool] = mapped_column(Boolean, default=False)
    bought_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    bought_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    shopping_list: Mapped["ShoppingList"] = relationship(back_populates="items")
    buyer: Mapped[Optional["User"]] = relationship(foreign_keys=[bought_by])
    creator: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by])


class FrequentItem(Base):
    """常买商品（系统自动统计）"""
    __tablename__ = "frequent_items"
    __table_args__ = (
        UniqueConstraint("family_id", "name", name="uq_family_frequent_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(20), default="other")
    buy_count: Mapped[int] = mapped_column(Integer, default=1)
    last_bought_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
