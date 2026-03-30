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
from app.models import User, Plant, FamilyMember
from app.services.ocr import process_pending_ocr_tasks
from app.wx_push import send_watering_reminder

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _check_and_push():
    """每分钟执行：匹配用户提醒时间，发送订阅消息（跨家庭聚合）"""
    template_id = os.getenv("WX_REMINDER_TMPL_ID", "")
    if not template_id:
        return

    now = datetime.now()
    current_hm = now.strftime("%H:%M")
    today = date.today()
    date_str = today.strftime("%Y年%m月%d日")

    db = SessionLocal()
    try:
        users = list(db.scalars(select(User)).all())
        for user in users:
            prefs = {}
            if user.preferences:
                try:
                    prefs = json.loads(user.preferences)
                except (json.JSONDecodeError, TypeError):
                    continue

            if not prefs.get("reminder_enabled", False):
                continue
            reminder_time = prefs.get("reminder_time", "06:30")
            if reminder_time != current_hm:
                continue

            # 查该用户所有家庭
            memberships = list(
                db.scalars(
                    select(FamilyMember).where(FamilyMember.user_id == user.id)
                ).all()
            )
            if not memberships:
                continue

            family_ids = [m.family_id for m in memberships]

            # 聚合所有家庭的待浇水植物
            plants = list(
                db.scalars(
                    select(Plant)
                    .where(Plant.family_id.in_(family_ids))
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


async def _run_ocr_task_worker():
    """定期从数据库取待处理 OCR 任务"""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, process_pending_ocr_tasks)


def start_scheduler():
    """启动定时任务"""
    scheduler.add_job(
        _check_and_push,
        trigger=CronTrigger(minute="*"),
        id="watering_reminder",
        replace_existing=True,
    )
    scheduler.add_job(
        _run_ocr_task_worker,
        trigger="interval",
        seconds=int(os.getenv("OCR_TASK_INTERVAL_SECONDS", "5")),
        id="ocr_task_worker",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("浇水提醒定时任务已启动")


def stop_scheduler():
    """停止定时任务"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("浇水提醒定时任务已停止")
