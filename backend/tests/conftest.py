"""Shared pytest fixtures."""
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_gateway.db"

import pytest
from fastapi.testclient import TestClient

from app.db.session import Base, engine
from app.main import app


@pytest.fixture(scope="function", autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def org_and_key(client):
    org_resp = client.post("/v1/admin/organizations", json={"name": "Test Org", "privacy_policy": "strict"})
    org_data = org_resp.json()
    token = org_data["admin_token"]
    key_resp = client.post(
        "/v1/admin/api-keys",
        json={"label": "test"},
        headers={"Authorization": f"Bearer {token}"},
    )
    api_key = key_resp.json()["key"]
    return {"org_id": org_data["org_id"], "admin_token": token, "api_key": api_key}
