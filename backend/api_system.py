from __future__ import annotations

import secrets
import time

from api_auth import (
    _DEFAULT_HOME_PATH,
    _USERS,
    _access_codes_for_role,
    _require_user,
    _User,
)
from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/system")
_ALLOWED_ROLES = {"super", "admin", "user"}


def _ok(data: object = None, message: str = "ok") -> JSONResponse:
    return JSONResponse({"code": 0, "data": data, "message": message})


def _fail(message: str, code: int = -1, status: int = 400) -> JSONResponse:
    return JSONResponse(
        {"code": code, "data": None, "message": message}, status_code=status
    )


def _user_row(user: _User) -> dict:
    role = user.roles[0] if user.roles else "user"
    return {
        "id": user.id,
        "username": user.username,
        "realName": user.real_name,
        "role": role,
        "status": user.status,
        "remark": user.remark,
        "createTime": user.create_time,
    }


def _find_user_by_id(user_id: str) -> tuple[str, _User] | None:
    for username, user in _USERS.items():
        if user.id == user_id:
            return username, user
    return None


def _normalize_role(value: object, *, required: bool) -> str | None:
    if value in (None, ""):
        if required:
            raise ValueError("角色不能为空")
        return None
    role = str(value).strip()
    if role not in _ALLOWED_ROLES:
        raise ValueError("角色不合法")
    return role


def _normalize_status(value: object, *, required: bool) -> int | None:
    if value in (None, ""):
        if required:
            raise ValueError("状态不能为空")
        return None
    try:
        status = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("状态不合法") from exc
    if status not in (0, 1):
        raise ValueError("状态不合法")
    return status


def _build_desc(role: str, remark: str) -> str:
    return remark or f"{role} user"


def _parse_user_payload(
    payload: object,
    *,
    partial: bool,
    current: _User | None = None,
) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("参数格式错误")

    data: dict[str, object] = {}

    if partial:
        if "username" in payload:
            username = str(payload.get("username", "")).strip()
            if not username:
                raise ValueError("用户名不能为空")
            data["username"] = username
        if "realName" in payload:
            real_name = str(payload.get("realName", "")).strip()
            if not real_name:
                raise ValueError("姓名不能为空")
            data["real_name"] = real_name
        if "role" in payload:
            data["role"] = _normalize_role(payload.get("role"), required=True)
        if "status" in payload:
            data["status"] = _normalize_status(payload.get("status"), required=True)
        if "remark" in payload:
            data["remark"] = str(payload.get("remark") or "").strip()
        if "password" in payload:
            password = str(payload.get("password") or "").strip()
            if not password:
                raise ValueError("密码不能为空")
            data["password"] = password
        return data

    username = str(payload.get("username", "")).strip()
    real_name = str(payload.get("realName", "")).strip()
    password = str(payload.get("password") or "123456").strip()
    remark = str(payload.get("remark") or "").strip()
    role = _normalize_role(payload.get("role"), required=True)
    status = _normalize_status(payload.get("status", 1), required=True)

    if not username:
        raise ValueError("用户名不能为空")
    if not real_name:
        raise ValueError("姓名不能为空")
    if not password:
        raise ValueError("密码不能为空")

    data["username"] = username
    data["real_name"] = real_name
    data["password"] = password
    data["role"] = role
    data["status"] = status
    data["remark"] = remark

    if current is not None:
        data.setdefault("username", current.username)
        data.setdefault("real_name", current.real_name)
        data.setdefault("password", current.password)
        data.setdefault("role", current.roles[0] if current.roles else "user")
        data.setdefault("status", current.status)
        data.setdefault("remark", current.remark)

    return data


@router.get("/user/list")
async def get_user_list(
    request: Request,
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    _require_user(authorization)
    params = request.query_params
    page = max(int(params.get("page", 1) or 1), 1)
    page_size = max(int(params.get("pageSize", 20) or 20), 1)
    real_name = str(params.get("realName", "") or "").strip().lower()
    role = str(params.get("role", "") or "").strip()
    username = str(params.get("username", "") or "").strip().lower()
    status_raw = params.get("status")
    status = None if status_raw in (None, "") else int(status_raw)

    items = [_user_row(user) for user in _USERS.values()]
    if username:
        items = [item for item in items if username in item["username"].lower()]
    if real_name:
        items = [item for item in items if real_name in item["realName"].lower()]
    if role:
        items = [item for item in items if item["role"] == role]
    if status in (0, 1):
        items = [item for item in items if item["status"] == status]

    items.sort(key=lambda item: item["createTime"], reverse=True)
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return _ok({"items": items[start:end], "total": total})


@router.post("/user")
async def create_user(
    request: Request,
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    _require_user(authorization)
    try:
        payload = await request.json()
        data = _parse_user_payload(payload, partial=False)
    except ValueError as exc:
        return _fail(str(exc))
    except Exception:
        return _fail("参数格式错误")

    username = str(data["username"])
    if username in _USERS:
        return _fail("用户名已存在")

    role = str(data["role"])
    remark = str(data.get("remark") or "")
    user = _User(
        id=f"u-{secrets.token_hex(4)}",
        username=username,
        password=str(data["password"]),
        real_name=str(data["real_name"]),
        roles=[role],
        home_path=_DEFAULT_HOME_PATH,
        access_codes=_access_codes_for_role(role),
        desc=_build_desc(role, remark),
        status=int(data["status"]),
        remark=remark,
        create_time=time.strftime("%Y-%m-%d %H:%M:%S"),
    )
    _USERS[username] = user
    return _ok(_user_row(user), "创建成功")


@router.put("/user/{user_id}")
async def update_user(
    user_id: str,
    request: Request,
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    _require_user(authorization)
    found = _find_user_by_id(user_id)
    if not found:
        return _fail("用户不存在", status=404)

    old_username, user = found
    try:
        payload = await request.json()
        data = _parse_user_payload(payload, partial=True, current=user)
    except ValueError as exc:
        return _fail(str(exc))
    except Exception:
        return _fail("参数格式错误")

    new_username = str(data.get("username", user.username))
    if new_username != old_username and new_username in _USERS:
        return _fail("用户名已存在")

    role = str(data.get("role", user.roles[0] if user.roles else "user"))
    remark = str(data.get("remark", user.remark))

    user.username = new_username
    user.real_name = str(data.get("real_name", user.real_name))
    user.password = str(data.get("password", user.password))
    user.roles = [role]
    user.home_path = _DEFAULT_HOME_PATH
    user.access_codes = _access_codes_for_role(role)
    user.desc = _build_desc(role, remark)
    user.status = int(data.get("status", user.status))
    user.remark = remark

    if new_username != old_username:
        _USERS.pop(old_username, None)
        _USERS[new_username] = user

    return _ok(_user_row(user), "更新成功")


@router.delete("/user/{user_id}")
async def delete_user(
    user_id: str,
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    _require_user(authorization)
    found = _find_user_by_id(user_id)
    if not found:
        return _fail("用户不存在", status=404)
    username, user = found
    _USERS.pop(username, None)
    return _ok(_user_row(user), "删除成功")
