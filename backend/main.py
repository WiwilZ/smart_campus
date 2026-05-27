"""Vision 后端入口：RealSense + WebRTC mosaic 实时流 + 多路录制。

本文件作为 FastAPI 薄入口，仅负责：
- 定义 lifespan：启动时初始化 asyncio 原语与后台线程，关闭时平滑停止。
- 挂载 `api_auth`（/api/auth/*、/api/user/info）与 `api_vision`（/api/vision/*）。
- 以 uvicorn 启动监听 0.0.0.0:8080。

注意：原 `GET /` 与 `/static` 静态前端挂载已移除，前端由 @vben/web-naive 提供，
通过 Vite 代理 `/api` 打通本服务。旧版 `index.html` 和 `static/` 已归档到 `bk/legacy_frontend/`。
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api_auth import router as auth_router
from api_inspection import router as inspection_router
from api_system import router as system_router
from api_vision import router as vision_router
from vision_runtime import shutdown_worker_threads, start_worker_threads
from vision_transport import close_all_peer_connections, init_realtime_primitives


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_realtime_primitives()
    start_worker_threads()
    try:
        yield
    finally:
        shutdown_worker_threads()
        await close_all_peer_connections()


app = FastAPI(lifespan=lifespan, title="Vision Backend")
app.include_router(auth_router)
app.include_router(inspection_router)
app.include_router(system_router)
app.include_router(vision_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
