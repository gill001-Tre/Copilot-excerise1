import importlib.util
import pathlib
import copy
from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def app_module():
    # Load the src/app.py module dynamically so tests work from repo root
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    app_path = repo_root / "src" / "app.py"
    spec = importlib.util.spec_from_file_location("app_module", str(app_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Keep an original snapshot of activities to reset between tests
    original_activities = copy.deepcopy(module.activities)

    yield module

    # Teardown: restore activities to original snapshot
    module.activities.clear()
    module.activities.update(copy.deepcopy(original_activities))


def test_get_activities(app_module):
    client = TestClient(app_module.app)
    r = client.get("/activities")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data


def test_signup_success_and_duplicate(app_module):
    client = TestClient(app_module.app)
    activity = "Chess Club"
    new_email = "test.student@mergington.edu"

    # Ensure not already present
    assert new_email not in app_module.activities[activity]["participants"]

    r = client.post(f"/activities/{activity}/signup", params={"email": new_email})
    assert r.status_code == 200
    assert new_email in app_module.activities[activity]["participants"]

    # Duplicate signup should return 400
    r2 = client.post(f"/activities/{activity}/signup", params={"email": new_email})
    assert r2.status_code == 400


def test_unregister_success_and_not_signed_up(app_module):
    client = TestClient(app_module.app)
    activity = "Programming Class"
    existing = app_module.activities[activity]["participants"][0]

    # Unregister existing participant
    r = client.post(f"/activities/{activity}/unregister", params={"email": existing})
    assert r.status_code == 200
    assert existing not in app_module.activities[activity]["participants"]

    # Try to unregister again -> should be 400
    r2 = client.post(f"/activities/{activity}/unregister", params={"email": existing})
    assert r2.status_code == 400

