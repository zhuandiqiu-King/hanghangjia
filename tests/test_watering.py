from datetime import date, timedelta

from tests.conftest import TestSession
from app.models import Plant


def _make_overdue_plant(user_id=None):
    """直接写入一棵逾期植物到数据库"""
    db = TestSession()
    plant = Plant(
        name="逾期兰花",
        watering_interval=2,
        category="indoor",
        next_watering_date=date.today() - timedelta(days=1),
        user_id=user_id,
    )
    db.add(plant)
    db.commit()
    db.refresh(plant)
    db.close()
    return plant


def test_water_plant(client, auth_headers, sample_plant):
    pid = sample_plant["id"]
    resp = client.post(f"/api/plants/{pid}/water", headers=auth_headers)
    assert resp.status_code == 201
    record = resp.json()
    assert record["plant_id"] == pid

    # 验证 next_watering_date 已更新
    plant = client.get(f"/api/plants/{pid}", headers=auth_headers).json()
    expected = (date.today() + timedelta(days=3)).isoformat()
    assert plant["next_watering_date"] == expected


def test_water_plant_not_found(client, auth_headers):
    resp = client.post("/api/plants/999/water", headers=auth_headers)
    assert resp.status_code == 404


def test_reminders_empty(client, auth_headers, sample_plant):
    """新植物不在提醒列表中"""
    resp = client.get("/api/reminders", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_reminders_with_overdue(client, auth_headers, test_user):
    """逾期植物应出现在提醒列表"""
    plant = _make_overdue_plant(user_id=test_user.id)
    resp = client.get("/api/reminders", headers=auth_headers)
    assert resp.status_code == 200
    names = [p["name"] for p in resp.json()]
    assert "逾期兰花" in names


def test_watering_records(client, auth_headers, sample_plant):
    pid = sample_plant["id"]
    # 浇两次水
    client.post(f"/api/plants/{pid}/water", headers=auth_headers)
    client.post(f"/api/plants/{pid}/water", headers=auth_headers)

    resp = client.get(f"/api/plants/{pid}/records", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_watering_records_not_found(client, auth_headers):
    resp = client.get("/api/plants/999/records", headers=auth_headers)
    assert resp.status_code == 404
