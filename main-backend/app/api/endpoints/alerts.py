from fastapi import APIRouter, Header, Request, Depends
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.alert import Alert
from app.api.endpoints.auth import _require_user
from app.api.endpoints.utils import _ok

router = APIRouter()

@router.get("/alerts")
def get_alerts(request: Request, authorization: str | None = Header(default=None), session: Session = Depends(get_session)):
    _require_user(authorization)
    alerts = session.exec(select(Alert)).all()
    return _ok({"items": [a.dict() for a in alerts], "total": len(alerts)})
