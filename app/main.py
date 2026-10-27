from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.responses import PlainTextResponse

from app import db
from app.schemas import Task, TaskCreate, TaskUpdate


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="hello-world-cicd", lifespan=lifespan)


@app.get("/hello", response_class=PlainTextResponse)
def hello() -> str:
    return "Hello World 3"


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "database": "ok" if db.ping() else "error"}


@app.get("/tasks", response_model=list[Task])
def list_tasks() -> list[dict]:
    return db.list_tasks()


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate) -> dict:
    return db.create_task(task.title, task.description)


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int) -> dict:
    return _or_404(db.get_task(task_id))


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task: TaskUpdate) -> dict:
    return _or_404(db.update_task(task_id, task.title, task.description, task.done))


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int) -> Response:
    if not db.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _or_404(task: dict | None) -> dict:
    if task is None:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return task
