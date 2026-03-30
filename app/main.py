import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.database import engine, Base
from app.routers import plants, watering, auth, chat, user, family, vocab, shopping, cooking, tts
from app.scheduler import start_scheduler, stop_scheduler

logger = logging.getLogger(__name__)

app = FastAPI(title="夯夯家", description="家庭生活助手服务", version="2.0.0")

app.include_router(auth.router)
app.include_router(plants.router)
app.include_router(watering.router)
app.include_router(chat.router)
app.include_router(user.router)
app.include_router(family.router)
app.include_router(vocab.router)
app.include_router(shopping.router)
app.include_router(cooking.router)
app.include_router(tts.router)


def _run_migrations():
    """建表 + 自动迁移补字段"""
    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        inspector = inspect(engine)

        # plants 表迁移
        plant_cols = [col["name"] for col in inspector.get_columns("plants")]
        for col in ("photo_url", "family_id", "created_by"):
            if col not in plant_cols:
                conn.execute(text(f"ALTER TABLE plants ADD COLUMN {col} {'INTEGER' if col != 'photo_url' else 'TEXT'}"))
                conn.commit()

        # users 表迁移
        user_cols = [col["name"] for col in inspector.get_columns("users")]
        for col in ("preferences", "current_family_id"):
            if col not in user_cols:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {'INTEGER' if col == 'current_family_id' else 'TEXT'}"))
                conn.commit()

        # watering_records 表迁移
        wr_cols = [col["name"] for col in inspector.get_columns("watering_records")]
        if "operator_id" not in wr_cols:
            conn.execute(text("ALTER TABLE watering_records ADD COLUMN operator_id INTEGER"))
            conn.commit()

    logger.info("数据库迁移完成")


@app.on_event("startup")
def on_startup():
    _run_migrations()
    start_scheduler()
    # 导入预置菜谱（延迟导入，避免启动时加载大模块）
    from app.seed_recipes import seed
    seed()


@app.on_event("shutdown")
def on_shutdown():
    stop_scheduler()


# 静态文件目录
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def root():
    """返回 H5 交互页面"""
    return FileResponse(STATIC_DIR / "index.html")
