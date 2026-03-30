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


# ========== 背单词模块 ==========

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


# ========== 购物清单模块 ==========

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


# ========== 烹饪助手模块 ==========

class Recipe(Base):
    """菜谱"""
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    cover_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cook_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 分钟
    servings: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="easy")  # easy/medium/hard
    category: Mapped[str] = mapped_column(String(20), default="home")  # home/quick/soup/breakfast/cold/baking/baby/diet
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON 数组
    tips: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="system")  # system/family/ai
    family_id: Mapped[Optional[int]] = mapped_column(ForeignKey("families.id"), nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", use_alter=True, name="fk_recipe_created_by"), nullable=True
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    favorite_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    ingredients: Mapped[List["RecipeIngredient"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )
    steps: Mapped[List["RecipeStep"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )


class RecipeIngredient(Base):
    """菜谱食材"""
    __tablename__ = "recipe_ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 如 "3个"、"适量"
    group_name: Mapped[str] = mapped_column(String(20), default="主料")  # 主料/调料/辅料
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    recipe: Mapped["Recipe"] = relationship(back_populates="ingredients")


class RecipeStep(Base):
    """菜谱步骤"""
    __tablename__ = "recipe_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), nullable=False)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tip: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    recipe: Mapped["Recipe"] = relationship(back_populates="steps")


class RecipeFavorite(Base):
    """菜谱收藏"""
    __tablename__ = "recipe_favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "recipe_id", name="uq_user_recipe_fav"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
