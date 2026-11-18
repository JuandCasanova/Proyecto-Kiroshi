"""API web del HUD Kiroshi; procesa fotogramas en memoria y no los almacena."""

from pathlib import Path
import threading

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from interfaces.hud.face_scanner import MediaPipeFaceScanner
from interfaces.hud.object_scanner import YoloSegmentationScanner


MAX_FRAME_BYTES = 2 * 1024 * 1024
WEB_DIRECTORY = Path(__file__).resolve().parents[1] / "hud" / "web"

_initialization_lock = threading.Lock()
_inference_lock = threading.Lock()
_object_scanner: YoloSegmentationScanner | None = None
_face_scanner: MediaPipeFaceScanner | None = None

app = FastAPI(title="Kiroshi HUD API")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def home() -> FileResponse:
    return FileResponse(WEB_DIRECTORY / "index.html")


def _get_scanners() -> tuple[YoloSegmentationScanner, MediaPipeFaceScanner]:
    global _object_scanner, _face_scanner

    if _object_scanner is None or _face_scanner is None:
        with _initialization_lock:
            if _object_scanner is None:
                _object_scanner = YoloSegmentationScanner()
            if _face_scanner is None:
                _face_scanner = MediaPipeFaceScanner()
    return _object_scanner, _face_scanner


def _analyze_frame(frame_bytes: bytes) -> dict[str, object]:
    global _object_scanner, _face_scanner

    frame = cv2.imdecode(np.frombuffer(frame_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=422, detail="No se pudo leer el fotograma JPEG.")

    object_scanner, face_scanner = _get_scanners()
    objects = object_scanner.detect(frame)
    faces = face_scanner.detect(frame)
    return {
        "device": object_scanner.device_name,
        "objects": [
            {
                "category": item.category,
                "score": item.score,
                "box": list(item.box),
            }
            for item in objects
        ],
        "faces": [list(box) for box in faces],
    }


@app.post("/api/scan")
async def scan(request: Request) -> dict[str, object]:
    if request.headers.get("content-type", "").split(";", 1)[0] != "image/jpeg":
        raise HTTPException(status_code=415, detail="Envía el fotograma como image/jpeg.")

    frame = bytearray()
    async for chunk in request.stream():
        if len(frame) + len(chunk) > MAX_FRAME_BYTES:
            raise HTTPException(status_code=413, detail="El fotograma supera el límite de 2 MB.")
        frame.extend(chunk)
    if not frame:
        raise HTTPException(status_code=400, detail="El fotograma está vacío.")

    if not _inference_lock.acquire(blocking=False):
        raise HTTPException(status_code=429, detail="El HUD está procesando otro fotograma.")
    try:
        try:
            return await run_in_threadpool(_analyze_frame, bytes(frame))
        except (ImportError, OSError, RuntimeError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        _inference_lock.release()


app.mount("/", StaticFiles(directory=WEB_DIRECTORY), name="web")


@app.on_event("shutdown")
def close_scanners() -> None:
    if _object_scanner is not None:
        _object_scanner.close()
    if _face_scanner is not None:
        _face_scanner.close()
