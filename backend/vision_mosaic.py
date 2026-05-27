from __future__ import annotations

import asyncio
from fractions import Fraction

import av
import cv2
import numpy as np
from aiortc import VideoStreamTrack

from vision_state import RTC_CLOCK_RATE, frame_condition, state

MOSAIC_WIDTH = 1920
MOSAIC_HEIGHT = 1080
TILE_WIDTH = MOSAIC_WIDTH // 2
TILE_HEIGHT = MOSAIC_HEIGHT // 2
MOSAIC_LAYOUT: tuple[tuple[str, int, int], ...] = (
    ("rgb_raw", 0, 0),
    ("depth", 0, TILE_WIDTH),
    ("ir1", TILE_HEIGHT, 0),
    ("ir2", TILE_HEIGHT, TILE_WIDTH),
)


class MosaicVideoTrack(VideoStreamTrack):
    kind = "video"

    def __init__(self) -> None:
        super().__init__()
        self._last_pts: int | None = None
        self._mosaic = np.zeros((MOSAIC_HEIGHT, MOSAIC_WIDTH, 3), dtype=np.uint8)

    async def recv(self) -> av.VideoFrame:
        loop = asyncio.get_running_loop()
        while True:
            frame = await loop.run_in_executor(None, self._wait_and_compose)
            if frame is not None:
                return frame

    def _wait_and_compose(self) -> av.VideoFrame | None:
        with frame_condition:
            while True:
                pts = state.frame_pts.get("rgb")
                if (
                    pts is not None
                    and pts != self._last_pts
                    and state.rgb_raw is not None
                ):
                    self._last_pts = pts
                    self._compose()
                    frame = av.VideoFrame.from_ndarray(self._mosaic, format="rgb24")
                    frame.pts = pts
                    frame.time_base = Fraction(1, RTC_CLOCK_RATE)
                    return frame
                if not frame_condition.wait(timeout=0.1):
                    return None

    def _compose(self) -> None:
        for attr, y, x in MOSAIC_LAYOUT:
            frame = getattr(state, attr, None)
            if frame is None:
                self._mosaic[y : y + TILE_HEIGHT, x : x + TILE_WIDTH] = 0
                continue
            if frame.shape[0] != TILE_HEIGHT or frame.shape[1] != TILE_WIDTH:
                tile = cv2.resize(
                    frame, (TILE_WIDTH, TILE_HEIGHT), interpolation=cv2.INTER_AREA
                )
            else:
                tile = frame
            self._mosaic[y : y + TILE_HEIGHT, x : x + TILE_WIDTH] = tile
