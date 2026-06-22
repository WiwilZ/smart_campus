from fastapi import APIRouter, Header, Depends
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.point import Point
from app.models.task import Task
from app.models.command import Command
from app.models.inspector import Inspector
from app.models.report import RealtimeReport
from app.api.endpoints.auth import _require_user
from app.api.endpoints.utils import _ok

router = APIRouter()

@router.get("/meta")
def get_meta(authorization: str | None = Header(default=None), session: Session = Depends(get_session)):
    _require_user(authorization)
    points = session.exec(select(Point)).all()
    inspectors = session.exec(select(Inspector)).all()
    return _ok({
        "pointOptions": [{"label": p.name, "value": p.name} for p in points],
        "statusOptions": [
            {"label": "待执行", "value": "pending"},
            {"label": "执行中", "value": "in_progress"},
            {"label": "执行成功", "value": "completed"},
            {"label": "执行失败", "value": "error"}
        ],
        "robotOptions": [
            {"label": "Robot-01", "value": "Robot-01"},
            {"label": "Robot-02", "value": "Robot-02"},
            {"label": "Robot-03", "value": "Robot-03"}
        ],
        "priorityOptions": [
            {"label": "高", "value": "high"},
            {"label": "中", "value": "medium"},
            {"label": "低", "value": "low"}
        ]
    })

@router.get("/dashboard")
def get_dashboard(authorization: str | None = Header(default=None), session: Session = Depends(get_session)):
    _require_user(authorization)
    tasks = session.exec(select(Task)).all()
    points = session.exec(select(Point)).all()
    commands = session.exec(select(Command)).all()
    
    totalPoints = len(points)
    offlinePoints = len([p for p in points if p.status == "offline"])
    warningPoints = len([p for p in points if p.status == "warning"])
    activeTasks = len([t for t in tasks if t.status == "in_progress"])
    pendingTasks = len([t for t in tasks if t.status == "pending"])
    completedTasks = len([t for t in tasks if t.status == "completed"])
    onDutyInspectors = 2 # mock
    
    return _ok({
        "summary": {
            "totalPoints": totalPoints,
            "offlinePoints": offlinePoints,
            "warningPoints": warningPoints,
            "activeTasks": activeTasks,
            "pendingTasks": pendingTasks,
            "completedTasks": completedTasks,
            "onDutyInspectors": onDutyInspectors
        },
        "statusDistribution": [
            {"label": "正常点位", "type": "success", "value": totalPoints - offlinePoints - warningPoints},
            {"label": "预警点位", "type": "warning", "value": warningPoints},
            {"label": "离线点位", "type": "error", "value": offlinePoints}
        ],
        "upcomingTasks": [{"id": t.id, "title": t.name, "priority": "medium", "status": "pending", "pointName": t.point, "inspectorName": "admin", "plannedStart": t.startTime} for t in tasks[:3]],
        "recentRecords": [],
        "alerts": []
    })

@router.get("/records")
def get_records(authorization: str | None = Header(default=None), session: Session = Depends(get_session)):
    _require_user(authorization)
    tasks = session.exec(select(Task)).all()
    return _ok([{"id": t.id, "taskName": t.name, "pointName": t.point, "status": t.status, "time": t.endTime or t.startTime} for t in tasks])

@router.get("/inspection-data")
def get_inspection_data(authorization: str | None = Header(default=None), session: Session = Depends(get_session)):
    _require_user(authorization)
    points = session.exec(select(Point)).all()
    return _ok([p.dict() for p in points])

@router.get("/realtime-data")
def get_realtime_data(authorization: str | None = Header(default=None), session: Session = Depends(get_session)):
    _require_user(authorization)
    reports = session.exec(select(RealtimeReport)).all()
    return _ok({"items": [r.dict() for r in reports], "total": len(reports)})
