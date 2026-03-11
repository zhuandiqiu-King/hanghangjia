from unittest.mock import patch, AsyncMock


def test_login_new_user(client):
    """首次登录创建新用户"""
    mock_code2session = AsyncMock(return_value="mock_openid_001")
    with patch("app.routers.auth.wx_code2session", mock_code2session):
        resp = client.post("/api/auth/login", json={
            "code": "mock_code",
            "nickname": "小明",
            "avatar_url": "https://example.com/avatar.png",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["user"]["nickname"] == "小明"


def test_login_existing_user(client):
    """重复登录更新用户信息"""
    mock_code2session = AsyncMock(return_value="mock_openid_002")
    with patch("app.routers.auth.wx_code2session", mock_code2session):
        # 第一次登录
        resp1 = client.post("/api/auth/login", json={
            "code": "mock_code",
            "nickname": "旧昵称",
        })
        # 第二次登录更新昵称
        resp2 = client.post("/api/auth/login", json={
            "code": "mock_code",
            "nickname": "新昵称",
        })
    assert resp2.status_code == 200
    assert resp2.json()["user"]["nickname"] == "新昵称"


def test_me(client, auth_headers, test_user):
    """获取当前用户信息"""
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["nickname"] == "测试用户"


def test_me_no_token(client):
    """无 token 返回 401"""
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401
