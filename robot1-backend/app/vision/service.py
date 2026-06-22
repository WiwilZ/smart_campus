from __future__ import annotations

import asyncio
import time
from pathlib import Path

from fastapi.responses import JSONResponse

from app.vision.pipeline import request_pipeline_restart, wait_pipeline_stopped
from app.vision.recording import _drain_all_queues
from app.vision.state import (
    FIXED_PROFILES,
    OUTPUT_DIR,
    TRACK_ORDER,
    RecordingStatus,
    frame_shape,
    start_event,
    state,
)


def ok(data: object = None, message: str = "ok") -> JSONResponse:
    return JSONResponse({"code": 0, "data": data, "message": message})


def fail(message: str, code: int = -1, status: int = 400) -> JSONResponse:
    return JSONResponse(
        {"code": code, "data": None, "message": message}, status_code=status
    )


def profiles_payload() -> dict:
    return {
        "depth_profile": FIXED_PROFILES["depth"].model_dump(),
        "ir1_profile": FIXED_PROFILES["ir1"].model_dump(),
        "ir2_profile": FIXED_PROFILES["ir2"].model_dump(),
        "rgb_profile": FIXED_PROFILES["rgb"].model_dump(),
    }


def health_payload() -> dict:
    return {
        "running": state.running,
        "starting": state.starting,
        "recording": state.recording.name.lower(),
        "record_tracks": list(state.record_tracks),
        "record_paths": dict(state.record_paths),
        "error": state.last_error,
        **profiles_payload(),
        "frames": {name: frame_shape(getattr(state, name)) for name in TRACK_ORDER},
    }


def streams_payload() -> dict:
    return {
        "device": None,
        "depth": [FIXED_PROFILES["depth"].model_dump()],
        "ir1": [FIXED_PROFILES["ir1"].model_dump()],
        "ir2": [FIXED_PROFILES["ir2"].model_dump()],
        "rgb": [FIXED_PROFILES["rgb"].model_dump()],
    }


async def start_pipeline() -> JSONResponse:
    if state.recording in (RecordingStatus.STARTED, RecordingStatus.RECORDING):
        return fail("录制中，无法修改配置")
    if state.starting:
        return fail("正在启动中，请稍后")

    if state.running:
        request_pipeline_restart()
        if not wait_pipeline_stopped(timeout=3.0):
            return fail("当前管线停止超时，请稍后重试")

    state.rgb_profile = FIXED_PROFILES["rgb"]
    state.ir1_profile = FIXED_PROFILES["ir1"]
    state.ir2_profile = FIXED_PROFILES["ir2"]
    state.depth_profile = FIXED_PROFILES["depth"]
    state.last_error = None
    state.starting = True
    start_event.set()

    deadline = time.monotonic() + 5.0
    try:
        while time.monotonic() < deadline:
            if state.running:
                return ok({"running": True, **profiles_payload()}, "已启动")
            if state.last_error:
                return fail(state.last_error)
            await asyncio.sleep(0.05)
        return fail("启动超时")
    finally:
        state.starting = False


def start_recording(params: object) -> JSONResponse:
    if not state.running:
        return fail("尚未启动采集")
    if state.recording in (RecordingStatus.STARTED, RecordingStatus.RECORDING):
        return fail("已在录制中")

    tracks_raw = params.get("tracks") if isinstance(params, dict) else None
    if not isinstance(tracks_raw, list):
        return fail("tracks 必须为数组")

    tracks = normalize_tracks(tracks_raw)
    if not tracks:
        return fail("请至少勾选一个录制轨道")

    missing = [track for track in tracks if getattr(state, track, None) is None]
    if missing:
        return fail(f"以下轨道尚未就绪: {missing}")

    ts = time.strftime("%Y%m%d_%H%M%S")
    paths = {name: str(OUTPUT_DIR / f"{ts}_{name}.mp4") for name in tracks}

    _drain_all_queues()
    state.record_tracks = list(tracks)
    state.record_paths = dict(paths)
    state.recording = RecordingStatus.STARTED
    return ok({"paths": paths, "tracks": list(tracks)}, "开始录制")


def stop_recording() -> JSONResponse:
    if state.recording not in (RecordingStatus.STARTED, RecordingStatus.RECORDING):
        return fail("当前未在录制")
    state.recording = RecordingStatus.STOPPING
    return ok({"paths": dict(state.record_paths)}, "结束录制")


def commit_recording() -> JSONResponse:
    if state.recording in (
        RecordingStatus.STARTED,
        RecordingStatus.RECORDING,
        RecordingStatus.STOPPING,
    ):
        return fail("录像仍在进行中")
    if not state.record_paths:
        return fail("没有可保存的录像")
    saved = dict(state.record_paths)
    state.record_paths = {}
    state.record_tracks = []
    state.recording = RecordingStatus.NOT_RECORDING
    return ok({"paths": saved}, "已保存")


def discard_recording(params: object) -> JSONResponse:
    paths_raw = extract_discard_paths(params)
    if not paths_raw:
        return fail("缺少 path / paths")

    if state.recording in (
        RecordingStatus.STARTED,
        RecordingStatus.RECORDING,
        RecordingStatus.STOPPING,
    ):
        active = set(state.record_paths.values())
        if any(path in active for path in paths_raw):
            return fail("录像进行中，无法丢弃")

    removed: list[str] = []
    errors: list[str] = []
    base = OUTPUT_DIR.resolve()
    for raw in paths_raw:
        try:
            target = Path(raw).resolve()
            if base not in target.parents:
                errors.append(f"{raw}: 路径不在录像目录下")
                continue
            if target.exists():
                target.unlink()
            removed.append(str(target))
            for name, saved_path in list(state.record_paths.items()):
                if saved_path == str(target):
                    state.record_paths.pop(name, None)
        except Exception as exc:
            errors.append(f"{raw}: {exc}")

    if not state.record_paths:
        state.record_tracks = []
        state.recording = RecordingStatus.NOT_RECORDING

    if errors and not removed:
        return fail("; ".join(errors))
    return ok({"paths": removed, "errors": errors}, "已丢弃")


def normalize_tracks(tracks_raw: list) -> list[str]:
    seen: set[str] = set()
    tracks: list[str] = []
    for track in tracks_raw:
        if isinstance(track, str) and track in TRACK_ORDER and track not in seen:
            seen.add(track)
            tracks.append(track)
    return tracks


def extract_discard_paths(params: object) -> list[str]:
    if not isinstance(params, dict):
        return []
    if isinstance(params.get("paths"), list):
        return [str(path) for path in params["paths"] if path]
    if params.get("path"):
        return [str(params["path"])]
    return []
