"""定时任务：每日浇水提醒推送"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import date, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.database import SessionLocal
from app.models import User, Plant
from app.wx_push import send_watering_reminder

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _check_and_push():
    """每分钟执行：匹配用户提醒时间，发送订阅消息"""
    template_id = os.getenv("WX_REMINDER_TMPL_ID", "")
    if not template_id:
        return  # 未配置模板则跳过

    now = datetime.now()
    current_hm = now.strftime("%H:%M")  # 如 "06:30"
    today = date.today()
    date_str = today.strftime("%Y年%m月%d日")

    db = SessionLocal()
    try:
        # 查所有用户
        users = list(db.scalars(select(User)).all())
        for user in users:
            prefs = {}
            if user.preferences:
                try:
                    prefs = json.loads(user.preferences)
                except (json.JSONDecodeError, TypeError):
                    continue

            # 检查是否开启提醒 + 时间匹配
            if not prefs.get("reminder_enabled", False):
                continue
            reminder_time = prefs.get("reminder_time", "06:30")
            if reminder_time != current_hm:
                continue

            # 查待浇水植物
            plants = list(
                db.scalars(
                    select(Plant)
                    .where(Plant.user_id == user.id)
                    .where(Plant.next_watering_date <= today)
                ).all()
            )
            if not plants:
                continue

            plant_names = [p.name for p in plants]
            await send_watering_reminder(
                openid=user.openid,
                template_id=template_id,
                plant_names=plant_names,
                count=len(plants),
                date_str=date_str,
            )
    except Exception as e:
        logger.error("定时推送异常: %s", e)
    finally:
        db.close()


def start_scheduler():
    """启动定时任务"""
    scheduler.add_job(
        _check_and_push,
        trigger=CronTrigger(minute="*"),  # 每分钟检查
        id="watering_reminder",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("浇水提醒定时任务已启动")


def stop_scheduler():
    """停止定时任务"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("浇水提醒定时任务已停止")
