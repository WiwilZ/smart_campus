from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING
from .links import PointTaskLink

if TYPE_CHECKING:
    from .task import Task

class Point(SQLModel, table=True):
    id: str | None = Field(default=None, primary_key=True)
    code: str | None = None
    name: str
    area: str | None = None
    deviceName: str | None = None
    deviceType: str | None = None
    status: str | None = None
    riskLevel: str | None = None
    inspectorName: str | None = None
    lastInspectionTime: str | None = None
    coordinates: str | None = None
    description: str | None = None
    creatorName: str | None = None
    createTime: str | None = None
    modifierName: str | None = None
    modifyTime: str | None = None
    
    tasks: list["Task"] = Relationship(back_populates="points", link_model=PointTaskLink)
