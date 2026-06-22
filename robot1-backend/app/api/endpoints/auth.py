"""认证 / 用户信息路由，取代原先的 Nitro Mock Server (apps/backend-mock)。

保持与 mock 相同的响应包装格式：`{ code: 0, data, message }`，这样 vben 前端的
`defaultResponseInterceptor` 才能正常 unwrap；token 校验失败返回 401，交给
`authenticateResponseInterceptor` 触发 refresh / reauth 流程。

账号与密码为了开发方便写死，等同于原 mock：`vben / admin / jack` 密码都是 `123456`。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time
from dataclasses import dataclass, field
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api")

# 进程启动时生成一次，整个进程生命周期内保持不变。支持通过环境变量覆盖以便重启后沿用 token。
_AUTH_SECRET: bytes = (
    os.environ.get("VISION_AUTH_SECRET") or "smart_campus_shared_secret_2026"
).encode()
_TOKEN_TTL = 24 * 3600  # 24h
_DEFAULT_AVATAR = "https://unpkg.com/@vbenjs/static-source@0.1.7/source/avatar-v1.webp"
_DEFAULT_HOME_PATH = "/dashboard"
_ROLE_ACCESS_CODES = {
    "super": ["AC_100100", "AC_100110", "AC_100120", "AC_100010"],
    "admin": ["AC_100010", "AC_100020", "AC_100030"],
    "user": ["AC_1000001", "AC_1000002"],
}


@dataclass
class _User:
    id: str
    username: str
    password: str
    real_name: str
    roles: list[str]
    home_path: str
    access_codes: list[str]
    desc: str = ""
    status: int = 1
    remark: str = ""
    create_time: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


def _access_codes_for_role(role: str) -> list[str]:
    return list(_ROLE_ACCESS_CODES.get(role, _ROLE_ACCESS_CODES["user"]))


_USERS: dict[str, _User] = {
    "vben": _User(
        id="u-vben",
        username="vben",
        password="123456",
        real_name="Vben",
        roles=["super"],
        home_path=_DEFAULT_HOME_PATH,
        access_codes=_access_codes_for_role("super"),
        desc="super user",
    ),
    "admin": _User(
        id="u-admin",
        username="admin",
        password="123456",
        real_name="Admin",
        roles=["admin"],
        home_path=_DEFAULT_HOME_PATH,
        access_codes=_access_codes_for_role("admin"),
        desc="admin user",
    ),
    "jack": _User(
        id="u-jack",
        username="jack",
        password="123456",
        real_name="Jack",
        roles=["user"],
        home_path=_DEFAULT_HOME_PATH,
        access_codes=_access_codes_for_role("user"),
        desc="normal user",
    ),
}


def _sign(username: str, ts: int) -> str:
    msg = f"{username}:{ts}".encode()
    return hmac.new(_AUTH_SECRET, msg, hashlib.sha256).hexdigest()


def _issue_token(username: str) -> str:
    ts = int(time.time())
    sig = _sign(username, ts)
    raw = f"{username}:{ts}:{sig}".encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _verify_token(token: str) -> Optional[str]:
    try:
        pad = "=" * (-len(token) % 4)
        decoded = base64.urlsafe_b64decode(token + pad).decode()
        username, ts_str, sig = decoded.split(":", 2)
        ts = int(ts_str)
    except Exception as e:
        print(f"Token decode failed: {e}")
        return None
    if username not in _USERS:
        print(f"User {username} not in _USERS")
        return None
    if _USERS[username].status != 1:
        print(f"User {username} status not 1")
        return None
    if not hmac.compare_digest(sig, _sign(username, ts)):
        print(f"Signature mismatch. sig={sig}, expected={_sign(username, ts)}")
        return None
    if time.time() - ts > _TOKEN_TTL:
        print(f"Token expired")
        return None
    return username


def _extract_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip() or None
    return authorization.strip() or None


def _require_user(authorization: str | None) -> str:
    token = _extract_token(authorization)
    username = _verify_token(token) if token else None
    if not username:
        raise HTTPException(status_code=401, detail="未授权")
    return username


def _ok(data: object = None, message: str = "ok") -> JSONResponse:
    return JSONResponse({"code": 0, "data": data, "message": message})


def _fail(message: str, code: int = -1, status: int = 400) -> JSONResponse:
    return JSONResponse(
        {"code": code, "data": None, "message": message}, status_code=status
    )


def _user_info_payload(user: _User) -> dict:
    return {
        "userId": user.id,
        "username": user.username,
        "realName": user.real_name,
        "avatar": _DEFAULT_AVATAR,
        "desc": user.desc,
        "homePath": user.home_path,
        "roles": user.roles,
    }


@router.post("/auth/login")
async def login(request: Request) -> JSONResponse:
    try:
        params = await request.json()
    except Exception:
        params = {}
    username = params.get("username", "").strip() if isinstance(params, dict) else ""
    password = params.get("password", "") if isinstance(params, dict) else ""

    user = _USERS.get(username)
    if not user or user.password != password or user.status != 1:
        return _fail("用户名或密码错误", status=200)

    token = _issue_token(user.username)
    return _ok({"accessToken": token}, "登录成功")


@router.post("/auth/refresh")
async def refresh(authorization: str | None = Header(default=None)) -> JSONResponse:
    """baseRequestClient 直调，不走默认响应拦截器，保持 mock 相同的返回结构。"""
    token = _extract_token(authorization)
    username = _verify_token(token) if token else None
    if not username:
        return JSONResponse({"data": "", "status": 401}, status_code=401)
    return JSONResponse({"data": _issue_token(username), "status": 0})


@router.post("/auth/logout")
async def logout() -> JSONResponse:
    return _ok(None, "已登出")


@router.get("/auth/codes")
async def codes(authorization: str | None = Header(default=None)) -> JSONResponse:
    username = _require_user(authorization)
    user = _USERS[username]
    return _ok(user.access_codes)


@router.get("/user/info")
async def user_info(authorization: str | None = Header(default=None)) -> JSONResponse:
    username = _require_user(authorization)
    user = _USERS[username]
    return _ok(_user_info_payload(user))
