from __future__ import annotations

import os
from pathlib import Path

import pytest

# The Flask app reads OPENCOMPUTER_SECRET_KEY at import time.
os.environ.setdefault("OPENCOMPUTER_SECRET_KEY", "test-secret-not-for-production")

from app import app, _list_apps, _count_tasks, _project_root  # noqa: E402


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_project_root_points_at_the_repo() -> None:
    root = _project_root()
    assert (root / "launch_webui.py").is_file()
    assert (root / "desktop_app" / "webui" / "app.py").is_file()


def test_index_renders(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "OpenComputer" in body
    assert "<div id=" in body or "sidebar" in body.lower() or "nav" in body.lower()


def test_dashboard_api_returns_counts(client) -> None:
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.get_json()
    assert set(data) >= {"tasks", "apps", "verifiers", "runs", "env_ok", "env_msg"}
    assert isinstance(data["tasks"], int)
    assert isinstance(data["apps"], int)
    assert data["tasks"] >= 0
    assert data["apps"] >= 0
    # The task tree in this checkout should be discoverable without extra deps.
    apps = _list_apps()
    task_count, app_count = _count_tasks()
    assert data["apps"] == app_count == len(apps)
    assert data["tasks"] == task_count


def test_tasks_and_verifiers_endpoints(client) -> None:
    tasks = client.get("/api/tasks")
    assert tasks.status_code == 200
    verifiers = client.get("/api/verifiers/list")
    assert verifiers.status_code == 200


def test_secret_key_is_not_hardcoded() -> None:
    source = Path(__file__).resolve().parent / "app.py"
    text = source.read_text(encoding="utf-8")
    assert "OPENCOMPUTER_SECRET_KEY" in text
    assert 'SECRET_KEY"] = "opencomputer-desktop"' not in text


def test_focus_and_placeholder_contrast() -> None:
    css = (Path(__file__).resolve().parent / "static" / "style.css").read_text(encoding="utf-8")
    assert "input:focus-visible" in css
    assert ".btn:focus-visible" in css
    assert ".nav-item:focus-visible" in css
    assert "input::placeholder { color: #6b778a; }" in css
    assert "input::placeholder { color: #a8b2c0; }" not in css
