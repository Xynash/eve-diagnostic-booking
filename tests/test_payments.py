from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment
from app.models.webhook_event import WebhookEvent

SUCCESS_ROLL = "app.routers.payments.random.random"


def pay(client, headers, booking_id):
    return client.post("/payments/", json={"booking_id": booking_id}, headers=headers)


def booking_status(client, headers, booking_id):
    return client.get(f"/bookings/{booking_id}", headers=headers).json()["status"]


def test_successful_payment_confirms_booking(client, booking, auth_headers, monkeypatch):
    monkeypatch.setattr(SUCCESS_ROLL, lambda: 0.1)
    res = pay(client, auth_headers, booking["id"])
    assert res.status_code == 201
    assert res.json()["status"] == "SUCCESS"
    assert booking_status(client, auth_headers, booking["id"]) == "CONFIRMED"


def test_failed_payment_marks_booking_failed(client, booking, auth_headers, monkeypatch):
    monkeypatch.setattr(SUCCESS_ROLL, lambda: 0.95)
    res = pay(client, auth_headers, booking["id"])
    assert res.status_code == 201
    assert res.json()["status"] == "FAILED"
    assert booking_status(client, auth_headers, booking["id"]) == "FAILED"


def test_cannot_pay_twice(client, booking, auth_headers, monkeypatch):
    monkeypatch.setattr(SUCCESS_ROLL, lambda: 0.1)
    pay(client, auth_headers, booking["id"])
    res = pay(client, auth_headers, booking["id"])
    assert res.status_code == 400


def test_cannot_pay_for_cancelled_booking(client, booking, auth_headers):
    client.post(f"/bookings/{booking['id']}/cancel", headers=auth_headers)
    res = pay(client, auth_headers, booking["id"])
    assert res.status_code == 400


def test_cannot_pay_for_other_users_booking(client, booking, other_headers):
    res = pay(client, other_headers, booking["id"])
    assert res.status_code == 403


def test_pay_for_missing_booking(client, auth_headers):
    res = pay(client, auth_headers, 999)
    assert res.status_code == 404


def test_payment_requires_auth(client, booking):
    res = client.post("/payments/", json={"booking_id": booking["id"]})
    assert res.status_code == 403


def test_webhook_updates_booking(client, booking, auth_headers, monkeypatch):
    monkeypatch.setattr(SUCCESS_ROLL, lambda: 0.95)
    payment = pay(client, auth_headers, booking["id"]).json()
    assert booking_status(client, auth_headers, booking["id"]) == "FAILED"

    res = client.post(
        "/payments/webhook/",
        json={"event_id": "evt_1", "transaction_id": payment["transaction_id"], "status": "SUCCESS"},
    )
    assert res.status_code == 200
    assert res.json()["booking_status"] == "CONFIRMED"
    assert booking_status(client, auth_headers, booking["id"]) == "CONFIRMED"


def test_webhook_replay_is_idempotent(client, db, booking, auth_headers, monkeypatch):
    monkeypatch.setattr(SUCCESS_ROLL, lambda: 0.95)
    payment = pay(client, auth_headers, booking["id"]).json()
    body = {"event_id": "evt_1", "transaction_id": payment["transaction_id"], "status": "SUCCESS"}

    first = client.post("/payments/webhook/", json=body)
    second = client.post("/payments/webhook/", json=body)
    third = client.post("/payments/webhook/", json=body)

    assert first.json()["detail"] == "Webhook processed"
    assert second.json()["detail"] == "Event already processed"
    assert third.json()["detail"] == "Event already processed"
    assert db.query(WebhookEvent).count() == 1
    assert db.query(Payment).count() == 1
    assert booking_status(client, auth_headers, booking["id"]) == "CONFIRMED"


def test_webhook_replay_with_different_status_is_ignored(client, booking, auth_headers, monkeypatch):
    monkeypatch.setattr(SUCCESS_ROLL, lambda: 0.95)
    payment = pay(client, auth_headers, booking["id"]).json()
    txn = payment["transaction_id"]

    client.post("/payments/webhook/", json={"event_id": "evt_1", "transaction_id": txn, "status": "SUCCESS"})
    res = client.post("/payments/webhook/", json={"event_id": "evt_1", "transaction_id": txn, "status": "FAILED"})

    assert res.json()["detail"] == "Event already processed"
    assert booking_status(client, auth_headers, booking["id"]) == "CONFIRMED"


def test_webhook_unknown_transaction(client):
    res = client.post(
        "/payments/webhook/",
        json={"event_id": "evt_1", "transaction_id": "does-not-exist", "status": "SUCCESS"},
    )
    assert res.status_code == 404


def test_webhook_unknown_transaction_is_not_recorded(client, db):
    client.post(
        "/payments/webhook/",
        json={"event_id": "evt_1", "transaction_id": "does-not-exist", "status": "SUCCESS"},
    )
    assert db.query(WebhookEvent).count() == 0


def test_webhook_malformed_payload(client):
    res = client.post("/payments/webhook/", json={"event_id": "evt_1"})
    assert res.status_code == 422


def test_webhook_invalid_status_value(client):
    res = client.post(
        "/payments/webhook/",
        json={"event_id": "evt_1", "transaction_id": "abc", "status": "MAYBE"},
    )
    assert res.status_code == 422


def test_webhook_does_not_revive_cancelled_booking(client, db, booking, auth_headers, monkeypatch):
    monkeypatch.setattr(SUCCESS_ROLL, lambda: 0.95)
    payment = pay(client, auth_headers, booking["id"]).json()

    row = db.get(Booking, booking["id"])
    row.status = BookingStatus.CANCELLED
    db.commit()

    res = client.post(
        "/payments/webhook/",
        json={"event_id": "evt_1", "transaction_id": payment["transaction_id"], "status": "SUCCESS"},
    )
    assert res.status_code == 200
    assert res.json()["booking_status"] == "CANCELLED"
