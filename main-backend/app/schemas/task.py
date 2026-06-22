from pydantic import BaseModel

class TaskCreate(BaseModel):
    name: str
    point: str
    robot: str
    description: str

class TaskUpdate(BaseModel):
    name: str | None = None
    point: str | None = None
    robot: str | None = None
    description: str | None = None
    status: str | None = None
