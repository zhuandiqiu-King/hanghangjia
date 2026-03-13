"""微信订阅消息推送"""
from __future__ import annotations

import os
import time
import logging

import httpx

logger = logging.getLogger(__name__)

# access_token 缓存
_token_cache: dict = {"token": "", "expires": 0}


async def _get_access_token() -> str:
    """获取微信 access_token，缓存 2 小时"""
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires"]:
        return _token_cache["token"]

    appid = os.getenv("WX_APPID", "")
    secret = os.getenv("WX_SECRET", "")
    if not appid or not secret:
        logger.warning("WX_APPID/WX_SECRET 未配置，跳过推送")
        return ""

    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {"grant_type": "client_credential", "appid": appid, "secret": secret}

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        data = resp.json()

    if "access_token" not in data:
        logger.error("获取 access_token 失败: %s", data)
        return ""

    _token_cache["token"] = data["access_token"]
    _token_cache["expires"] = now + data.get("expires_in", 7200) - 300  # 提前 5 分钟刷新
    return _token_cache["token"]


async def send_watering_reminder(
    openid: str,
    template_id: str,
    plant_names: list[str],
    count: int,
    date_str: str,
) -> bool:
    """发送浇水提醒订阅消息"""
    token = await _get_access_token()
    if not token:
        return False

    url = f"https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={token}"

    # 拼接植物名称，最多显示 3 个
    if len(plant_names) > 3:
        names_text = "、".join(plant_names[:3]) + f" 等{count}棵"
    else:
        names_text = "、".join(plant_names)

    payload = {
        "touser": openid,
        "template_id": template_id,
        "page": "pages/plant/watering/watering",
        "data": {
            "number2": {"value": count},                          # 植物数量
            "thing4": {"value": f"{names_text}需要浇水啦"},        # 温馨提示（限 20 字）
        },
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload)
            result = resp.json()

        if result.get("errcode", 0) != 0:
            logger.warning("订阅消息发送失败 openid=%s: %s", openid, result)
            return False

        logger.info("订阅消息发送成功 openid=%s, count=%d", openid, count)
        return True
    except Exception as e:
        logger.error("发送订阅消息异常: %s", e)
        return False
