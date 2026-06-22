from pydantic import BaseModel

class PointCreate(BaseModel):
    name: str
    coordinates: str
    description: str

class PointUpdate(BaseModel):
    name: str | None = None
    coordinates: str | None = None
    description: str | None = None
