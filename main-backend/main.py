from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.points import router as points_router
from app.api.endpoints.tasks import router as tasks_router
from app.api.endpoints.alerts import router as alerts_router
from app.api.endpoints.dashboard import router as dashboard_router
from app.api.endpoints.system import router as system_router


app = FastAPI(title="Smart Campus Basic Backend")

# 挂载静态文件
app.mount("/images", StaticFiles(directory="static/images"), name="images")

# 基础业务路由
app.include_router(auth_router)
app.include_router(points_router, prefix="/api/inspection")
app.include_router(tasks_router, prefix="/api/inspection")
app.include_router(alerts_router, prefix="/api/inspection")
app.include_router(dashboard_router, prefix="/api/inspection")
app.include_router(system_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=10000, reload=True)
