from fastapi import APIRouter, Header, Request, Depends, HTTPException
from sqlmodel import Session, select
import uuid
from datetime import datetime
from app.core.database import get_session
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate
from app.api.endpoints.auth import _require_user
from app.api.endpoints.utils import _ok

router = APIRouter()

@router.get("/tasks")
def get_tasks(request: Request, authorization: str | None = Header(default=None), session: Session = Depends(get_session)):
    _require_user(authorization)
    params = request.query_params
    name = str(params.get("name") or "").strip().lower()
    stmt = select(Task)
    if name: stmt = stmt.where(Task.name.like(f"%{name}%"))
    tasks = session.exec(stmt).all()
    return _ok({"items": [t.dict() for t in tasks], "total": len(tasks)})

@router.post("/tasks")
def create_task(task: TaskCreate, request: Request, authorization: str | None = Header(default=None), session: Session = Depends(get_session)):
    user = _require_user(authorization)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    t = Task(id=str(uuid.uuid4()), name=task.name, point=task.point, robot=task.robot, status="待执行",
             description=task.description, creatorName=user["realName"], createTime=now, modifierName=user["realName"], modifyTime=now)
    session.add(t)
    session.commit()
    return _ok({"id": t.id})

@router.put("/tasks/{t_id}")
def update_task(t_id: str, task: TaskUpdate, request: Request, authorization: str | None = Header(default=None), session: Session = Depends(get_session)):
    user = _require_user(authorization)
    t = session.get(Task, t_id)
    if not t: raise HTTPException(status_code=404, detail="Not found")
    if task.name is not None: t.name = task.name
    if task.point is not None: t.point = task.point
    if task.robot is not None: t.robot = task.robot
    if task.description is not None: t.description = task.description
    if task.status is not None: t.status = task.status
    t.modifierName = user["realName"]
    t.modifyTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session.commit()
    return _ok({"id": t.id})

@router.delete("/tasks/{t_id}")
def delete_task(t_id: str, authorization: str | None = Header(default=None), session: Session = Depends(get_session)):
    _require_user(authorization)
    t = session.get(Task, t_id)
    if t:
        session.delete(t)
        session.commit()
    return _ok({"id": t_id})
