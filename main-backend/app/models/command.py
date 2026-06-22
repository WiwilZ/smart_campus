from sqlmodel import SQLModel, Field

class Command(SQLModel, table=True):
    id: str | None = Field(default=None, primary_key=True)
    command: str
    target: str | None = None
    operator: str | None = None
    status: str | None = None
    createdAt: str | None = None
    result: str | None = None
