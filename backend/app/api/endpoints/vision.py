from __future__ import annotations

from fastapi import APIRouter, Request, WebSocket
from fastapi.responses import JSONResponse

from app.vision import service
from app.vision.transport import vision_ws

router = APIRouter(prefix="/api/vision")


async def request_json_or_empty(request: Request) -> object:
    try:
        return await request.json()
    except Exception:
        return {}


@router.get("/health")
def health() -> JSONResponse:
    return service.ok(service.health_payload())


@router.get("/streams")
def list_streams() -> JSONResponse:
    return service.ok(service.streams_payload())


@router.post("/start")
async def pipeline_start() -> JSONResponse:
    return await service.start_pipeline()


@router.post("/record/start")
async def record_start(request: Request) -> JSONResponse:
    return service.start_recording(await request_json_or_empty(request))


@router.post("/record/stop")
def record_stop() -> JSONResponse:
    return service.stop_recording()


@router.post("/record/commit")
def record_commit() -> JSONResponse:
    return service.commit_recording()


@router.post("/record/discard")
async def record_discard(request: Request) -> JSONResponse:
    return service.discard_recording(await request_json_or_empty(request))


@router.websocket("/ws")
async def websocket_signaling(websocket: WebSocket) -> None:
    await vision_ws(websocket)
