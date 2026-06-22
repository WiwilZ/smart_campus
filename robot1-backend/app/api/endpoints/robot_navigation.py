from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

from fastapi import APIRouter, Header

from app.api.endpoints.auth import _require_user
from app.api.endpoints.utils import _ok
from app.core.config import settings
from app.models.robot_navigation import (
    RobotInitialPose,
    RobotNavigationClear,
    RobotNavigationGoal,
)

router = APIRouter(prefix="/api/robot/navigation")

WORLD_SIZE = 100.0
DEFAULT_ROBOTS = [f"Robot-{index}" for index in range(1, 6)]
OBSTACLES = [
    {"x": 10.0, "y": 14.0, "width": 18.0, "height": 10.0},
    {"x": 39.0, "y": 22.0, "width": 13.0, "height": 28.0},
    {"x": 65.0, "y": 10.0, "width": 18.0, "height": 12.0},
    {"x": 72.0, "y": 46.0, "width": 10.0, "height": 22.0},
    {"x": 18.0, "y": 60.0, "width": 22.0, "height": 12.0},
    {"x": 48.0, "y": 70.0, "width": 26.0, "height": 10.0},
]


def _available_robots() -> list[str]:
    config_robots = [robot.id for robot in settings.robots if robot.id]
    return config_robots or DEFAULT_ROBOTS


def _clamp(value: float, min_value: float = 0.0, max_value: float = WORLD_SIZE) -> float:
    return min(max(value, min_value), max_value)


def _hash_robot_name(name: str) -> int:
    return sum(ord(char) for char in name)


def _costmap_zones() -> list[dict]:
    zones = []
    for obstacle in OBSTACLES:
        margin = 3.0
        zones.append(
            {
                "x": _clamp(obstacle["x"] - margin),
                "y": _clamp(obstacle["y"] - margin),
                "width": _clamp(obstacle["width"] + margin * 2, 0.0, WORLD_SIZE),
                "height": _clamp(obstacle["height"] + margin * 2, 0.0, WORLD_SIZE),
            }
        )
    return zones


def _default_pose(robot_name: str) -> dict:
    hashed = _hash_robot_name(robot_name)
    return {
        "x": 18.0 + (hashed % 24),
        "y": 18.0 + ((hashed * 3) % 24),
        "yaw": math.radians(hashed % 360),
    }


def _build_global_path(start: dict, end: dict) -> list[dict]:
    mid_x = _clamp((start["x"] + end["x"]) / 2 + (end["y"] - start["y"]) * 0.18, 8.0, 92.0)
    mid_y = _clamp((start["y"] + end["y"]) / 2 - (end["x"] - start["x"]) * 0.12, 8.0, 92.0)
    return [
        {"x": start["x"], "y": start["y"]},
        {"x": mid_x, "y": start["y"]},
        {"x": mid_x, "y": mid_y},
        {"x": end["x"], "y": end["y"]},
    ]


def _refresh_local_path(pose: dict, goal: dict | None, nav_status: str) -> list[dict]:
    if not goal or nav_status != "navigating":
        return []

    dx = goal["x"] - pose["x"]
    dy = goal["y"] - pose["y"]
    distance = math.hypot(dx, dy)
    if distance < 0.1:
        return []

    normal_x = dx / distance
    normal_y = dy / distance
    lateral = {"x": -normal_y * 1.5, "y": normal_x * 1.5}
    return [
        {"x": pose["x"], "y": pose["y"]},
        {
            "x": pose["x"] + dx * 0.35 + lateral["x"],
            "y": pose["y"] + dy * 0.35 + lateral["y"],
        },
        {
            "x": pose["x"] + dx * 0.7,
            "y": pose["y"] + dy * 0.7,
        },
        {"x": goal["x"], "y": goal["y"]},
    ]


def _refresh_scan(pose: dict, time_seconds: float) -> list[dict]:
    points = []
    for angle_index in range(72):
        angle = angle_index * 0.11 + time_seconds * 0.25
        base_radius = 8 + math.sin(angle * 2.4) * 1.2 + math.cos(angle * 0.75) * 0.8
        obstacle_influence = -1.4 if angle_index % 12 == 0 else 0.4
        radius = _clamp(base_radius + obstacle_influence, 4.8, 12.5)
        points.append(
            {
                "x": _clamp(pose["x"] + math.cos(angle) * radius),
                "y": _clamp(pose["y"] + math.sin(angle) * radius),
            }
        )
    return points


@dataclass
class RobotNavigationState:
    robot: str
    pose: dict
    goal_pose: dict | None = None
    nav_status: str = "idle"
    global_path: list[dict] = field(default_factory=list)
    local_path: list[dict] = field(default_factory=list)
    trail: list[dict] = field(default_factory=list)
    scan_points: list[dict] = field(default_factory=list)
    updated_at: float = field(default_factory=time.time)


_ROBOT_STATES: dict[str, RobotNavigationState] = {}


def _get_state(robot_name: str) -> RobotNavigationState:
    available_robots = _available_robots()
    if robot_name not in available_robots:
        robot_name = available_robots[0]

    if robot_name not in _ROBOT_STATES:
        pose = _default_pose(robot_name)
        _ROBOT_STATES[robot_name] = RobotNavigationState(
            robot=robot_name,
            pose=pose,
            trail=[{"x": pose["x"], "y": pose["y"]}],
            scan_points=_refresh_scan(pose, 0),
        )
    return _ROBOT_STATES[robot_name]


def _update_state(state: RobotNavigationState) -> RobotNavigationState:
    now = time.time()
    delta_seconds = max(0.0, now - state.updated_at)
    state.updated_at = now

    if state.goal_pose and state.nav_status == "navigating":
        dx = state.goal_pose["x"] - state.pose["x"]
        dy = state.goal_pose["y"] - state.pose["y"]
        distance = math.hypot(dx, dy)

        if distance < 0.6:
            state.pose = {
                "x": state.goal_pose["x"],
                "y": state.goal_pose["y"],
                "yaw": state.pose["yaw"],
            }
            state.nav_status = "arrived"
            state.local_path = []
        else:
            speed = 10.0
            step = min(distance, speed * delta_seconds)
            normal_x = dx / distance
            normal_y = dy / distance
            state.pose = {
                "x": state.pose["x"] + normal_x * step,
                "y": state.pose["y"] + normal_y * step,
                "yaw": math.atan2(normal_y, normal_x),
            }
            state.trail.append({"x": state.pose["x"], "y": state.pose["y"]})
            if len(state.trail) > 180:
                state.trail.pop(0)

    state.local_path = _refresh_local_path(state.pose, state.goal_pose, state.nav_status)
    state.scan_points = _refresh_scan(state.pose, now)
    return state


def _serialize_state(state: RobotNavigationState) -> dict:
    return {
        "robot": state.robot,
        "pose": state.pose,
        "goalPose": state.goal_pose,
        "navStatus": state.nav_status,
        "globalPath": state.global_path,
        "localPath": state.local_path,
        "trail": state.trail,
        "scanPoints": state.scan_points,
        "updatedAt": int(state.updated_at * 1000),
    }


@router.get("/robots")
def get_robots(authorization: str | None = Header(default=None)):
    _require_user(authorization)
    robots = _available_robots()
    return _ok(
        {
            "items": [{"label": robot, "value": robot} for robot in robots],
            "total": len(robots),
        }
    )


@router.get("/map")
def get_navigation_map(
    robot: str = "Robot-1",
    authorization: str | None = Header(default=None),
):
    _require_user(authorization)
    state = _update_state(_get_state(robot))
    return _ok(
        {
            "robot": state.robot,
            "worldSize": WORLD_SIZE,
            "obstacles": OBSTACLES,
            "costmapZones": _costmap_zones(),
            "legend": {
                "costmap": "障碍物膨胀区",
                "globalPath": "全局规划路径",
                "localPath": "局部规划路径",
                "scan": "激光扫描点",
            },
        }
    )


@router.get("/state")
def get_navigation_state(
    robot: str = "Robot-1",
    authorization: str | None = Header(default=None),
):
    _require_user(authorization)
    state = _update_state(_get_state(robot))
    return _ok(_serialize_state(state))


@router.get("/scene")
def get_navigation_scene(
    robot: str = "Robot-1",
    authorization: str | None = Header(default=None),
):
    _require_user(authorization)
    state = _update_state(_get_state(robot))
    return _ok(
        {
            "map": {
                "robot": state.robot,
                "worldSize": WORLD_SIZE,
                "obstacles": OBSTACLES,
                "costmapZones": _costmap_zones(),
            },
            "state": _serialize_state(state),
        }
    )


@router.post("/goal")
def send_navigation_goal(
    payload: RobotNavigationGoal,
    authorization: str | None = Header(default=None),
):
    _require_user(authorization)
    state = _update_state(_get_state(payload.robot))
    goal_pose = {
        "x": _clamp(payload.x),
        "y": _clamp(payload.y),
        "yaw": payload.yaw,
    }
    state.goal_pose = goal_pose
    state.nav_status = "navigating"
    state.global_path = _build_global_path(state.pose, goal_pose)
    state.local_path = _refresh_local_path(state.pose, goal_pose, state.nav_status)
    state.updated_at = time.time()
    return _ok(
        {
            "accepted": True,
            "message": "导航目标已下发",
            "state": _serialize_state(state),
        }
    )


@router.post("/initial-pose")
def set_initial_pose(
    payload: RobotInitialPose,
    authorization: str | None = Header(default=None),
):
    _require_user(authorization)
    state = _get_state(payload.robot)
    state.pose = {
        "x": _clamp(payload.x),
        "y": _clamp(payload.y),
        "yaw": payload.yaw,
    }
    state.goal_pose = None
    state.nav_status = "idle"
    state.global_path = []
    state.local_path = []
    state.trail = [{"x": state.pose["x"], "y": state.pose["y"]}]
    state.scan_points = _refresh_scan(state.pose, time.time())
    state.updated_at = time.time()
    return _ok(
        {
            "message": "初始位姿已设置",
            "state": _serialize_state(state),
        }
    )


@router.post("/clear-goal")
def clear_navigation_goal(
    payload: RobotNavigationClear,
    authorization: str | None = Header(default=None),
):
    _require_user(authorization)
    state = _get_state(payload.robot)
    state.goal_pose = None
    state.nav_status = "idle"
    state.global_path = []
    state.local_path = []
    state.updated_at = time.time()
    return _ok(
        {
            "message": "导航目标已清除",
            "state": _serialize_state(_update_state(state)),
        }
    )
