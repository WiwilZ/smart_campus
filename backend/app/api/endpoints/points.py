from fastapi import APIRouter, Header, Request, Depends, HTTPException
from sqlmodel import Session, select
import uuid
from datetime import datetime
from app.core.database import get_session
from app.models.point import Point
from app.schemas.point import PointCreate, PointUpdate
from app.api.endpoints.auth import _require_user
from app.api.endpoints.utils import _ok

router = APIRouter()

@router.get("/points")
def get_points(request: Request, authorization: str | None = Header(default=None), session: Session = Depends(get_session)):
    _require_user(authorization)
    params = request.query_params
    name = str(params.get("name") or "").strip().lower()
    description = str(params.get("description") or "").strip().lower()
    
    stmt = select(Point)
    if name: stmt = stmt.where(Point.name.like(f"%{name}%"))
    if description: stmt = stmt.where(Point.description.like(f"%{description}%"))
    
    points = session.exec(stmt).all()
    return _ok({"items": [p.dict() for p in points], "total": len(points)})

@router.post("/points")
def create_point(point: PointCreate, request: Request, authorization: str | None = Header(default=None), session: Session = Depends(get_session)):
    user = _require_user(authorization)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pt = Point(id=str(uuid.uuid4()), name=point.name, coordinates=point.coordinates, description=point.description,
               creatorName=user["realName"], createTime=now, modifierName=user["realName"], modifyTime=now)
    session.add(pt)
    session.commit()
    return _ok({"id": pt.id})

@router.put("/points/{pt_id}")
def update_point(pt_id: str, point: PointUpdate, request: Request, authorization: str | None = Header(default=None), session: Session = Depends(get_session)):
    user = _require_user(authorization)
    pt = session.get(Point, pt_id)
    if not pt: raise HTTPException(status_code=404, detail="Not found")
    if point.name is not None: pt.name = point.name
    if point.coordinates is not None: pt.coordinates = point.coordinates
    if point.description is not None: pt.description = point.description
    pt.modifierName = user["realName"]
    pt.modifyTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session.commit()
    return _ok({"id": pt.id})

@router.delete("/points/{pt_id}")
def delete_point(pt_id: str, authorization: str | None = Header(default=None), session: Session = Depends(get_session)):
    _require_user(authorization)
    pt = session.get(Point, pt_id)
    if pt:
        session.delete(pt)
        session.commit()
    return _ok({"id": pt_id})
