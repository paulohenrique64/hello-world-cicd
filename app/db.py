import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    done        INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
)
"""


def db_path() -> str:
    return os.environ.get("DB_PATH", "data/app.db")


@contextmanager
def get_connection():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    Path(db_path()).parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.execute(SCHEMA)


# Todas as queries usam parâmetros (?) — nunca concatenar entrada do usuário no SQL.

def list_tasks() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()
    return [_to_dict(r) for r in rows]


def get_task(task_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return _to_dict(row) if row else None


def create_task(title: str, description: str) -> dict:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, description) VALUES (?, ?)", (title, description)
        )
        task_id = cur.lastrowid
    return get_task(task_id)


def update_task(task_id: int, title: str, description: str, done: bool) -> dict | None:
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE tasks SET title = ?, description = ?, done = ? WHERE id = ?",
            (title, description, int(done), task_id),
        )
        if cur.rowcount == 0:
            return None
    return get_task(task_id)


def delete_task(task_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return cur.rowcount > 0


def ping() -> bool:
    with get_connection() as conn:
        return conn.execute("SELECT 1").fetchone()[0] == 1


def _to_dict(row: sqlite3.Row) -> dict:
    task = dict(row)
    task["done"] = bool(task["done"])
    return task
