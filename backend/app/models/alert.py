from sqlmodel import SQLModel, Field

class Alert(SQLModel, table=True):
    id: str | None = Field(default=None, primary_key=True)
    time: str | None = None
    location: str | None = None
    image: str | None = None
    description: str | None = None
