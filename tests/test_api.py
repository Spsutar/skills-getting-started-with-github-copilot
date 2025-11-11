import copy
import pytest
from fastapi.testclient import TestClient
from src import app as _app


@pytest.fixture
def client():
    return TestClient(_app.app)


@pytest.fixture(autouse=True)
def reset_activities():
    # Snapshot the activities dict and restore after each test to avoid cross-test pollution
    orig = copy.deepcopy(_app.activities)
    yield
    _app.activities.clear()
    _app.activities.update(orig)


def test_get_activities(client):
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # A couple of known activities should be present
    assert "Chess Club" in data
    assert "Programming Class" in data


def test_signup_and_delete_flow(client):
    email = "pytest.user@mergington.edu"

    # Ensure not present initially
    activities = client.get("/activities").json()
    assert email not in activities["Programming Class"]["participants"]

    # Sign up
    r = client.post("/activities/Programming Class/signup", params={"email": email})
    assert r.status_code == 200
    assert "Signed up" in r.json().get("message", "")

    activities = client.get("/activities").json()
    assert email in activities["Programming Class"]["participants"]

    # Duplicate signup should fail
    r_dup = client.post("/activities/Programming Class/signup", params={"email": email})
    assert r_dup.status_code == 400

    # Remove the participant
    r_del = client.delete("/activities/Programming Class/participants", params={"email": email})
    assert r_del.status_code == 200
    assert "Removed" in r_del.json().get("message", "")

    activities = client.get("/activities").json()
    assert email not in activities["Programming Class"]["participants"]


def test_delete_nonexistent_participant_returns_404(client):
    r = client.delete("/activities/Chess Club/participants", params={"email": "nobody@mergington.edu"})
    assert r.status_code == 404
