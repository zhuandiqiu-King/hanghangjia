"""微信登录相关接口"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import WxLoginRequest, LoginResponse, UserOut
from app.auth import wx_code2session, create_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(req: WxLoginRequest, db: Session = Depends(get_db)):
    """微信登录：code → openid → 查/创建用户 → 返回 JWT"""
    openid = await wx_code2session(req.code)

    # 查找或创建用户
    user = db.scalars(select(User).where(User.openid == openid)).first()
    if user is None:
        user = User(openid=openid, nickname=req.nickname, avatar_url=req.avatar_url)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # 更新昵称和头像
        if req.nickname:
            user.nickname = req.nickname
        if req.avatar_url:
            user.avatar_url = req.avatar_url
        db.commit()
        db.refresh(user)

    token = create_token(user.id)
    return LoginResponse(token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return current_user
