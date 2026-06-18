from __future__ import annotations

import asyncio
import contextlib
import json

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.exceptions import InvalidStateError
from aiortc.sdp import candidate_from_sdp
from fastapi import WebSocket, WebSocketDisconnect

from app.vision.mosaic import MosaicVideoTrack

_peer_connections: set[RTCPeerConnection] = set()
_previous_exception_handler = None


def init_realtime_primitives() -> None:
    global _previous_exception_handler
    loop = asyncio.get_running_loop()
    if _previous_exception_handler is not None:
        return
    _previous_exception_handler = loop.get_exception_handler()

    def exception_handler(loop, context):
        exc = context.get("exception")
        if isinstance(exc, InvalidStateError) and "RTCIceTransport is closed" in str(
            exc
        ):
            return
        if _previous_exception_handler is not None:
            _previous_exception_handler(loop, context)
            return
        loop.default_exception_handler(context)

    loop.set_exception_handler(exception_handler)


async def close_all_peer_connections() -> None:
    coros = [_safe_close_peer_connection(pc) for pc in list(_peer_connections)]
    _peer_connections.clear()
    if coros:
        await asyncio.gather(*coros, return_exceptions=True)


async def _safe_close_peer_connection(pc: RTCPeerConnection) -> None:
    if pc.connectionState == "closed":
        _peer_connections.discard(pc)
        return
    try:
        await pc.close()
    except InvalidStateError as exc:
        if "RTCIceTransport is closed" not in str(exc):
            raise
    finally:
        _peer_connections.discard(pc)


def _candidate_from_payload(payload: dict):
    raw = payload.get("candidate")
    if not raw:
        return None
    if raw.startswith("candidate:"):
        raw = raw[len("candidate:") :]
    candidate = candidate_from_sdp(raw)
    candidate.sdpMid = payload.get("sdpMid")
    candidate.sdpMLineIndex = payload.get("sdpMLineIndex")
    return candidate


async def vision_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    pc = RTCPeerConnection()
    _peer_connections.add(pc)

    pc.addTrack(MosaicVideoTrack())

    @pc.on("connectionstatechange")
    async def on_connectionstatechange() -> None:
        if pc.connectionState == "closed":
            _peer_connections.discard(pc)
        elif pc.connectionState == "failed":
            asyncio.create_task(_safe_close_peer_connection(pc))

    try:
        while True:
            payload = json.loads(await websocket.receive_text())
            msg_type = payload.get("type")
            if msg_type == "offer":
                await pc.setRemoteDescription(
                    RTCSessionDescription(sdp=payload["sdp"], type="offer")
                )
                answer = await pc.createAnswer()
                await pc.setLocalDescription(answer)
                await websocket.send_json(
                    {"type": pc.localDescription.type, "sdp": pc.localDescription.sdp}
                )
            elif msg_type == "candidate":
                if pc.connectionState == "closed":
                    continue
                candidate = _candidate_from_payload(payload)
                with contextlib.suppress(InvalidStateError):
                    await pc.addIceCandidate(candidate)
            elif msg_type == "close":
                break
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass
    finally:
        await _safe_close_peer_connection(pc)
