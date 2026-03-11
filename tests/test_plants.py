from datetime import date, timedelta


def test_create_plant(client, auth_headers):
    resp = client.post("/api/plants", json={
        "name": "仙人掌",
        "watering_interval": 14,
        "category": "indoor",
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "仙人掌"
    assert data["watering_interval"] == 14
    expected = (date.today() + timedelta(days=14)).isoformat()
    assert data["next_watering_date"] == expected


def test_create_plant_validation(client, auth_headers):
    # interval 必须 > 0
    resp = client.post("/api/plants", json={
        "name": "x",
        "watering_interval": 0,
    }, headers=auth_headers)
    assert resp.status_code == 422


def test_create_plant_no_auth(client):
    """未登录不能创建植物"""
    resp = client.post("/api/plants", json={
        "name": "仙人掌",
        "watering_interval": 14,
    })
    assert resp.status_code == 401


def test_list_plants(client, auth_headers, sample_plant):
    resp = client.get("/api/plants", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_plant(client, auth_headers, sample_plant):
    pid = sample_plant["id"]
    resp = client.get(f"/api/plants/{pid}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "绿萝"


def test_get_plant_not_found(client, auth_headers):
    resp = client.get("/api/plants/999", headers=auth_headers)
    assert resp.status_code == 404


def test_update_plant(client, auth_headers, sample_plant):
    pid = sample_plant["id"]
    resp = client.put(f"/api/plants/{pid}", json={"name": "大绿萝"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "大绿萝"
    # interval 未改，next_watering_date 不变
    assert resp.json()["next_watering_date"] == sample_plant["next_watering_date"]


def test_update_plant_interval(client, auth_headers, sample_plant):
    """修改 interval 应重算 next_watering_date"""
    pid = sample_plant["id"]
    resp = client.put(f"/api/plants/{pid}", json={"watering_interval": 10}, headers=auth_headers)
    assert resp.status_code == 200
    expected = (date.today() + timedelta(days=10)).isoformat()
    assert resp.json()["next_watering_date"] == expected


def test_delete_plant(client, auth_headers, sample_plant):
    pid = sample_plant["id"]
    resp = client.delete(f"/api/plants/{pid}", headers=auth_headers)
    assert resp.status_code == 204
    # 确认已删除
    resp = client.get(f"/api/plants/{pid}", headers=auth_headers)
    assert resp.status_code == 404


def test_user_isolation(client, auth_headers, sample_plant, test_user):
    """用户 A 的植物，用户 B 看不到"""
    from tests.conftest import TestSession
    from app.models import User
    from app.auth import create_token

    # 创建用户 B
    db = TestSession()
    user_b = User(openid="test_openid_002", nickname="用户B")
    db.add(user_b)
    db.commit()
    db.refresh(user_b)
    db.close()

    headers_b = {"Authorization": f"Bearer {create_token(user_b.id)}"}

    # 用户 B 看不到用户 A 的植物
    resp = client.get("/api/plants", headers=headers_b)
    assert resp.status_code == 200
    assert len(resp.json()) == 0

    # 用户 B 访问用户 A 的植物返回 404
    pid = sample_plant["id"]
    resp = client.get(f"/api/plants/{pid}", headers=headers_b)
    assert resp.status_code == 404
