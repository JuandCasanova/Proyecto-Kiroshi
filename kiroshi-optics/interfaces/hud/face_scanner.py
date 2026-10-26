"""Deteccion local de rostros mediante MediaPipe Tasks."""

from pathlib import Path
from urllib.request import urlopen

import cv2
import numpy as np


MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_detector/"
    "blaze_face_short_range/float16/1/blaze_face_short_range.tflite"
)
MODEL_PATH = Path.home() / ".cache" / "kiroshi-optics" / "face_detector.tflite"


def ensure_model(model_path: Path = MODEL_PATH) -> Path:
    """Descarga una vez el modelo oficial de MediaPipe en la cache local."""
    if model_path.is_file() and model_path.stat().st_size > 0:
        return model_path

    model_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = model_path.with_suffix(".tflite.tmp")
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
            f"No se pudo obtener el modelo de deteccion desde {MODEL_URL}: {exc}"
        ) from exc
    return model_path


class MediaPipeFaceScanner:
    """Devuelve cajas delimitadoras de rostros, sin identificacion personal."""

    def __init__(self, min_detection_confidence: float = 0.55) -> None:
        try:
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
        except ImportError as exc:
            raise RuntimeError(
                "MediaPipe no esta instalado. Instala las dependencias con "
                "'python -m pip install -r requirements.txt'."
            ) from exc

        self._mp = mp
        options = vision.FaceDetectorOptions(
            base_options=python.BaseOptions(model_asset_path=str(ensure_model())),
            running_mode=vision.RunningMode.IMAGE,
            min_detection_confidence=min_detection_confidence,
        )
        self._detector = vision.FaceDetector.create_from_options(options)

    def detect(self, frame_bgr: np.ndarray) -> list[tuple[int, int, int, int]]:
        """Detecta rostros y devuelve cajas (x, y, ancho, alto) en pixeles."""
        height, width = frame_bgr.shape[:2]
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = self._mp.Image(
            image_format=self._mp.ImageFormat.SRGB,
            data=frame_rgb,
        )
        result = self._detector.detect(image)

        boxes = []
        for detection in result.detections:
            box = detection.bounding_box
            x = max(0, box.origin_x)
            y = max(0, box.origin_y)
            right = min(width, box.origin_x + box.width)
            bottom = min(height, box.origin_y + box.height)
            if right > x and bottom > y:
                boxes.append((x, y, right - x, bottom - y))
        return boxes

    def close(self) -> None:
        self._detector.close()
