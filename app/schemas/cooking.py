from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum

from app.schemas.shopping import ShoppingItemCreate


class RecipeDifficultyEnum(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class RecipeCategoryEnum(str, Enum):
    home = "home"
    quick = "quick"
    soup = "soup"
    breakfast = "breakfast"
    cold = "cold"
    baking = "baking"
    baby = "baby"
    diet = "diet"


class RecipeIngredientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["鸡蛋"])
    amount: Optional[str] = Field(None, max_length=50, examples=["3个"])
    group_name: str = Field(default="主料", max_length=20)


class RecipeIngredientOut(BaseModel):
    id: int
    name: str
    amount: Optional[str]
    group_name: str
    sort_order: int

    model_config = {"from_attributes": True}


class RecipeStepCreate(BaseModel):
    step_number: int = Field(..., ge=1)
    content: str = Field(..., min_length=1, max_length=1000)
    tip: Optional[str] = Field(None, max_length=500)


class RecipeStepOut(BaseModel):
    id: int
    step_number: int
    content: str
    tip: Optional[str]
    image_url: Optional[str]

    model_config = {"from_attributes": True}


class RecipeListOut(BaseModel):
    """菜谱列表项（不含食材和步骤）"""
    id: int
    name: str
    cover_image: Optional[str]
    description: Optional[str]
    cook_time: Optional[int]
    servings: Optional[int]
    difficulty: str
    category: str
    tags: Optional[str]
    source: str
    favorite_count: int
    is_favorited: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class RecipeDetailOut(RecipeListOut):
    """菜谱详情（含食材和步骤）"""
    tips: Optional[str]
    ingredients: List[RecipeIngredientOut] = []
    steps: List[RecipeStepOut] = []
    creator_name: str = ""


class RecipeCreateRequest(BaseModel):
    """创建家庭菜谱"""
    name: str = Field(..., min_length=1, max_length=100, examples=["奶奶的红烧肉"])
    cover_image: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)
    cook_time: Optional[int] = Field(None, ge=1, le=600)
    servings: Optional[int] = Field(None, ge=1, le=20)
    difficulty: RecipeDifficultyEnum = RecipeDifficultyEnum.easy
    category: RecipeCategoryEnum = RecipeCategoryEnum.home
    tips: Optional[str] = Field(None, max_length=1000)
    ingredients: List[RecipeIngredientCreate] = Field(default=[], min_length=0)
    steps: List[RecipeStepCreate] = Field(default=[], min_length=0)


class RecipeUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    cover_image: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)
    cook_time: Optional[int] = Field(None, ge=1, le=600)
    servings: Optional[int] = Field(None, ge=1, le=20)
    difficulty: Optional[RecipeDifficultyEnum] = None
    category: Optional[RecipeCategoryEnum] = None
    tips: Optional[str] = Field(None, max_length=1000)
    ingredients: Optional[List[RecipeIngredientCreate]] = None
    steps: Optional[List[RecipeStepCreate]] = None


class CookingAddToShoppingRequest(BaseModel):
    items: List[ShoppingItemCreate] = Field(..., min_length=1)
