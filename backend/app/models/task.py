from sqlmodel import SQLModel, Field, Relationship
from .point import Point

from .links import PointTaskLink

class Task(SQLModel, table=True):
    id: str | None = Field(default=None, primary_key=True)
    name: str
    point: str | None = None
    robot: str | None = None
    status: str | None = None
    startTime: str | None = None
    endTime: str | None = None
    description: str | None = None
    creatorName: str | None = None
    createTime: str | None = None
    modifierName: str | None = None
    modifyTime: str | None = None
    
    points: list[Point] = Relationship(back_populates="tasks", link_model=PointTaskLink)
