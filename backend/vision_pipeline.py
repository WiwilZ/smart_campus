from __future__ import annotations

import time

import cv2
import numpy as np
import pyrealsense2 as rs

from vision_recording import _enqueue_if_recording
from vision_state import (
    DEPTH_SCALE_ALPHA,
    FIXED_PROFILES,
    RTC_CLOCK_RATE,
    RTC_EPOCH,
    StreamProfile,
    frame_condition,
    pipeline_stop_event,
    shutdown_event,
    start_event,
    state,
)

_RS_FORMAT_LOOKUP = {
    str(fmt).replace("format.", ""): fmt for fmt in rs.format.__members__.values()
}
_RS_STREAM_LOOKUP = {
    str(stream).replace("stream.", ""): stream
    for stream in rs.stream.__members__.values()
}


def _rs_stream(name: str) -> rs.stream:
    try:
        return _RS_STREAM_LOOKUP[name]
    except KeyError as exc:
        raise ValueError(f"不支持的流类型: {name}") from exc


def _rs_format(name: str) -> rs.format:
    try:
        return _RS_FORMAT_LOOKUP[name]
    except KeyError as exc:
        raise ValueError(f"不支持的格式: {name}") from exc


def _ir_to_rgb(ir_frame: np.ndarray) -> np.ndarray:
    if ir_frame.ndim == 3 and ir_frame.shape[2] == 3:
        ir_frame = cv2.cvtColor(ir_frame, cv2.COLOR_RGB2GRAY)
    if ir_frame.dtype == np.uint16:
        gray = cv2.convertScaleAbs(ir_frame, alpha=255.0 / 65535.0)
    else:
        gray = ir_frame
    lo = int(gray.min())
    hi = int(gray.max())
    if hi > lo:
        gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    bgr = cv2.applyColorMap(gray, cv2.COLORMAP_PLASMA)
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def _colorize_depth(depth_u16: np.ndarray) -> np.ndarray:
    bgr = cv2.applyColorMap(
        cv2.convertScaleAbs(depth_u16, alpha=DEPTH_SCALE_ALPHA),
        cv2.COLORMAP_JET,
    )
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def _build_rs_config() -> rs.config:
    config = rs.config()
    for profile in FIXED_PROFILES.values():
        config.enable_stream(
            _rs_stream(profile.stream),
            profile.stream_index,
            profile.width,
            profile.height,
            _rs_format(profile.format),
            profile.fps,
        )
    return config


def _rgb_frame_to_numpy(color_frame) -> np.ndarray:
    arr = np.asanyarray(color_frame.get_data())
    fmt = color_frame.get_profile().format()
    if fmt == rs.format.rgb8:
        return arr.copy()
    if fmt == rs.format.bgr8:
        return cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
    if fmt == rs.format.rgba8:
        return cv2.cvtColor(arr, cv2.COLOR_RGBA2RGB)
    if fmt == rs.format.bgra8:
        return cv2.cvtColor(arr, cv2.COLOR_BGRA2RGB)
    if fmt == rs.format.yuyv:
        width = color_frame.get_width()
        height = color_frame.get_height()
        yuyv = arr.reshape(height, width, 2)
        return cv2.cvtColor(yuyv, cv2.COLOR_YUV2RGB_YUYV)
    if fmt == rs.format.y8:
        return cv2.cvtColor(arr, cv2.COLOR_GRAY2RGB)
    return arr.copy()


def _monotonic_pts() -> int:
    return max(0, int((time.monotonic() - RTC_EPOCH) * RTC_CLOCK_RATE))


def _install_fixed_profiles() -> None:
    state.rgb_profile = FIXED_PROFILES["rgb"]
    state.ir1_profile = FIXED_PROFILES["ir1"]
    state.ir2_profile = FIXED_PROFILES["ir2"]
    state.depth_profile = FIXED_PROFILES["depth"]


def _run_pipeline_once() -> None:
    _install_fixed_profiles()
    rgb_profile: StreamProfile = FIXED_PROFILES["rgb"]
    ir1_profile: StreamProfile = FIXED_PROFILES["ir1"]
    ir2_profile: StreamProfile = FIXED_PROFILES["ir2"]
    depth_profile: StreamProfile = FIXED_PROFILES["depth"]

    pipeline = rs.pipeline()
    config = _build_rs_config()
    pipeline.start(config)
    try:
        state.running = True
        state.starting = False
        state.last_error = None
        pipeline_stop_event.clear()

        while not shutdown_event.is_set() and not pipeline_stop_event.is_set():
            try:
                frames = pipeline.wait_for_frames()
            except RuntimeError as exc:
                state.last_error = str(exc)
                time.sleep(0.05)
                continue
            frame_pts = _monotonic_pts()

            color_frame = frames.first_or_default(_rs_stream(rgb_profile.stream))
            depth_frame = frames.first_or_default(_rs_stream(depth_profile.stream))

            # --- Process frames (CPU-intensive, no lock) ---
            rgb: np.ndarray | None = None
            if color_frame:
                rgb = _rgb_frame_to_numpy(color_frame)

            ir_data: dict[str, tuple[np.ndarray, np.ndarray]] = {}
            for ir_profile, track_name in (
                (ir1_profile, "ir1"),
                (ir2_profile, "ir2"),
            ):
                ir_frame = frames.get_infrared_frame(ir_profile.stream_index)
                if not ir_frame:
                    continue
                ir_np = np.asanyarray(ir_frame.get_data()).copy()
                colored = _ir_to_rgb(ir_np)
                ir_data[track_name] = (ir_np, colored)

            depth_raw: np.ndarray | None = None
            depth_colored: np.ndarray | None = None
            depth_error: Exception | None = None
            if depth_frame:
                try:
                    depth_raw = np.asanyarray(depth_frame.get_data()).copy()
                    depth_colored = _colorize_depth(depth_raw)
                except Exception as exc:
                    depth_error = exc

            # --- Atomic state update (under lock) ---
            with frame_condition:
                if rgb is not None:
                    state.rgb = rgb
                    state.rgb_raw = rgb
                    state.rgb_raw_pts = frame_pts
                    state.frame_pts["rgb"] = frame_pts
                for track_name, (ir_np, colored) in ir_data.items():
                    if track_name == "ir1":
                        state.ir1_raw = ir_np
                        state.ir1 = colored
                    else:
                        state.ir2_raw = ir_np
                        state.ir2 = colored
                    state.frame_pts[track_name] = frame_pts
                if depth_colored is not None:
                    state.depth_raw = depth_raw
                    state.depth = depth_colored
                    state.frame_pts["depth"] = frame_pts
                if depth_error is not None:
                    state.last_error = f"深度着色失败: {depth_error}"
                frame_condition.notify_all()

            # --- Enqueue for recording (outside lock) ---
            if rgb is not None:
                _enqueue_if_recording("rgb", rgb)
            for track_name, (_, colored) in ir_data.items():
                _enqueue_if_recording(track_name, colored)
            if depth_colored is not None:
                _enqueue_if_recording("depth", depth_colored)

            if depth_error is not None:
                time.sleep(0.05)
                continue
    finally:
        try:
            pipeline.stop()
        except Exception:
            pass
        state.running = False


def capture_loop() -> None:
    while not shutdown_event.is_set():
        if not start_event.wait(timeout=0.1):
            continue
        start_event.clear()
        if shutdown_event.is_set():
            return
        state.starting = True
        try:
            _run_pipeline_once()
        except Exception as exc:
            state.last_error = str(exc)
        finally:
            state.starting = False
            state.running = False


def wait_pipeline_stopped(timeout: float = 3.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not state.running:
            return True
        time.sleep(0.02)
    return not state.running


def request_pipeline_restart() -> None:
    pipeline_stop_event.set()
