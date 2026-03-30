from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


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
