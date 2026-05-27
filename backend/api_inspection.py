from __future__ import annotations

import json
import threading
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path

from api_auth import _require_user
from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/inspection")
_DATA_PATH = Path(__file__).resolve().parent / "inspection_data.json"
_STORE_LOCK = threading.Lock()
_POINT_STATUSES = {"normal", "offline", "warning"}
_TASK_STATUSES = {"completed", "in_progress", "paused", "pending", "scheduled"}
_TASK_PRIORITIES = {"high", "low", "medium"}
_SHIFT_OPTIONS = [
    {"label": "早班", "value": "morning"},
    {"label": "中班", "value": "afternoon"},
    {"label": "夜班", "value": "night"},
]


def _dt(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M")


def _fmt(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M")


def _seed_store() -> dict:
    now = datetime.now().replace(second=0, microsecond=0)
    inspectors = [
        {
            "id": "insp-001",
            "name": "张敏",
            "phone": "18800010001",
            "shift": "早班",
            "status": "on_duty",
            "title": "值班主管",
        },
        {
            "id": "insp-002",
            "name": "李波",
            "phone": "18800010002",
            "shift": "中班",
            "status": "on_duty",
            "title": "巡检工程师",
        },
        {
            "id": "insp-003",
            "name": "王雪",
            "phone": "18800010003",
            "shift": "夜班",
            "status": "resting",
            "title": "巡检工程师",
        },
        {
            "id": "insp-004",
            "name": "陈晨",
            "phone": "18800010004",
            "shift": "机动",
            "status": "support",
            "title": "设备专员",
        },
    ]
    points = [
        {
            "id": "pt-001",
            "code": "A-01",
            "name": "学府广场",
            "area": "校园公共空间",
            "deviceName": "学府广场巡检机器人",
            "deviceType": "广场安防巡检点",
            "status": "normal",
            "riskLevel": "medium",
            "inspectorName": "张敏",
            "lastInspectionTime": _fmt(now - timedelta(minutes=16)),
            "description": "重点关注人流密度、广场照明、公共广播与异常聚集。",
        },
        {
            "id": "pt-002",
            "code": "A-02",
            "name": "体育运动中心",
            "area": "体育运动中心",
            "deviceName": "体育运动中心巡检机器人",
            "deviceType": "场馆安防巡检点",
            "status": "warning",
            "riskLevel": "high",
            "inspectorName": "李波",
            "lastInspectionTime": _fmt(now - timedelta(hours=1, minutes=8)),
            "description": "晚间训练时段人流较高，需复核入口通道、消防门与视频链路。",
        },
        {
            "id": "pt-003",
            "code": "A-03",
            "name": "文理图书馆",
            "area": "文理图书馆",
            "deviceName": "文理图书馆巡检机器人",
            "deviceType": "室内巡检点",
            "status": "normal",
            "riskLevel": "high",
            "inspectorName": "王雪",
            "lastInspectionTime": _fmt(now - timedelta(minutes=34)),
            "description": "关注阅览区温湿度、门禁闸机、人流密度与消防通道。",
        },
        {
            "id": "pt-004",
            "code": "A-04",
            "name": "听荷池",
            "area": "景观水域",
            "deviceName": "听荷池水域巡检终端",
            "deviceType": "水域环境巡检点",
            "status": "warning",
            "riskLevel": "medium",
            "inspectorName": "陈晨",
            "lastInspectionTime": _fmt(now - timedelta(hours=2, minutes=10)),
            "description": "水位与护栏状态需要持续关注，夜间补光设备需复核。",
        },
        {
            "id": "pt-005",
            "code": "A-05",
            "name": "东三食堂",
            "area": "后勤餐饮",
            "deviceName": "东三食堂后勤巡检机器人",
            "deviceType": "餐饮后勤巡检点",
            "status": "normal",
            "riskLevel": "medium",
            "inspectorName": "张敏",
            "lastInspectionTime": _fmt(now - timedelta(minutes=48)),
            "description": "检查燃气报警、后厨温度、排烟系统与后勤通道占用。",
        },
        {
            "id": "pt-006",
            "code": "A-06",
            "name": "北园学生宿舍",
            "area": "学生宿舍",
            "deviceName": "北园学生宿舍消防巡检机器人",
            "deviceType": "宿舍区巡检点",
            "status": "normal",
            "riskLevel": "low",
            "inspectorName": "李波",
            "lastInspectionTime": _fmt(now - timedelta(hours=1, minutes=36)),
            "description": "重点关注消防通道、电瓶车停放、楼栋照明与夜间噪声。",
        },
        {
            "id": "pt-007",
            "code": "A-07",
            "name": "东区停车场",
            "area": "交通停车",
            "deviceName": "东区停车场巡检机器人",
            "deviceType": "停车场巡检点",
            "status": "offline",
            "riskLevel": "high",
            "inspectorName": "陈晨",
            "lastInspectionTime": _fmt(now - timedelta(hours=4, minutes=20)),
            "description": "停车场视频终端离线，需检查充电桩、车道占用与视频网关。",
        },
    ]
    tasks = [
        {
            "id": "task-001",
            "title": "学府广场人流与照明巡检",
            "pointId": "pt-001",
            "pointName": "学府广场",
            "inspectorId": "insp-001",
            "inspectorName": "张敏",
            "frequency": "每日 08:00 / 20:00",
            "priority": "medium",
            "status": "in_progress",
            "plannedStart": _fmt(now - timedelta(minutes=10)),
            "plannedEnd": _fmt(now + timedelta(minutes=20)),
            "lastExecutionTime": _fmt(now - timedelta(days=1, minutes=5)),
            "description": "核对广场人流密度、公共广播、照明与异常聚集情况。",
            "checklist": [
                "检查广场人流密度",
                "确认公共照明状态",
                "核对广播与安防摄像头在线情况",
            ],
        },
        {
            "id": "task-002",
            "title": "体育运动中心入口通道复核",
            "pointId": "pt-002",
            "pointName": "体育运动中心",
            "inspectorId": "insp-002",
            "inspectorName": "李波",
            "frequency": "每日 3 次",
            "priority": "high",
            "status": "scheduled",
            "plannedStart": _fmt(now + timedelta(hours=1)),
            "plannedEnd": _fmt(now + timedelta(hours=1, minutes=40)),
            "lastExecutionTime": _fmt(now - timedelta(hours=4, minutes=2)),
            "description": "复核场馆入口拥堵、消防门开启、视频链路与应急照明。",
            "checklist": [
                "检查入口人流拥堵",
                "确认消防门与疏散标识",
                "复核视频链路在线状态",
            ],
        },
        {
            "id": "task-003",
            "title": "文理图书馆阅览区环境巡检",
            "pointId": "pt-003",
            "pointName": "文理图书馆",
            "inspectorId": "insp-003",
            "inspectorName": "王雪",
            "frequency": "每日 4 次",
            "priority": "high",
            "status": "pending",
            "plannedStart": _fmt(now + timedelta(hours=2, minutes=30)),
            "plannedEnd": _fmt(now + timedelta(hours=3, minutes=5)),
            "lastExecutionTime": _fmt(now - timedelta(hours=3, minutes=25)),
            "description": "检查阅览区温湿度、人流密度、门禁闸机与消防通道。",
            "checklist": [
                "读取温湿度数值",
                "检查阅览区人流密度",
                "确认消防通道无遮挡",
            ],
        },
        {
            "id": "task-004",
            "title": "听荷池水域安全巡检",
            "pointId": "pt-004",
            "pointName": "听荷池",
            "inspectorId": "insp-004",
            "inspectorName": "陈晨",
            "frequency": "每日 2 次",
            "priority": "medium",
            "status": "scheduled",
            "plannedStart": _fmt(now + timedelta(hours=3)),
            "plannedEnd": _fmt(now + timedelta(hours=3, minutes=35)),
            "lastExecutionTime": _fmt(now - timedelta(hours=6, minutes=10)),
            "description": "巡检水位、护栏完整性、警示牌与夜间补光状态。",
            "checklist": [
                "读取水位标尺",
                "检查护栏与警示牌",
                "确认夜间补光设备",
            ],
        },
        {
            "id": "task-005",
            "title": "东三食堂后勤安全巡检",
            "pointId": "pt-005",
            "pointName": "东三食堂",
            "inspectorId": "insp-001",
            "inspectorName": "张敏",
            "frequency": "每日 10:00 / 15:00",
            "priority": "medium",
            "status": "completed",
            "plannedStart": _fmt(now - timedelta(hours=3)),
            "plannedEnd": _fmt(now - timedelta(hours=2, minutes=25)),
            "lastExecutionTime": _fmt(now - timedelta(hours=2, minutes=25)),
            "description": "确认燃气报警器、排烟系统、后厨温度与通道占用。",
            "checklist": [
                "检查燃气报警器",
                "读取后厨温度",
                "确认排烟系统和后勤通道",
            ],
        },
        {
            "id": "task-006",
            "title": "北园学生宿舍消防通道复核",
            "pointId": "pt-006",
            "pointName": "北园学生宿舍",
            "inspectorId": "insp-002",
            "inspectorName": "李波",
            "frequency": "每日 2 次",
            "priority": "low",
            "status": "completed",
            "plannedStart": _fmt(now - timedelta(hours=2)),
            "plannedEnd": _fmt(now - timedelta(hours=1, minutes=25)),
            "lastExecutionTime": _fmt(now - timedelta(hours=1, minutes=25)),
            "description": "检查宿舍消防通道、电瓶车停放、楼栋照明与夜间噪声。",
            "checklist": [
                "检查消防通道占用",
                "检查电瓶车停放",
                "复核楼栋照明与噪声",
            ],
        },
        {
            "id": "task-007",
            "title": "东区停车场视频链路恢复",
            "pointId": "pt-007",
            "pointName": "东区停车场",
            "inspectorId": "insp-004",
            "inspectorName": "陈晨",
            "frequency": "故障触发",
            "priority": "high",
            "status": "paused",
            "plannedStart": _fmt(now + timedelta(hours=4)),
            "plannedEnd": _fmt(now + timedelta(hours=4, minutes=45)),
            "lastExecutionTime": _fmt(now - timedelta(days=1, hours=1, minutes=20)),
            "description": "排查停车场视频终端离线、车道占用、充电桩与网络网关状态。",
            "checklist": [
                "检查视频终端网络",
                "检查车道与充电桩状态",
                "远程重启停车场网关",
            ],
        },
    ]
    schedules = [
        {
            "id": "sch-001",
            "taskId": "task-002",
            "taskTitle": "体育运动中心入口通道复核",
            "inspectorId": "insp-002",
            "inspectorName": "李波",
            "executionTime": _fmt(now + timedelta(hours=1)),
            "shift": "afternoon",
            "note": "结合晚间训练高峰复核入口拥堵与消防门状态",
            "reminderMinutes": 20,
            "createdAt": _fmt(now - timedelta(minutes=30)),
        },
        {
            "id": "sch-002",
            "taskId": "task-004",
            "taskTitle": "听荷池水域安全巡检",
            "inspectorId": "insp-004",
            "inspectorName": "陈晨",
            "executionTime": _fmt(now + timedelta(hours=3)),
            "shift": "evening",
            "note": "夜间补光开启前复核水位、护栏和警示牌",
            "reminderMinutes": 15,
            "createdAt": _fmt(now - timedelta(minutes=18)),
        },
        {
            "id": "sch-003",
            "taskId": "task-007",
            "taskTitle": "东区停车场视频链路恢复",
            "inspectorId": "insp-004",
            "inspectorName": "陈晨",
            "executionTime": _fmt(now + timedelta(hours=4)),
            "shift": "evening",
            "note": "优先检查停车场网关、视频终端和充电桩状态",
            "reminderMinutes": 10,
            "createdAt": _fmt(now - timedelta(minutes=12)),
        },
    ]
    records = [
        {
            "id": "rec-001",
            "taskId": "task-005",
            "taskTitle": "东三食堂后勤安全巡检",
            "pointName": "东三食堂",
            "inspectorName": "张敏",
            "result": "normal",
            "finishedAt": _fmt(now - timedelta(hours=2, minutes=25)),
            "summary": "燃气报警器、排烟系统和后勤通道均正常，未发现占道。",
        },
        {
            "id": "rec-002",
            "taskId": "task-001",
            "taskTitle": "学府广场人流与照明巡检",
            "pointName": "学府广场",
            "inspectorName": "张敏",
            "result": "normal",
            "finishedAt": _fmt(now - timedelta(days=1, minutes=5)),
            "summary": "广场人流平稳，照明、广播和安防摄像头状态正常。",
        },
        {
            "id": "rec-003",
            "taskId": "task-002",
            "taskTitle": "体育运动中心入口通道复核",
            "pointName": "体育运动中心",
            "inspectorName": "李波",
            "result": "warning",
            "finishedAt": _fmt(now - timedelta(hours=4, minutes=2)),
            "summary": "主入口训练时段短时拥堵，应急照明正常，建议晚间复核。",
        },
        {
            "id": "rec-004",
            "taskId": "task-003",
            "taskTitle": "文理图书馆阅览区环境巡检",
            "pointName": "文理图书馆",
            "inspectorName": "王雪",
            "result": "normal",
            "finishedAt": _fmt(now - timedelta(hours=3, minutes=25)),
            "summary": "阅览区温湿度、人流密度、门禁闸机与消防通道均正常。",
        },
        {
            "id": "rec-005",
            "taskId": "task-006",
            "taskTitle": "北园学生宿舍消防通道复核",
            "pointName": "北园学生宿舍",
            "inspectorName": "李波",
            "result": "normal",
            "finishedAt": _fmt(now - timedelta(hours=1, minutes=25)),
            "summary": "消防通道无遮挡，电瓶车停放规范，楼栋照明正常。",
        },
    ]
    alerts = [
        {
            "id": "alert-001",
            "level": "medium",
            "title": "体育运动中心入口人流预警",
            "content": "晚间训练时段入口人流密度接近阈值，建议加强疏导。",
            "createdAt": _fmt(now - timedelta(minutes=9)),
        },
        {
            "id": "alert-002",
            "level": "medium",
            "title": "听荷池夜间补光待复核",
            "content": "听荷池北侧补光设备响应延迟，需要夜间巡检时复核。",
            "createdAt": _fmt(now - timedelta(hours=1, minutes=10)),
        },
        {
            "id": "alert-003",
            "level": "high",
            "title": "东区停车场视频终端离线",
            "content": "东区停车场视频终端离线超过 4 小时，请检查网关与供电。",
            "createdAt": _fmt(now - timedelta(hours=1, minutes=35)),
        },
    ]
    inspection_rows = [
        {
            "id": "data-001",
            "algorithm": "人流密度 - 聚集检测算法",
            "taskNo": "自动巡检 - 22",
            "pointName": "学府广场",
            "value": "126 人/小时",
            "time": _fmt(now - timedelta(minutes=2)),
            "detail": "广场人流处于正常范围，未发现异常聚集。",
        },
        {
            "id": "data-002",
            "algorithm": "通道占用 - 入口拥堵识别",
            "taskNo": "自动巡检 - 22",
            "pointName": "体育运动中心",
            "value": "拥堵指数 72%",
            "time": _fmt(now - timedelta(minutes=5)),
            "detail": "训练时段主入口人流较高，建议加强现场疏导。",
        },
        {
            "id": "data-003",
            "algorithm": "温湿度 - 阅览区环境检测",
            "taskNo": "自动巡检 - 21",
            "pointName": "文理图书馆",
            "value": "24.6 ℃ / 51%",
            "time": _fmt(now - timedelta(minutes=12)),
            "detail": "阅览区温湿度舒适，消防通道无遮挡。",
        },
        {
            "id": "data-004",
            "algorithm": "水域安全 - 水位护栏检测",
            "taskNo": "自动巡检 - 20",
            "pointName": "听荷池",
            "value": "水位 0.82 m",
            "time": _fmt(now - timedelta(minutes=18)),
            "detail": "水位正常，北侧补光设备需夜间复核。",
        },
        {
            "id": "data-005",
            "algorithm": "燃气 - 后厨安全检测",
            "taskNo": "自动巡检 - 19",
            "pointName": "东三食堂",
            "value": "0 ppm",
            "time": _fmt(now - timedelta(minutes=25)),
            "detail": "燃气报警器与排烟系统状态正常。",
        },
        {
            "id": "data-006",
            "algorithm": "消防通道 - 占道检测",
            "taskNo": "手动巡检 - 18",
            "pointName": "北园学生宿舍",
            "value": "无遮挡",
            "time": _fmt(now - timedelta(minutes=36)),
            "detail": "宿舍消防通道无遮挡，楼栋照明正常。",
        },
        {
            "id": "data-007",
            "algorithm": "视频链路 - 终端在线检测",
            "taskNo": "故障巡检 - 17",
            "pointName": "东区停车场",
            "value": "离线",
            "time": _fmt(now - timedelta(hours=1)),
            "detail": "停车场视频终端离线，需检查网络网关与供电。",
        },
    ]
    realtime_rows = [
        {
            "id": "rt-001",
            "pointName": "学府广场",
            "metric": "人流密度",
            "value": "126 人/小时",
            "status": "normal",
            "time": _fmt(now - timedelta(minutes=1)),
        },
        {
            "id": "rt-002",
            "pointName": "体育运动中心",
            "metric": "拥堵指数",
            "value": "72%",
            "status": "warning",
            "time": _fmt(now - timedelta(minutes=1)),
        },
        {
            "id": "rt-003",
            "pointName": "文理图书馆",
            "metric": "阅览区温湿度",
            "value": "24.6 ℃ / 51%",
            "status": "normal",
            "time": _fmt(now - timedelta(minutes=2)),
        },
        {
            "id": "rt-004",
            "pointName": "听荷池",
            "metric": "水位",
            "value": "0.82 m",
            "status": "warning",
            "time": _fmt(now - timedelta(minutes=3)),
        },
        {
            "id": "rt-005",
            "pointName": "东三食堂",
            "metric": "燃气浓度",
            "value": "0 ppm",
            "status": "normal",
            "time": _fmt(now - timedelta(minutes=4)),
        },
        {
            "id": "rt-006",
            "pointName": "北园学生宿舍",
            "metric": "消防通道",
            "value": "无遮挡",
            "status": "normal",
            "time": _fmt(now - timedelta(minutes=5)),
        },
        {
            "id": "rt-007",
            "pointName": "东区停车场",
            "metric": "视频终端",
            "value": "离线",
            "status": "offline",
            "time": _fmt(now - timedelta(minutes=6)),
        },
    ]
    batches = [
        {
            "id": "batch-022",
            "batchNo": "22",
            "type": "自动巡检",
            "route": "学府广场 - 体育运动中心 - 文理图书馆",
            "pointCount": 3,
            "startedAt": _fmt(now - timedelta(minutes=55)),
            "finishedAt": _fmt(now - timedelta(minutes=8)),
            "status": "completed",
        },
        {
            "id": "batch-021",
            "batchNo": "21",
            "type": "自动巡检",
            "route": "听荷池 - 东三食堂",
            "pointCount": 2,
            "startedAt": _fmt(now - timedelta(hours=2)),
            "finishedAt": "",
            "status": "running",
        },
        {
            "id": "batch-020",
            "batchNo": "20",
            "type": "手动巡检",
            "route": "北园学生宿舍消防路线",
            "pointCount": 1,
            "startedAt": _fmt(now - timedelta(hours=3)),
            "finishedAt": _fmt(now - timedelta(hours=2, minutes=18)),
            "status": "completed",
        },
        {
            "id": "batch-019",
            "batchNo": "19",
            "type": "故障巡检",
            "route": "东区停车场视频链路恢复路线",
            "pointCount": 1,
            "startedAt": _fmt(now - timedelta(hours=5)),
            "finishedAt": "",
            "status": "unfinished",
        },
    ]
    commands = [
        {
            "id": "cmd-001",
            "command": "开始录像",
            "target": "学府广场巡检机器人",
            "operator": "user1",
            "status": "success",
            "createdAt": _fmt(now - timedelta(minutes=6)),
            "result": "录像任务已启动。",
        },
        {
            "id": "cmd-002",
            "command": "云台左转",
            "target": "体育运动中心巡检机器人",
            "operator": "user1",
            "status": "success",
            "createdAt": _fmt(now - timedelta(minutes=11)),
            "result": "云台已左转 15°。",
        },
        {
            "id": "cmd-003",
            "command": "机械臂初始化",
            "target": "东三食堂后勤巡检机器人",
            "operator": "root",
            "status": "success",
            "createdAt": _fmt(now - timedelta(minutes=18)),
            "result": "机械臂已归零。",
        },
        {
            "id": "cmd-004",
            "command": "拍摄照片",
            "target": "东区停车场巡检机器人",
            "operator": "user1",
            "status": "failed",
            "createdAt": _fmt(now - timedelta(hours=1)),
            "result": "设备离线，命令未执行。",
        },
    ]
    return {
        "alerts": alerts,
        "batches": batches,
        "commands": commands,
        "inspectionRows": inspection_rows,
        "inspectors": inspectors,
        "points": points,
        "realtimeRows": realtime_rows,
        "records": records,
        "schedules": schedules,
        "tasks": tasks,
    }


def _ok(data: object = None, message: str = "ok") -> JSONResponse:
    return JSONResponse({"code": 0, "data": data, "message": message})


def _fail(message: str, code: int = -1, status: int = 400) -> JSONResponse:
    return JSONResponse(
        {"code": code, "data": None, "message": message}, status_code=status
    )


def _ensure_store() -> None:
    if _DATA_PATH.exists():
        return
    _DATA_PATH.write_text(
        json.dumps(_seed_store(), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _load_store() -> dict:
    _ensure_store()
    with _STORE_LOCK:
        store = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    seed = _seed_store()
    for key in [
        "alerts",
        "batches",
        "commands",
        "inspectionRows",
        "inspectors",
        "points",
        "realtimeRows",
        "records",
        "schedules",
        "tasks",
    ]:
        store.setdefault(key, seed[key])
    return store


def _save_store(store: dict) -> None:
    with _STORE_LOCK:
        _DATA_PATH.write_text(
            json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def _find_by_id(items: list[dict], item_id: str) -> dict | None:
    return next((item for item in items if item.get("id") == item_id), None)


def _point_options(store: dict) -> list[dict[str, str]]:
    return [
        {"label": point["name"], "value": point["id"]}
        for point in sorted(store["points"], key=lambda item: item["code"])
    ]


def _inspector_options(store: dict) -> list[dict[str, str]]:
    return [
        {"label": inspector["name"], "value": inspector["id"]}
        for inspector in store["inspectors"]
    ]


def _task_options(values: list[str]) -> list[dict[str, str]]:
    return [{"label": value, "value": value} for value in values]


def _store_options(store: dict, key: str, field: str) -> list[dict[str, str]]:
    return _task_options(
        sorted({item[field] for item in store[key] if item.get(field)})
    )


def _contains(value: object, keyword: str) -> bool:
    return keyword in str(value or "").lower()


def _dashboard_payload(store: dict) -> dict:
    points = store["points"]
    tasks = store["tasks"]
    records = sorted(
        store["records"], key=lambda item: item["finishedAt"], reverse=True
    )
    alerts = sorted(store["alerts"], key=lambda item: item["createdAt"], reverse=True)
    normal_points = sum(1 for point in points if point["status"] == "normal")
    warning_points = sum(1 for point in points if point["status"] == "warning")
    offline_points = sum(1 for point in points if point["status"] == "offline")
    pending_tasks = sum(
        1 for task in tasks if task["status"] in {"pending", "scheduled"}
    )
    active_tasks = sum(1 for task in tasks if task["status"] == "in_progress")
    completed_tasks = sum(1 for task in tasks if task["status"] == "completed")
    upcoming_tasks = [
        task
        for task in sorted(tasks, key=lambda item: item["plannedStart"])
        if task["status"] in {"pending", "scheduled", "in_progress"}
    ][:6]
    return {
        "alerts": alerts[:5],
        "recentRecords": records[:6],
        "statusDistribution": [
            {"label": "正常点位", "type": "success", "value": normal_points},
            {"label": "预警点位", "type": "warning", "value": warning_points},
            {"label": "离线点位", "type": "error", "value": offline_points},
        ],
        "summary": {
            "activeTasks": active_tasks,
            "completedTasks": completed_tasks,
            "offlinePoints": offline_points,
            "onDutyInspectors": sum(
                1
                for inspector in store["inspectors"]
                if inspector["status"] == "on_duty"
            ),
            "pendingTasks": pending_tasks,
            "totalPoints": len(points),
            "warningPoints": warning_points,
        },
        "upcomingTasks": upcoming_tasks,
    }


def _task_payload(store: dict, task: dict) -> dict:
    task_copy = deepcopy(task)
    point = _find_by_id(store["points"], task_copy["pointId"])
    if point is not None:
        task_copy["point"] = point
    return task_copy


def _normalize_task_payload(store: dict, payload: object) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("参数格式错误")

    point_id = str(payload.get("pointId") or "").strip()
    title = str(payload.get("title") or "").strip()
    inspector_id = str(payload.get("inspectorId") or "").strip()
    frequency = str(payload.get("frequency") or "").strip()
    priority = str(payload.get("priority") or "").strip()
    status = str(payload.get("status") or "").strip()
    planned_start = str(payload.get("plannedStart") or "").strip()
    planned_end = str(payload.get("plannedEnd") or "").strip()
    description = str(payload.get("description") or "").strip()
    checklist_raw = payload.get("checklist") or []

    if not title:
        raise ValueError("任务标题不能为空")
    point = _find_by_id(store["points"], point_id)
    if point is None:
        raise ValueError("巡检点位不存在")
    inspector = _find_by_id(store["inspectors"], inspector_id)
    if inspector is None:
        raise ValueError("巡检人员不存在")
    if not frequency:
        raise ValueError("巡检频次不能为空")
    if priority not in _TASK_PRIORITIES:
        raise ValueError("任务优先级不合法")
    if status not in _TASK_STATUSES:
        raise ValueError("任务状态不合法")
    if not planned_start or not planned_end:
        raise ValueError("计划时间不能为空")
    if _dt(planned_end) <= _dt(planned_start):
        raise ValueError("结束时间必须晚于开始时间")
    if not isinstance(checklist_raw, list) or not checklist_raw:
        raise ValueError("巡检项不能为空")

    checklist = [str(item).strip() for item in checklist_raw if str(item).strip()]
    if not checklist:
        raise ValueError("巡检项不能为空")

    return {
        "checklist": checklist,
        "description": description,
        "frequency": frequency,
        "inspectorId": inspector["id"],
        "inspectorName": inspector["name"],
        "plannedEnd": planned_end,
        "plannedStart": planned_start,
        "pointId": point["id"],
        "pointName": point["name"],
        "priority": priority,
        "status": status,
        "title": title,
    }


def _normalize_schedule_payload(store: dict, payload: object) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("参数格式错误")
    inspector_id = str(payload.get("inspectorId") or "").strip()
    execution_time = str(payload.get("executionTime") or "").strip()
    shift = str(payload.get("shift") or "").strip()
    note = str(payload.get("note") or "").strip()
    reminder_minutes = int(payload.get("reminderMinutes") or 15)
    inspector = _find_by_id(store["inspectors"], inspector_id)
    if inspector is None:
        raise ValueError("巡检人员不存在")
    if not execution_time:
        raise ValueError("执行时间不能为空")
    try:
        parsed_execution = datetime.fromisoformat(execution_time)
    except ValueError as exc:
        raise ValueError("执行时间格式不正确") from exc
    if shift not in {option["value"] for option in _SHIFT_OPTIONS}:
        raise ValueError("班次不合法")
    if reminder_minutes <= 0:
        raise ValueError("提醒时间必须大于 0")
    return {
        "executionTime": _fmt(parsed_execution),
        "inspectorId": inspector["id"],
        "inspectorName": inspector["name"],
        "note": note,
        "plannedEnd": _fmt(parsed_execution + timedelta(minutes=45)),
        "plannedStart": _fmt(parsed_execution),
        "reminderMinutes": reminder_minutes,
        "shift": shift,
    }


@router.get("/meta")
def inspection_meta(authorization: str | None = Header(default=None)) -> JSONResponse:
    _require_user(authorization)
    store = _load_store()
    return _ok(
        {
            "inspectors": store["inspectors"],
            "pointOptions": _point_options(store),
            "priorityOptions": _task_options(["high", "medium", "low"]),
            "shiftOptions": _SHIFT_OPTIONS,
            "statusOptions": _task_options(
                ["pending", "scheduled", "in_progress", "completed", "paused"]
            ),
        }
    )


@router.get("/dashboard")
def inspection_dashboard(
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    _require_user(authorization)
    return _ok(_dashboard_payload(_load_store()))


@router.get("/points")
def inspection_points(
    request: Request,
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    _require_user(authorization)
    store = _load_store()
    params = request.query_params
    keyword = str(params.get("keyword") or "").strip().lower()
    area = str(params.get("area") or "").strip()
    status = str(params.get("status") or "").strip()

    items = deepcopy(store["points"])
    if keyword:
        items = [
            item
            for item in items
            if keyword in item["name"].lower()
            or keyword in item["code"].lower()
            or keyword in item["deviceName"].lower()
        ]
    if area:
        items = [item for item in items if item["area"] == area]
    if status:
        if status not in _POINT_STATUSES:
            return _fail("点位状态不合法")
        items = [item for item in items if item["status"] == status]

    items.sort(key=lambda item: (item["status"], item["code"]))
    stats = {
        "normal": sum(1 for item in items if item["status"] == "normal"),
        "offline": sum(1 for item in items if item["status"] == "offline"),
        "warning": sum(1 for item in items if item["status"] == "warning"),
    }
    return _ok(
        {
            "areaOptions": _task_options(
                sorted({item["area"] for item in store["points"]})
            ),
            "items": items,
            "stats": stats,
            "statusOptions": _task_options(["normal", "warning", "offline"]),
            "total": len(items),
        }
    )


@router.get("/tasks")
def inspection_tasks(
    request: Request,
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    _require_user(authorization)
    store = _load_store()
    params = request.query_params
    keyword = str(params.get("keyword") or "").strip().lower()
    priority = str(params.get("priority") or "").strip()
    status = str(params.get("status") or "").strip()
    inspector_id = str(params.get("inspectorId") or "").strip()

    items = [_task_payload(store, task) for task in store["tasks"]]
    if keyword:
        items = [
            item
            for item in items
            if keyword in item["title"].lower()
            or keyword in item["pointName"].lower()
            or keyword in item["id"].lower()
        ]
    if priority:
        if priority not in _TASK_PRIORITIES:
            return _fail("任务优先级不合法")
        items = [item for item in items if item["priority"] == priority]
    if status:
        if status not in _TASK_STATUSES:
            return _fail("任务状态不合法")
        items = [item for item in items if item["status"] == status]
    if inspector_id:
        items = [item for item in items if item["inspectorId"] == inspector_id]

    items.sort(key=lambda item: item["plannedStart"])
    summary = {
        "completed": sum(1 for item in items if item["status"] == "completed"),
        "inProgress": sum(1 for item in items if item["status"] == "in_progress"),
        "pending": sum(
            1 for item in items if item["status"] in {"pending", "scheduled"}
        ),
        "paused": sum(1 for item in items if item["status"] == "paused"),
    }
    return _ok(
        {
            "inspectorOptions": _inspector_options(store),
            "items": items,
            "priorityOptions": _task_options(["high", "medium", "low"]),
            "statusOptions": _task_options(
                ["pending", "scheduled", "in_progress", "completed", "paused"]
            ),
            "summary": summary,
            "total": len(items),
        }
    )


@router.get("/records")
def inspection_records(
    request: Request,
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    _require_user(authorization)
    store = _load_store()
    params = request.query_params
    keyword = str(params.get("keyword") or "").strip().lower()
    result = str(params.get("result") or "").strip()

    items = deepcopy(store["records"])
    if keyword:
        items = [
            item
            for item in items
            if _contains(item.get("taskTitle"), keyword)
            or _contains(item.get("pointName"), keyword)
            or _contains(item.get("inspectorName"), keyword)
            or _contains(item.get("summary"), keyword)
        ]
    if result:
        items = [item for item in items if item.get("result") == result]

    items.sort(key=lambda item: item["finishedAt"], reverse=True)
    return _ok(
        {
            "items": items,
            "resultOptions": _task_options(["normal", "warning", "abnormal"]),
            "total": len(items),
        }
    )


@router.get("/inspection-data")
def inspection_data(
    request: Request,
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    _require_user(authorization)
    store = _load_store()
    params = request.query_params
    keyword = str(params.get("keyword") or "").strip().lower()
    point_name = str(params.get("pointName") or "").strip()
    algorithm = str(params.get("algorithm") or "").strip()

    items = deepcopy(store["inspectionRows"])
    if keyword:
        items = [
            item
            for item in items
            if _contains(item.get("algorithm"), keyword)
            or _contains(item.get("taskNo"), keyword)
            or _contains(item.get("pointName"), keyword)
            or _contains(item.get("value"), keyword)
        ]
    if point_name:
        items = [item for item in items if item.get("pointName") == point_name]
    if algorithm:
        items = [item for item in items if item.get("algorithm") == algorithm]

    items.sort(key=lambda item: item["time"], reverse=True)
    return _ok(
        {
            "algorithmOptions": _store_options(store, "inspectionRows", "algorithm"),
            "items": items,
            "pointOptions": _store_options(store, "inspectionRows", "pointName"),
            "total": len(items),
        }
    )


@router.get("/realtime-data")
def realtime_data(
    request: Request,
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    _require_user(authorization)
    store = _load_store()
    params = request.query_params
    keyword = str(params.get("keyword") or "").strip().lower()
    status = str(params.get("status") or "").strip()

    items = deepcopy(store["realtimeRows"])
    if keyword:
        items = [
            item
            for item in items
            if _contains(item.get("pointName"), keyword)
            or _contains(item.get("metric"), keyword)
            or _contains(item.get("value"), keyword)
        ]
    if status:
        items = [item for item in items if item.get("status") == status]

    items.sort(key=lambda item: item["time"], reverse=True)
    return _ok(
        {
            "items": items,
            "statusOptions": _task_options(["normal", "warning", "offline"]),
            "total": len(items),
        }
    )


@router.get("/alerts")
def inspection_alerts(
    request: Request,
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    _require_user(authorization)
    store = _load_store()
    params = request.query_params
    keyword = str(params.get("keyword") or "").strip().lower()
    level = str(params.get("level") or "").strip()

    items = deepcopy(store["alerts"])
    if keyword:
        items = [
            item
            for item in items
            if _contains(item.get("title"), keyword)
            or _contains(item.get("content"), keyword)
        ]
    if level:
        items = [item for item in items if item.get("level") == level]

    items.sort(key=lambda item: item["createdAt"], reverse=True)
    return _ok(
        {
            "items": items,
            "levelOptions": _task_options(["high", "medium", "low"]),
            "total": len(items),
        }
    )


@router.get("/batches")
def inspection_batches(
    request: Request,
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    _require_user(authorization)
    store = _load_store()
    params = request.query_params
    keyword = str(params.get("keyword") or "").strip().lower()
    status = str(params.get("status") or "").strip()

    items = deepcopy(store["batches"])
    if keyword:
        items = [
            item
            for item in items
            if _contains(item.get("batchNo"), keyword)
            or _contains(item.get("type"), keyword)
            or _contains(item.get("route"), keyword)
        ]
    if status:
        items = [item for item in items if item.get("status") == status]

    items.sort(key=lambda item: item["startedAt"], reverse=True)
    return _ok(
        {
            "items": items,
            "statusOptions": _task_options(["completed", "running", "unfinished"]),
            "total": len(items),
        }
    )


@router.get("/commands")
def inspection_commands(
    request: Request,
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    _require_user(authorization)
    store = _load_store()
    params = request.query_params
    keyword = str(params.get("keyword") or "").strip().lower()
    status = str(params.get("status") or "").strip()

    items = deepcopy(store["commands"])
    if keyword:
        items = [
            item
            for item in items
            if _contains(item.get("command"), keyword)
            or _contains(item.get("target"), keyword)
            or _contains(item.get("operator"), keyword)
        ]
    if status:
        items = [item for item in items if item.get("status") == status]

    items.sort(key=lambda item: item["createdAt"], reverse=True)
    return _ok(
        {
            "items": items,
            "statusOptions": _task_options(["success", "running", "failed"]),
            "total": len(items),
        }
    )


@router.get("/tasks/{task_id}")
def inspection_task_detail(
    task_id: str,
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    _require_user(authorization)
    store = _load_store()
    task = _find_by_id(store["tasks"], task_id)
    if task is None:
        return _fail("任务不存在", status=404)
    return _ok(_task_payload(store, task))


@router.put("/tasks/{task_id}")
async def update_inspection_task(
    task_id: str,
    request: Request,
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    _require_user(authorization)
    store = _load_store()
    task = _find_by_id(store["tasks"], task_id)
    if task is None:
        return _fail("任务不存在", status=404)
    try:
        payload = await request.json()
        normalized = _normalize_task_payload(store, payload)
    except ValueError as exc:
        return _fail(str(exc))
    except Exception:
        return _fail("参数格式错误")

    task.update(normalized)
    _save_store(store)
    return _ok(_task_payload(store, task), "保存成功")


@router.post("/tasks/{task_id}/schedule")
async def schedule_inspection_task(
    task_id: str,
    request: Request,
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    _require_user(authorization)
    store = _load_store()
    task = _find_by_id(store["tasks"], task_id)
    if task is None:
        return _fail("任务不存在", status=404)
    try:
        payload = await request.json()
        normalized = _normalize_schedule_payload(store, payload)
    except ValueError as exc:
        return _fail(str(exc))
    except Exception:
        return _fail("参数格式错误")

    task.update(
        {
            "inspectorId": normalized["inspectorId"],
            "inspectorName": normalized["inspectorName"],
            "plannedEnd": normalized["plannedEnd"],
            "plannedStart": normalized["plannedStart"],
            "status": "scheduled",
        }
    )
    schedule = {
        "createdAt": _fmt(datetime.now().replace(second=0, microsecond=0)),
        "executionTime": normalized["executionTime"],
        "id": f"sch-{int(datetime.now().timestamp())}",
        "inspectorId": normalized["inspectorId"],
        "inspectorName": normalized["inspectorName"],
        "note": normalized["note"],
        "reminderMinutes": normalized["reminderMinutes"],
        "shift": normalized["shift"],
        "taskId": task["id"],
        "taskTitle": task["title"],
    }
    store["schedules"].insert(0, schedule)
    _save_store(store)
    return _ok({"schedule": schedule, "task": _task_payload(store, task)}, "排班成功")
