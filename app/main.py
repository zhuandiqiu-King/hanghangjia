from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.database import engine, Base, SessionLocal
from app.routers import plants, watering, auth, chat, user, family
from app.scheduler import start_scheduler, stop_scheduler

# 创建数据库表（含新增的 families、family_members）
Base.metadata.create_all(bind=engine)

# 自动迁移：为已有表补充新字段
with engine.connect() as conn:
    inspector = inspect(engine)

    # plants 表迁移
    plant_cols = [col["name"] for col in inspector.get_columns("plants")]
    if "photo_url" not in plant_cols:
        conn.execute(text("ALTER TABLE plants ADD COLUMN photo_url TEXT"))
        conn.commit()
    if "family_id" not in plant_cols:
        conn.execute(text("ALTER TABLE plants ADD COLUMN family_id INTEGER"))
        conn.commit()
    if "created_by" not in plant_cols:
        conn.execute(text("ALTER TABLE plants ADD COLUMN created_by INTEGER"))
        conn.commit()

    # users 表迁移
    user_cols = [col["name"] for col in inspector.get_columns("users")]
    if "preferences" not in user_cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN preferences TEXT"))
        conn.commit()
    if "current_family_id" not in user_cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN current_family_id INTEGER"))
        conn.commit()

    # watering_records 表迁移
    wr_cols = [col["name"] for col in inspector.get_columns("watering_records")]
    if "operator_id" not in wr_cols:
        conn.execute(text("ALTER TABLE watering_records ADD COLUMN operator_id INTEGER"))
        conn.commit()

# 数据迁移：为已有用户创建个人家庭，把植物归到家庭下
from app.models import User, Plant, Family, FamilyMember  # noqa: E402

with SessionLocal() as db:
    # 找有植物但没有个人家庭的用户
    users_with_plants = (
        db.query(User)
        .join(Plant, Plant.user_id == User.id)
        .filter(Plant.family_id.is_(None))
        .distinct()
        .all()
    )
    for u in users_with_plants:
        # 检查是否已有个人家庭
        personal = (
            db.query(Family)
            .filter(Family.created_by == u.id, Family.is_personal.is_(True))
            .first()
        )
        if not personal:
            personal = Family(
                name="我的植物",
                created_by=u.id,
                is_personal=True,
            )
            db.add(personal)
            db.flush()
            db.add(FamilyMember(family_id=personal.id, user_id=u.id, role="admin"))
            db.flush()
        # 迁移该用户的植物到个人家庭
        db.query(Plant).filter(
            Plant.user_id == u.id, Plant.family_id.is_(None)
        ).update({"family_id": personal.id, "created_by": u.id})
        # 设置当前家庭
        if not u.current_family_id:
            u.current_family_id = personal.id
    db.commit()

app = FastAPI(title="夯夯家", description="家庭生活助手服务", version="2.0.0")

app.include_router(auth.router)
app.include_router(plants.router)
app.include_router(watering.router)
app.include_router(chat.router)
app.include_router(user.router)
app.include_router(family.router)


@app.on_event("startup")
def on_startup():
    start_scheduler()


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
