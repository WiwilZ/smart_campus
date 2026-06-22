from sqlmodel import SQLModel, Field

class PointTaskLink(SQLModel, table=True):
    point_id: str | None = Field(default=None, foreign_key="point.id", primary_key=True)
    task_id: str | None = Field(default=None, foreign_key="task.id", primary_key=True)
