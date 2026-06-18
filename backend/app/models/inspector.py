from sqlmodel import SQLModel, Field

class Inspector(SQLModel, table=True):
    id: str | None = Field(default=None, primary_key=True)
    name: str
    phone: str
    shift: str
    status: str
    title: str
