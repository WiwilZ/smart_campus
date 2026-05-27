from __future__ import annotations

import threading

from vision_pipeline import capture_loop
from vision_recording import writer_loop
from vision_state import pipeline_stop_event, shutdown_event, start_event, write_queues

capture_thread: threading.Thread | None = None
writer_thread: threading.Thread | None = None


def start_worker_threads() -> None:
    global capture_thread, writer_thread
    if capture_thread is None or not capture_thread.is_alive():
        capture_thread = threading.Thread(target=capture_loop, daemon=True)
        capture_thread.start()
    if writer_thread is None or not writer_thread.is_alive():
        writer_thread = threading.Thread(target=writer_loop, daemon=True)
        writer_thread.start()


def shutdown_worker_threads() -> None:
    shutdown_event.set()
    pipeline_stop_event.set()
    start_event.set()
    for q in write_queues.values():
        try:
            q.put_nowait(None)
        except Exception:
            pass
    for thread in (capture_thread, writer_thread):
        if thread is not None:
            try:
                thread.join(timeout=2.0)
            except Exception:
                pass
