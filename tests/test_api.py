import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    with TestClient(app) as c:
        yield c


def test_hello(client):
    r = client.get("/hello")
    assert r.status_code == 200
    assert r.text == "Hello World 3"


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "database": "ok"}


def test_create_and_get_task(client):
    r = client.post("/tasks", json={"title": "Estudar DevSecOps", "description": "Trivy"})
    assert r.status_code == 201
    task = r.json()
    assert task["title"] == "Estudar DevSecOps"
    assert task["done"] is False

    r = client.get(f"/tasks/{task['id']}")
    assert r.status_code == 200
    assert r.json() == task


def test_list_tasks(client):
    client.post("/tasks", json={"title": "A"})
    client.post("/tasks", json={"title": "B"})
    r = client.get("/tasks")
    assert r.status_code == 200
    assert [t["title"] for t in r.json()] == ["A", "B"]


def test_update_task(client):
    task_id = client.post("/tasks", json={"title": "A"}).json()["id"]
    r = client.put(f"/tasks/{task_id}", json={"title": "A2", "description": "x", "done": True})
    assert r.status_code == 200
    assert r.json()["title"] == "A2"
    assert r.json()["done"] is True


def test_delete_task(client):
    task_id = client.post("/tasks", json={"title": "A"}).json()["id"]
    assert client.delete(f"/tasks/{task_id}").status_code == 204
    assert client.get(f"/tasks/{task_id}").status_code == 404


@pytest.mark.parametrize(
    "method, body",
    [("get", None), ("put", {"title": "x"}), ("delete", None)],
)
def test_task_not_found(client, method, body):
    r = client.request(method, "/tasks/999", json=body)
    assert r.status_code == 404


def test_create_task_invalid(client):
    assert client.post("/tasks", json={"title": ""}).status_code == 422
    assert client.post("/tasks", json={}).status_code == 422


def test_import_tasks_csv(client):
    csv_content = "title,description\nTarefa 1,primeira\nTarefa 2,\n"
    r = client.post("/tasks/import", files={"file": ("tarefas.csv", csv_content, "text/csv")})
    assert r.status_code == 201
    assert [t["title"] for t in r.json()] == ["Tarefa 1", "Tarefa 2"]
    assert len(client.get("/tasks").json()) == 2


@pytest.mark.parametrize(
    "content",
    [b"title,description\n", b"title,description\n,sem titulo\n", b"\xff\xfe\x00"],
)
def test_import_tasks_csv_invalid(client, content):
    r = client.post("/tasks/import", files={"file": ("tarefas.csv", content, "text/csv")})
    assert r.status_code == 400
