import copy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module

client = TestClient(app_module.app)
original_activities = copy.deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def restore_activities():
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(original_activities))
    yield
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(original_activities))


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code in (307, 308)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_list():
    response = client.get("/activities")
    data = response.json()

    assert response.status_code == 200
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"], dict)
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_for_activity_adds_participant():
    email = "tester@mergington.edu"
    activity_name = "Chess Club"

    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    data = response.json()

    assert response.status_code == 200
    assert data["message"] == f"Signed up {email} for {activity_name}"

    activities_response = client.get("/activities").json()
    assert email in activities_response[activity_name]["participants"]


def test_signup_duplicate_returns_400():
    email = "duplicate@mergington.edu"
    activity_name = "Chess Club"

    first_response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert first_response.status_code == 200

    second_response = client.post(f"/activities/{activity_name}/signup?email={email}")
    data = second_response.json()

    assert second_response.status_code == 400
    assert data["detail"] == "Student already signed up for this activity"


def test_remove_participant_unregisters_activity():
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    response = client.delete(f"/activities/{activity_name}/participants?email={email}")
    data = response.json()

    assert response.status_code == 200
    assert data["message"] == f"Unregistered {email} from {activity_name}"

    activities_response = client.get("/activities").json()
    assert email not in activities_response[activity_name]["participants"]


def test_remove_nonexistent_participant_returns_404():
    activity_name = "Chess Club"
    email = "notfound@mergington.edu"

    response = client.delete(f"/activities/{activity_name}/participants?email={email}")
    data = response.json()

    assert response.status_code == 404
    assert data["detail"] == "Participant not found for this activity"
