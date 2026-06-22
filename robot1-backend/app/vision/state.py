from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from fractions import Fraction
from pathlib import Path

import numpy as np
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR.parent.parent / "recordings"
OUTPUT_DIR.mkdir(exist_ok=True)

DEPTH_SCALE_ALPHA = 0.03
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FRAME_FPS = 30
RTC_CLOCK_RATE = 90_000
RTC_TIME_BASE = Fraction(1, RTC_CLOCK_RATE)
RTC_EPOCH = time.monotonic()
WRITE_QUEUE_MAX = 120

TRACK_ORDER: tuple[str, ...] = ("rgb", "ir1", "ir2", "depth")


class RecordingStatus(Enum):
    NOT_RECORDING = auto()
    STARTED = auto()
    RECORDING = auto()
    STOPPING = auto()
    STOPPED = auto()


class StreamProfile(BaseModel):
    stream: str
    stream_index: int = 0
    format: str
    width: int
    height: int
    fps: int


@dataclass
class State:
    rgb: np.ndarray | None = None
    ir1: np.ndarray | None = None
    ir2: np.ndarray | None = None
    depth: np.ndarray | None = None

    rgb_raw: np.ndarray | None = None
    ir1_raw: np.ndarray | None = None
    ir2_raw: np.ndarray | None = None
    depth_raw: np.ndarray | None = None
    rgb_raw_pts: int | None = None

    running: bool = False
    starting: bool = False
    last_error: str | None = None

    frame_pts: dict[str, int | None] = field(
        default_factory=lambda: {name: None for name in TRACK_ORDER}
    )

    recording: RecordingStatus = RecordingStatus.NOT_RECORDING
    record_tracks: list[str] = field(default_factory=list)
    record_paths: dict[str, str] = field(default_factory=dict)

    rgb_profile: StreamProfile | None = None
    ir1_profile: StreamProfile | None = None
    ir2_profile: StreamProfile | None = None
    depth_profile: StreamProfile | None = None


state = State()

shutdown_event = threading.Event()
pipeline_stop_event = threading.Event()
start_event = threading.Event()
frame_condition = threading.Condition()

FIXED_PROFILES: dict[str, StreamProfile] = {
    "rgb": StreamProfile(
        stream="color",
        stream_index=0,
        format="rgb8",
        width=FRAME_WIDTH,
        height=FRAME_HEIGHT,
        fps=FRAME_FPS,
    ),
    "ir1": StreamProfile(
        stream="infrared",
        stream_index=1,
        format="y8",
        width=FRAME_WIDTH,
        height=FRAME_HEIGHT,
        fps=FRAME_FPS,
    ),
    "ir2": StreamProfile(
        stream="infrared",
        stream_index=2,
        format="y8",
        width=FRAME_WIDTH,
        height=FRAME_HEIGHT,
        fps=FRAME_FPS,
    ),
    "depth": StreamProfile(
        stream="depth",
        stream_index=0,
        format="z16",
        width=FRAME_WIDTH,
        height=FRAME_HEIGHT,
        fps=FRAME_FPS,
    ),
}

write_queues: dict[str, queue.Queue] = {
    name: queue.Queue(maxsize=WRITE_QUEUE_MAX) for name in TRACK_ORDER
}


def frame_shape(frame: np.ndarray | None) -> list[int] | None:
    if frame is None:
        return None
    return list(frame.shape)


def notify_frame(track_name: str) -> None:
    with frame_condition:
        frame_condition.notify_all()
