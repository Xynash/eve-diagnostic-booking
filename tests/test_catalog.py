FUTURE = "2030-01-01T10:00:00"


def make_centre(client, headers, name="City Lab", location="Noida"):
    return client.post("/centres/", json={"name": name, "location": location}, headers=headers).json()


def make_test(client, headers, name="Vitamin D"):
    return client.post("/tests/", json={"name": name}, headers=headers).json()


def test_create_centre_requires_auth(client):
    res = client.post("/centres/", json={"name": "City Lab", "location": "Noida"})
    assert res.status_code == 403


def test_create_centre(client, auth_headers):
    res = client.post("/centres/", json={"name": "City Lab", "location": "Noida"}, headers=auth_headers)
    assert res.status_code == 201
    assert res.json()["name"] == "City Lab"
    assert res.json()["tests"] == []


def test_create_centre_invalid_body(client, auth_headers):
    res = client.post("/centres/", json={"name": "", "location": "Noida"}, headers=auth_headers)
    assert res.status_code == 422


def test_create_test(client, auth_headers):
    res = client.post("/tests/", json={"name": "Vitamin D"}, headers=auth_headers)
    assert res.status_code == 201
    assert res.json()["name"] == "Vitamin D"


def test_create_test_requires_auth(client):
    res = client.post("/tests/", json={"name": "Vitamin D"})
    assert res.status_code == 403


def test_list_tests(client, auth_headers):
    make_test(client, auth_headers)
    res = client.get("/tests/")
    assert res.status_code == 200
    assert [t["name"] for t in res.json()] == ["Vitamin D"]


def test_add_test_to_centre(client, auth_headers):
    centre = make_centre(client, auth_headers)
    test = make_test(client, auth_headers)

    res = client.post(
        f"/centres/{centre['id']}/tests",
        json={"test_id": test["id"], "price": "650.00"},
        headers=auth_headers,
    )
    assert res.status_code == 201
    assert res.json()["test"]["name"] == "Vitamin D"
    assert float(res.json()["price"]) == 650

    listed = client.get(f"/centres/{centre['id']}").json()
    assert len(listed["tests"]) == 1


def test_add_same_test_twice_conflict(client, auth_headers):
    centre = make_centre(client, auth_headers)
    test = make_test(client, auth_headers)
    body = {"test_id": test["id"], "price": "650.00"}

    client.post(f"/centres/{centre['id']}/tests", json=body, headers=auth_headers)
    res = client.post(f"/centres/{centre['id']}/tests", json=body, headers=auth_headers)
    assert res.status_code == 409


def test_add_test_to_missing_centre(client, auth_headers):
    test = make_test(client, auth_headers)
    res = client.post("/centres/999/tests", json={"test_id": test["id"], "price": "650.00"}, headers=auth_headers)
    assert res.status_code == 404


def test_add_missing_test_to_centre(client, auth_headers):
    centre = make_centre(client, auth_headers)
    res = client.post(f"/centres/{centre['id']}/tests", json={"test_id": 999, "price": "650.00"}, headers=auth_headers)
    assert res.status_code == 404


def test_add_test_negative_price(client, auth_headers):
    centre = make_centre(client, auth_headers)
    test = make_test(client, auth_headers)
    res = client.post(
        f"/centres/{centre['id']}/tests",
        json={"test_id": test["id"], "price": "-5"},
        headers=auth_headers,
    )
    assert res.status_code == 422


def test_booking_response_includes_centre_and_test(booking):
    assert booking["centre_name"] == "Apollo Diagnostics"
    assert booking["centre_location"] == "Delhi"
    assert booking["test_name"] == "Complete Blood Count"


def test_booking_on_api_created_catalog(client, auth_headers):
    centre = make_centre(client, auth_headers)
    test = make_test(client, auth_headers)
    link = client.post(
        f"/centres/{centre['id']}/tests",
        json={"test_id": test["id"], "price": "650.00"},
        headers=auth_headers,
    ).json()

    res = client.post(
        "/bookings/",
        json={"centre_test_id": link["id"], "appointment_time": FUTURE},
        headers=auth_headers,
    )
    assert res.status_code == 201
    assert res.json()["centre_name"] == "City Lab"
    assert res.json()["test_name"] == "Vitamin D"
    assert float(res.json()["amount"]) == 650
