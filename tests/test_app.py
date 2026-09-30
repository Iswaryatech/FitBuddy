import os

os.environ["DATABASE_URL"] = "sqlite:///./test_movemap.db"
os.environ["GEMINI_API_KEY"] = ""  # force the built-in generators

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app
from app.revise import revise_builtin
from app.planner import builtin_plan, normalize_plan
from app.tips import builtin_tip

FORM = dict(name="Asha", handle="asha_1", age="28", weight="62", goal="Weight loss", intensity="Medium")


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_pages_render(client):
    assert "Seven days" in client.get("/").text
    assert client.get("/coach").status_code == 200
    assert client.get("/plan/nobody").status_code == 404


def test_generate_and_view(client):
    r = client.post("/generate", data=FORM, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/plan/asha_1"
    page = client.get("/plan/asha_1")
    assert page.status_code == 200 and "Asha" in page.text and "Warm-up" in page.text
    assert page.text.count('role="tab"') == 7


def test_validation_errors(client):
    r = client.post("/generate", data={**FORM, "age": "5", "handle": "a b"})
    assert r.status_code == 422
    assert "Age should be between" in r.text and "letters, numbers" in r.text


def test_feedback_keeps_original(client):
    client.post("/generate", data=FORM)
    before = client.get("/api/plans/asha_1").json()["original_plan"]
    r = client.post("/plan/asha_1/feedback", data={"feedback": "Add more cardio and one extra rest day"})
    assert r.status_code == 200 and "What changed" in r.text
    data = client.get("/api/plans/asha_1").json()
    assert data["original_plan"] == before
    assert data["updated_plan"] and data["updated_plan"] != before
    kinds = [d["kind"] for d in data["updated_plan"]]
    assert kinds.count("recovery") > [d["kind"] for d in before].count("recovery")


def test_regenerate_replaces_plan(client):
    client.post("/generate", data=FORM)
    client.post("/plan/asha_1/feedback", data={"feedback": "make it easier"})
    client.post("/generate", data={**FORM, "goal": "Strength"})
    data = client.get("/api/plans/asha_1").json()
    assert data["updated_plan"] is None and data["member"]["goal"] == "Strength"


def test_coach_and_delete(client):
    client.post("/generate", data=FORM)
    assert "@asha_1" in client.get("/coach").text
    r = client.post("/coach/asha_1/delete", follow_redirects=False)
    assert r.status_code == 303
    assert client.get("/api/plans/asha_1").status_code == 404


def test_api_roundtrip(client):
    body = dict(name="Ravi", handle="ravi", age=40, weight=80, goal="Muscle gain", intensity="High")
    assert client.post("/api/plans", json=body).status_code == 200
    r = client.post("/api/plans/ravi/feedback", json={"feedback": "make sessions shorter"})
    assert r.status_code == 200 and r.json()["changes"]
    assert client.delete("/api/plans/ravi").json() == {"deleted": "ravi"}


@pytest.mark.parametrize("goal", ["Weight loss", "Muscle gain", "General wellness", "Strength", "Flexibility", "Cardio fitness"])
@pytest.mark.parametrize("level", ["Low", "Medium", "High"])
def test_every_goal_and_level(goal, level):
    p = {"goal": goal, "intensity": level, "age": 30, "weight": 70, "name": "T"}
    days = builtin_plan(p)
    assert len(days) == 7 and normalize_plan(days) == days
    assert any(d["kind"] == "rest" for d in days)
    assert builtin_tip(p)


def test_revise_no_match_changes_nothing():
    days = builtin_plan({"goal": "Strength", "intensity": "Low", "age": 30, "weight": 70})
    new, changes = revise_builtin(days, "I love pizza")
    assert new == days and changes == []


def test_normalize_rejects_bad_plans():
    with pytest.raises(ValueError):
        normalize_plan({"days": []})
