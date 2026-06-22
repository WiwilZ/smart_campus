from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.endpoints.commands import router as commands_router
from app.api.endpoints.vision import router as vision_router
from app.api.endpoints.robot_navigation import router as robot_navigation_router
from app.vision.runtime import shutdown_worker_threads, start_worker_threads
from app.vision.transport import close_all_peer_connections, init_realtime_primitives
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading robot config...")
    for robot in settings.robots:
        print(f"Loaded Robot: {robot.id} -> IP: {robot.ip}")
        
    init_realtime_primitives()
    start_worker_threads()
    try:
        yield
    finally:
        shutdown_worker_threads()
        await close_all_peer_connections()


app = FastAPI(lifespan=lifespan, title="Vision & Robotics Backend")

# 机器人管理与实时监控路由
app.include_router(commands_router, prefix="/api/inspection")
app.include_router(vision_router)
app.include_router(robot_navigation_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=10001, reload=True)
