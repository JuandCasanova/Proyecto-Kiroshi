"""Deteccion local de manos mediante MediaPipe Tasks."""

from dataclasses import dataclass
from pathlib import Path
import math
import time
from urllib.request import urlopen

import cv2
import numpy as np


MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)
MODEL_PATH = Path.home() / ".cache" / "kiroshi-optics" / "hand_landmarker.task"


def ensure_model(model_path: Path = MODEL_PATH) -> Path:
    """Descarga una vez el modelo oficial de manos a la cache local."""
    if model_path.is_file() and model_path.stat().st_size > 0:
        return model_path

    model_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = model_path.with_suffix(".task.tmp")
    try:
        with urlopen(MODEL_URL, timeout=30) as response, temporary_path.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        if temporary_path.stat().st_size == 0:
            raise OSError("El archivo del modelo descargado esta vacio.")
        temporary_path.replace(model_path)
    except OSError as exc:
        temporary_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"No se pudo obtener el modelo de manos desde {MODEL_URL}: {exc}"
        ) from exc
    return model_path


@dataclass(frozen=True)
class HandScanResult:
    """Posicion de los dedos y separacion normalizada entre indice y pulgar."""

    thumb_tip: tuple[int, int]
    index_tip: tuple[int, int]
    finger_gap_ratio: float


class MediaPipeHandScanner:
    """Detecta la mano mas visible sin clasificar ni identificar a la persona."""

    def __init__(self) -> None:
        try:
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
        except ImportError as exc:
            raise RuntimeError(
                "MediaPipe Tasks no esta disponible. Reinstala las dependencias "
                "del proyecto con 'python -m pip install -r requirements.txt'."
            ) from exc

        self._mp = mp
        options = vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(ensure_model())),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.55,
            min_hand_presence_confidence=0.55,
            min_tracking_confidence=0.5,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)
        self._last_timestamp_ms = -1

    def detect(self, frame_bgr: np.ndarray) -> HandScanResult | None:
        """Detecta la mano y calcula distancia de pinza relativa al tamano de palma."""
        height, width = frame_bgr.shape[:2]
        detection_frame = frame_bgr
        if width > 640:
            detection_frame = cv2.resize(
                frame_bgr,
                (640, max(1, int(height * 640 / width))),
                interpolation=cv2.INTER_AREA,
            )
        frame_rgb = cv2.cvtColor(detection_frame, cv2.COLOR_BGR2RGB)
        image = self._mp.Image(
            image_format=self._mp.ImageFormat.SRGB,
            data=frame_rgb,
        )
        timestamp_ms = max(self._last_timestamp_ms + 1, int(time.monotonic() * 1000))
        self._last_timestamp_ms = timestamp_ms
        result = self._landmarker.detect_for_video(image, timestamp_ms)
        if not result.hand_landmarks:
            return None

        landmarks = result.hand_landmarks[0]
        thumb = landmarks[4]
        index = landmarks[8]
        wrist = landmarks[0]
        middle_mcp = landmarks[9]
        palm_length = math.hypot(
            (middle_mcp.x - wrist.x) * width,
            (middle_mcp.y - wrist.y) * height,
        )
        if palm_length <= 1:
            return None
        gap_pixels = math.hypot(
            (index.x - thumb.x) * width,
            (index.y - thumb.y) * height,
        )
        return HandScanResult(
            thumb_tip=(int(thumb.x * width), int(thumb.y * height)),
            index_tip=(int(index.x * width), int(index.y * height)),
            finger_gap_ratio=gap_pixels / palm_length,
        )

    def close(self) -> None:
        self._landmarker.close()
