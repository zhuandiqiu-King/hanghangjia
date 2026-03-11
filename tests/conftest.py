import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import User
from app.auth import create_token

# 使用内存 SQLite 做测试数据库
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """每个测试前重建表"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def test_user():
    """创建测试用户"""
    db = TestSession()
    user = User(openid="test_openid_001", nickname="测试用户")
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture()
def auth_headers(test_user):
    """生成带 JWT 的认证 header"""
    token = create_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def sample_plant(client, auth_headers):
    """创建一棵示例植物并返回响应数据"""
    resp = client.post("/api/plants", json={
        "name": "绿萝",
        "watering_interval": 3,
        "category": "indoor",
        "note": "放在客厅",
    }, headers=auth_headers)
    return resp.json()
