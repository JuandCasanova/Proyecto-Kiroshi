import asyncio
import base64
import logging
import threading
import time
from typing import List

from contextlib import asynccontextmanager

import cv2
import numpy as np
import torch
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("kiroshi.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("kiroshi")

model = None
camera = None
connected_clients: List[WebSocket] = []

DETECTION_CLASSES = ["person", "car", "dog", "bottle", "cell phone"]
MAX_DETECTIONS = 5
CONFIDENCE_THRESHOLD = 0.5
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
TARGET_FPS = 30
CAMERA_INDEX = 0

inference_lock = threading.Lock()
broadcaster_alive = False
broadcaster_error = None
last_frame_time = 0.0
_broadcaster_task: asyncio.Task | None = None


def load_model():
    global model
    model = YOLO("yolov8n.pt")
    if torch.cuda.is_available():
        model.to("cuda")
        log.info("YOLOv8-nano cargado en GPU: %s", torch.cuda.get_device_name(0))
    else:
        log.warning("YOLOv8-nano cargado en CPU (sin CUDA)")
    log.info("Primera inferencia de warmup...")
    dummy = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
    _ = model(dummy, conf=CONFIDENCE_THRESHOLD, verbose=False)
    log.info("Warmup completado")


def open_camera():
    global camera
    if camera is not None:
        camera.release()
    camera = cv2.VideoCapture(CAMERA_INDEX)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    camera.set(cv2.CAP_PROP_FPS, TARGET_FPS)
    if camera.isOpened():
        log.info(
            "Camara inicializada: %sx%s @ %sfps",
            FRAME_WIDTH,
            FRAME_HEIGHT,
            TARGET_FPS,
        )
        return True
    log.error("NO se pudo abrir la camara (indice %s)", CAMERA_INDEX)
    return False


async def capture_broadcaster():
    global broadcaster_alive, broadcaster_error, last_frame_time
    log.info("Productor de frames iniciado")
    frame_interval = 1.0 / TARGET_FPS
    camera_failures = 0
    broadcaster_alive = True

    try:
        while True:
            start_time = time.time()

            try:
                ret, frame = camera.read()
                if not ret:
                    camera_failures += 1
                    log.warning("Fallo lectura de camara (intento %s)", camera_failures)
                    if camera_failures >= 5:
                        log.error("Reiniciando camara...")
                        open_camera()
                        camera_failures = 0
                    await asyncio.sleep(0.05)
                    continue
                camera_failures = 0
            except Exception as e:
                log.exception("Error leyendo camara: %s", e)
                await asyncio.sleep(0.5)
                continue

            try:
                detections = await asyncio.to_thread(run_inference, frame)
            except Exception as e:
                log.exception("Error en inferencia: %s", e)
                detections = []

            try:
                _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                frame_base64 = base64.b64encode(buffer).decode("utf-8")
            except Exception as e:
                log.exception("Error codificando frame: %s", e)
                await asyncio.sleep(0.1)
                continue

            last_frame_time = time.time()
            payload = {
                "frame": frame_base64,
                "detections": detections,
                "timestamp": time.time(),
                "fps": round(1.0 / max(time.time() - start_time, 0.001), 1),
            }

            for ws in list(connected_clients):
                try:
                    await ws.send_json(payload)
                except Exception as e:
                    log.debug("Cliente no disponible, eliminado: %s", e)
                    connected_clients.remove(ws)

            elapsed = time.time() - start_time
            sleep_time = max(0, frame_interval - elapsed)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
    except asyncio.CancelledError:
        broadcaster_alive = False
        raise
    except Exception as e:
        broadcaster_alive = False
        broadcaster_error = str(e)
        log.critical("Productor de frames DETENIDO: %s", e)


async def watchdog():
    global _broadcaster_task
    log.info("Watchdog iniciado")
    while True:
        await asyncio.sleep(5)
        if _broadcaster_task is None or _broadcaster_task.done():
            log.critical("Watchdog detecto productor caido. Reiniciando...")
            broadcaster_error = None
            _broadcaster_task = asyncio.create_task(capture_broadcaster())


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _broadcaster_task
    load_model()
    open_camera()
    _broadcaster_task = asyncio.create_task(capture_broadcaster())
    asyncio.create_task(watchdog())
    yield
    global camera
    if camera is not None:
        camera.release()
        log.info("Camara liberada")


app = FastAPI(title="Kiroshi Optics API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    cam_status = "ok" if (camera is not None and camera.isOpened()) else "error"
    return {
        "status": "online",
        "model": "yolov8n",
        "cuda": model.device.type if model else "unknown",
        "camera": cam_status,
        "broadcaster": "ok" if broadcaster_alive else f"STOPPED: {broadcaster_error}",
        "last_frame_seconds_ago": (
            round(time.time() - last_frame_time, 1) if last_frame_time else "n/a"
        ),
    }


def run_inference(frame):
    with inference_lock:
        results = model(
            frame,
            conf=CONFIDENCE_THRESHOLD,
            verbose=False,
            device=0,
        )
        detections = []
        count = 0
        for r in results:
            boxes = r.boxes
            if boxes is None:
                continue
            for box in boxes:
                if count >= MAX_DETECTIONS:
                    break

                cls_id = int(box.cls[0])
                class_name = model.names[cls_id]

                if class_name not in DETECTION_CLASSES:
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = float(box.conf[0])

                detections.append(
                    {
                        "id": count,
                        "class": class_name,
                        "confidence": round(confidence, 3),
                        "bbox": {
                            "x1": x1,
                            "y1": y1,
                            "x2": x2,
                            "y2": y2,
                        },
                        "center": {"x": (x1 + x2) // 2, "y": (y1 + y2) // 2},
                        "size": {"width": x2 - x1, "height": y2 - y1},
                    }
                )
                count += 1
        return detections


@app.websocket("/ws/detect")
async def websocket_detection(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    log.info("Cliente conectado. Total: %s", len(connected_clients))

    try:
        while True:
            await asyncio.sleep(3600)
    except WebSocketDisconnect:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        log.info("Cliente desconectado. Total: %s", len(connected_clients))
    except Exception:
        if websocket in connected_clients:
            connected_clients.remove(websocket)