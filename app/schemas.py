from __future__ import annotations

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class CategoryEnum(str, Enum):
    indoor = "indoor"
    outdoor = "outdoor"


# --- Plant schemas ---

class PlantCreate(BaseModel):
    name: str = Field(..., max_length=100, examples=["绿萝"])
    watering_interval: int = Field(..., gt=0, le=365, examples=[7])
    category: CategoryEnum = CategoryEnum.indoor
    note: Optional[str] = None
    photo_url: Optional[str] = None


class PlantUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    watering_interval: Optional[int] = Field(None, gt=0, le=365)
    category: Optional[CategoryEnum] = None
    note: Optional[str] = None
    photo_url: Optional[str] = None


class PlantOut(BaseModel):
    id: int
    name: str
    watering_interval: int
    category: str
    note: Optional[str]
    photo_url: Optional[str]
    next_watering_date: date
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- WateringRecord schemas ---

class WateringRecordOut(BaseModel):
    id: int
    plant_id: int
    watered_at: datetime

    model_config = {"from_attributes": True}


# --- Auth schemas ---

class WxLoginRequest(BaseModel):
    code: str
    nickname: str = ""
    avatar_url: Optional[str] = None


class UserOut(BaseModel):
    id: int
    nickname: str
    avatar_url: Optional[str]

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    token: str
    user: UserOut
    is_new_user: bool = False


# --- Chat schemas ---

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, examples=["绿萝叶子发黄怎么办？"])


class ChatResponse(BaseModel):
    reply: str


class VoiceChatRequest(BaseModel):
    audio_url: str = Field(..., examples=["https://xxx.com/voice.mp3"])


class VoiceChatResponse(BaseModel):
    text: str     # 语音识别出的文字
    reply: str    # AI 回复


# --- User profile schemas ---

class UserProfileOut(BaseModel):
    id: int
    nickname: str
    avatar_url: Optional[str]
    preferences: dict = {}
    is_profile_complete: bool = False

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    nickname: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None
    preferences: Optional[dict] = None


# --- Family schemas ---

class FamilyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["我的小家"])


class FamilyOut(BaseModel):
    id: int
    name: str
    is_personal: bool = False
    created_at: datetime
    member_count: int = 0
    my_role: str = "member"  # 当前用户在此家庭的角色


class FamilyMemberOut(BaseModel):
    id: int
    user_id: int
    nickname: str = ""
    avatar_url: Optional[str] = None
    role: str = "member"
    joined_at: datetime


class FamilyDetailOut(FamilyOut):
    members: List[FamilyMemberOut] = []


class InviteOut(BaseModel):
    invite_code: str
    expires_at: datetime


class JoinFamilyRequest(BaseModel):
    invite_code: str = Field(..., min_length=1, max_length=32)


class SwitchFamilyRequest(BaseModel):
    family_id: int


class TransferAdminRequest(BaseModel):
    target_user_id: int


# --- 背单词 schemas ---

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


# --- Shopping schemas ---

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


# --- Cooking schemas ---

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
