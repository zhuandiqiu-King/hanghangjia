"""用户信息与偏好接口"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.auth import get_current_user
from app.schemas import UserProfileOut, UserProfileUpdate

router = APIRouter(prefix="/api/user", tags=["user"])


def _is_profile_complete(user: User) -> bool:
    """判断用户是否已完善个人信息"""
    has_real_avatar = bool(user.avatar_url) and not user.avatar_url.startswith("emoji:")
    has_nickname = bool(user.nickname)
    return has_real_avatar and has_nickname


@router.get("/profile", response_model=UserProfileOut)
def get_profile(current_user: User = Depends(get_current_user)):
    """获取用户信息（含偏好设置）"""
    prefs = {}
    if current_user.preferences:
        try:
            prefs = json.loads(current_user.preferences)
        except (json.JSONDecodeError, TypeError):
            pass

    return UserProfileOut(
        id=current_user.id,
        nickname=current_user.nickname,
        avatar_url=current_user.avatar_url,
        preferences=prefs,
        is_profile_complete=_is_profile_complete(current_user),
    )


@router.put("/profile", response_model=UserProfileOut)
def update_profile(
    req: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新用户昵称、头像、偏好设置"""
    if req.nickname is not None:
        current_user.nickname = req.nickname
    if req.avatar_url is not None:
        current_user.avatar_url = req.avatar_url
    if req.preferences is not None:
        current_user.preferences = json.dumps(req.preferences, ensure_ascii=False)

    db.commit()
    db.refresh(current_user)

    prefs = {}
    if current_user.preferences:
        try:
            prefs = json.loads(current_user.preferences)
        except (json.JSONDecodeError, TypeError):
            pass

    return UserProfileOut(
        id=current_user.id,
        nickname=current_user.nickname,
        avatar_url=current_user.avatar_url,
        preferences=prefs,
        is_profile_complete=_is_profile_complete(current_user),
    )
