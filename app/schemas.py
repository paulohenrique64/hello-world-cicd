from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)


class TaskUpdate(TaskCreate):
    done: bool = False


class Task(TaskUpdate):
    id: int
    created_at: str
