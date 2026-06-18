from sqlmodel import SQLModel, Field

class RealtimeReport(SQLModel, table=True):
    id: str | None = Field(default=None, primary_key=True)
    pointName: str | None = None
    metric: str | None = None
    value: str | None = None
    unit: str | None = None
    status: str | None = None
    time: str | None = None
