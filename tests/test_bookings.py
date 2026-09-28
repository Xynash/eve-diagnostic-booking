FUTURE = "2030-01-01T10:00:00"


def test_create_booking(client, auth_headers, centre_test):
    res = client.post(
        "/bookings/",
        json={"centre_test_id": centre_test.id, "appointment_time": FUTURE},
        headers=auth_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "PENDING"
    assert float(data["amount"]) == 500


def test_create_booking_requires_auth(client, centre_test):
    res = client.post("/bookings/", json={"centre_test_id": centre_test.id, "appointment_time": FUTURE})
    assert res.status_code == 403


def test_create_booking_unknown_centre_test(client, auth_headers):
    res = client.post(
        "/bookings/",
        json={"centre_test_id": 999, "appointment_time": FUTURE},
        headers=auth_headers,
    )
    assert res.status_code == 404


def test_create_booking_in_the_past(client, auth_headers, centre_test):
    res = client.post(
        "/bookings/",
        json={"centre_test_id": centre_test.id, "appointment_time": "2020-01-01T10:00:00"},
        headers=auth_headers,
    )
    assert res.status_code == 400


def test_create_booking_invalid_body(client, auth_headers):
    res = client.post("/bookings/", json={"centre_test_id": "abc"}, headers=auth_headers)
    assert res.status_code == 422


def test_list_returns_only_own_bookings(client, booking, other_headers):
    res = client.get("/bookings/", headers=other_headers)
    assert res.status_code == 200
    assert res.json() == []


def test_get_own_booking(client, booking, auth_headers):
    res = client.get(f"/bookings/{booking['id']}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["id"] == booking["id"]


def test_get_other_users_booking_forbidden(client, booking, other_headers):
    res = client.get(f"/bookings/{booking['id']}", headers=other_headers)
    assert res.status_code == 403


def test_get_missing_booking(client, auth_headers):
    res = client.get("/bookings/999", headers=auth_headers)
    assert res.status_code == 404


def test_cancel_pending_booking(client, booking, auth_headers):
    res = client.post(f"/bookings/{booking['id']}/cancel", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "CANCELLED"


def test_cancel_twice_rejected(client, booking, auth_headers):
    client.post(f"/bookings/{booking['id']}/cancel", headers=auth_headers)
    res = client.post(f"/bookings/{booking['id']}/cancel", headers=auth_headers)
    assert res.status_code == 400


def test_cancel_other_users_booking_forbidden(client, booking, other_headers):
    res = client.post(f"/bookings/{booking['id']}/cancel", headers=other_headers)
    assert res.status_code == 403