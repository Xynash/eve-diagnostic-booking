import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.core.database import Base, get_db
from app.main import app
from app.models.centre import Centre
from app.models.centre_test import CentreTest
from app.models.test import Test as DiagnosticTest

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def login_headers(client, email):
    client.post("/auth/signup", json={"email": email, "password": "secret123"})
    res = client.post("/auth/login", json={"email": email, "password": "secret123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture()
def auth_headers(client):
    return login_headers(client, "a@example.com")


@pytest.fixture()
def other_headers(client):
    return login_headers(client, "b@example.com")


@pytest.fixture()
def centre_test(db):
    centre = Centre(name="Apollo Diagnostics", location="Delhi")
    test = DiagnosticTest(name="Complete Blood Count")
    db.add_all([centre, test])
    db.commit()
    link = CentreTest(centre_id=centre.id, test_id=test.id, price=500)
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@pytest.fixture()
def booking(client, auth_headers, centre_test):
    res = client.post(
        "/bookings/",
        json={"centre_test_id": centre_test.id, "appointment_time": "2030-01-01T10:00:00"},
        headers=auth_headers,
    )
    return res.json()