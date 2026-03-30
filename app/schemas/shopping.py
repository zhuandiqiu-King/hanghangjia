from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class ShoppingCategoryEnum(str, Enum):
    fresh = "fresh"
    meat = "meat"
    grain = "grain"
    snack = "snack"
    daily = "daily"
    other = "other"


class ShoppingItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["西红柿"])
    quantity: Optional[str] = Field(None, max_length=50, examples=["2斤"])
    price: Optional[float] = Field(None, ge=0)
    category: ShoppingCategoryEnum = ShoppingCategoryEnum.other
    note: Optional[str] = Field(None, max_length=200)


class ShoppingItemBatchCreate(BaseModel):
    items: List[ShoppingItemCreate] = Field(..., min_length=1)


class ShoppingItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    quantity: Optional[str] = Field(None, max_length=50)
    price: Optional[float] = Field(None, ge=0)
    category: Optional[ShoppingCategoryEnum] = None
    note: Optional[str] = Field(None, max_length=200)


class ShoppingItemOut(BaseModel):
    id: int
    name: str
    quantity: Optional[str]
    price: Optional[float]
    category: str
    note: Optional[str]
    is_bought: bool
    bought_by: Optional[int]
    bought_at: Optional[datetime]
    buyer_name: str = ""
    created_by: int
    creator_name: str = ""
    created_at: datetime

    model_config = {"from_attributes": True}


class ShoppingListOut(BaseModel):
    id: int
    name: str
    status: str
    created_at: datetime
    items: List[ShoppingItemOut] = []

    model_config = {"from_attributes": True}


class ShoppingHistoryOut(BaseModel):
    id: int
    name: str
    archived_at: Optional[datetime]
    item_count: int = 0
    total_price: Optional[float] = None
    items: List[ShoppingItemOut] = []

    model_config = {"from_attributes": True}


class FrequentItemOut(BaseModel):
    id: int
    name: str
    category: str
    buy_count: int
    last_bought_at: datetime

    model_config = {"from_attributes": True}


class FrequentAddToListRequest(BaseModel):
    item_ids: List[int] = Field(..., min_length=1)
