from __future__ import annotations

import queue
import time
from dataclasses import dataclass

import ffmpeg
import numpy as np

from app.vision.state import (
    RecordingStatus,
    TRACK_ORDER,
    shutdown_event,
    state,
    write_queues,
)


@dataclass
class Recorder:
    process: object | None = None

    def start(self, path: str, width: int, height: int, fps: int) -> bool:
        self.stop()
        video_stream = ffmpeg.input(
            "pipe:",
            format="rawvideo",
            pix_fmt="rgb24",
            s=f"{width}x{height}",
            framerate=fps,
        )
        output = video_stream.output(path, vcodec="h264_nvmpi")
        process = output.run_async(
            pipe_stdin=True,
            cmd="/usr/local/bin/ffmpeg",
            quiet=True,
        )
        if process.poll() is not None:
            return False
        self.process = process
        return True

    def stop(self) -> None:
        if self.process is not None:
            try:
                self.process.stdin.close()
                self.process.wait()
            except Exception:
                pass
        self.process = None

    def write(self, frame: np.ndarray) -> None:
        if self.process is None:
            return
        try:
            self.process.stdin.write(frame.tobytes())
        except (BrokenPipeError, ValueError):
            self.process = None


def _drain_queue(q: queue.Queue) -> None:
    try:
        while True:
            q.get_nowait()
    except queue.Empty:
        pass


def _drain_all_queues() -> None:
    for q in write_queues.values():
        _drain_queue(q)


def _track_profile(name: str):
    return {
        "rgb": state.rgb_profile,
        "depth": state.depth_profile,
        "ir1": state.ir1_profile,
        "ir2": state.ir2_profile,
    }.get(name)


def _enqueue_if_recording(track_name: str, frame: np.ndarray) -> None:
    if state.recording not in (
        RecordingStatus.STARTED,
        RecordingStatus.RECORDING,
    ):
        return
    if track_name not in state.record_tracks:
        return
    q = write_queues.get(track_name)
    if q is None:
        return
    try:
        q.put_nowait(frame)
    except queue.Full:
        pass


def writer_loop() -> None:
    recorders: dict[str, Recorder] = {name: Recorder() for name in TRACK_ORDER}
    try:
        while not shutdown_event.is_set():
            rec = state.recording

            if rec == RecordingStatus.STARTED:
                active = list(state.record_tracks)
                paths = dict(state.record_paths)
                ok = True
                err_detail: str | None = None
                for name in active:
                    profile = _track_profile(name)
                    path = paths.get(name)
                    if not profile or not path:
                        err_detail = f"录像参数无效: {name}"
                        ok = False
                        break
                    if not recorders[name].start(
                        path, profile.width, profile.height, profile.fps
                    ):
                        err_detail = f"ffmpeg 子进程启动失败: {name}"
                        ok = False
                        break
                if ok:
                    state.recording = RecordingStatus.RECORDING
                else:
                    for recorder in recorders.values():
                        recorder.stop()
                    state.record_tracks = []
                    state.record_paths = {}
                    state.last_error = err_detail
                    state.recording = RecordingStatus.NOT_RECORDING
                    _drain_all_queues()
                continue

            if rec == RecordingStatus.STOPPING:
                for name in list(state.record_tracks):
                    q = write_queues[name]
                    while True:
                        try:
                            frame = q.get_nowait()
                        except queue.Empty:
                            break
                        if frame is not None:
                            recorders[name].write(frame)
                    recorders[name].stop()
                state.recording = RecordingStatus.STOPPED
                continue

            if rec == RecordingStatus.STOPPED:
                time.sleep(0.05)
                continue

            if rec == RecordingStatus.RECORDING:
                active = list(state.record_tracks)
                if not active:
                    time.sleep(0.05)
                    continue
                wrote_any = False
                got_sentinel = False
                for name in active:
                    q = write_queues[name]
                    try:
                        while True:
                            frame = q.get_nowait()
                            if frame is None:
                                got_sentinel = True
                                break
                            recorders[name].write(frame)
                            wrote_any = True
                    except queue.Empty:
                        pass
                    if got_sentinel:
                        break
                if got_sentinel:
                    return
                if not wrote_any:
                    time.sleep(0.01)
                continue

            _drain_all_queues()
            time.sleep(0.05)
    finally:
        for recorder in recorders.values():
            recorder.stop()
