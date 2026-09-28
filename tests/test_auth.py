def test_signup_creates_user(client):
    res = client.post("/auth/signup", json={"email": "a@example.com", "password": "secret123"})
    assert res.status_code == 201
    assert res.json()["email"] == "a@example.com"
    assert "password" not in res.json()


def test_signup_duplicate_email(client):
    body = {"email": "a@example.com", "password": "secret123"}
    client.post("/auth/signup", json=body)
    res = client.post("/auth/signup", json=body)
    assert res.status_code == 400


def test_signup_short_password(client):
    res = client.post("/auth/signup", json={"email": "a@example.com", "password": "123"})
    assert res.status_code == 422


def test_signup_invalid_email(client):
    res = client.post("/auth/signup", json={"email": "not-an-email", "password": "secret123"})
    assert res.status_code == 422


def test_login_returns_token(client):
    body = {"email": "a@example.com", "password": "secret123"}
    client.post("/auth/signup", json=body)
    res = client.post("/auth/login", json=body)
    assert res.status_code == 200
    assert res.json()["token_type"] == "bearer"
    assert res.json()["access_token"]


def test_login_wrong_password(client):
    client.post("/auth/signup", json={"email": "a@example.com", "password": "secret123"})
    res = client.post("/auth/login", json={"email": "a@example.com", "password": "wrongpass"})
    assert res.status_code == 401


def test_protected_route_without_token(client):
    res = client.get("/bookings/")
    assert res.status_code == 403


def test_protected_route_with_garbage_token(client):
    res = client.get("/bookings/", headers={"Authorization": "Bearer not.a.token"})
    assert res.status_code == 401