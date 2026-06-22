from fastapi import APIRouter, Header, Request, Depends
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.command import Command
from app.api.endpoints.auth import _require_user
from app.api.endpoints.utils import _ok

router = APIRouter()

@router.get("/commands")
def get_commands(request: Request, authorization: str | None = Header(default=None), session: Session = Depends(get_session)):
    _require_user(authorization)
    commands = session.exec(select(Command)).all()
    return _ok({"items": [c.dict() for c in commands], "total": len(commands)})
