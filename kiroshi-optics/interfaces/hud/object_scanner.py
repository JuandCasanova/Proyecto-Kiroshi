"""Segmentacion local de instancias con YOLO y aceleracion CUDA opcional."""

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
import threading

import cv2
import numpy as np


MODEL_NAME = "yolo11n-seg.pt"
MODEL_PATH = Path.home() / ".cache" / "kiroshi-optics" / MODEL_NAME
ALLOWED_CATEGORIES = frozenset(
    {
        "person",
        "bottle",
        "cup",
        "laptop",
        "keyboard",
        "tv",
        "cat",
        "dog",
        "teddy bear",
    }
)
SCORE_THRESHOLD = 0.4
MAX_RESULTS = 10
SAMPLE_INTERVAL = 0.25


@dataclass(frozen=True)
class ObjectDetection:
    category: str
    score: float
    box: tuple[int, int, int, int]
    contour: tuple[tuple[int, int], ...]


class YoloSegmentationScanner:
    """Calcula máscaras de objetos en segundo plano y conserva solo el último resultado."""

    def __init__(self) -> None:
        try:
            import torch
            from ultralytics import YOLO
            from ultralytics.utils.downloads import attempt_download_asset
        except ImportError as exc:
            raise RuntimeError(
                "La segmentacion requiere PyTorch y Ultralytics. Instala las "
                "dependencias del proyecto con 'python -m pip install -r requirements.txt'."
            ) from exc

        self._device = "0" if torch.cuda.is_available() else "cpu"
        if self._device == "0":
            self.device_name = f"CUDA: {torch.cuda.get_device_name(0)}"
        else:
            self.device_name = "CPU (CUDA no disponible)"

        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            model_path = attempt_download_asset(MODEL_PATH)
            self._model = YOLO(model_path)
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            raise RuntimeError(f"No se pudo cargar el modelo de segmentacion: {exc}") from exc

        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="kiroshi-seg")
        self._future: Future[tuple[ObjectDetection, ...]] | None = None
        self._last_submitted_at = float("-inf")
        self._detections: tuple[ObjectDetection, ...] = ()
        self._error: str | None = None

    def submit(self, frame_bgr: np.ndarray, now: float) -> bool:
        """Envia hasta cuatro fotogramas por segundo sin acumular inferencias."""
        with self._lock:
            if (
                self._future is not None
                or now - self._last_submitted_at < SAMPLE_INTERVAL
            ):
                return False
            self._last_submitted_at = now
            self._future = self._executor.submit(self._infer, frame_bgr.copy())
            return True

    def _infer(self, frame_bgr: np.ndarray) -> tuple[ObjectDetection, ...]:
        height, width = frame_bgr.shape[:2]
        result = self._model.predict(
            source=frame_bgr,
            conf=SCORE_THRESHOLD,
            imgsz=640,
            device=self._device,
            max_det=MAX_RESULTS,
            retina_masks=True,
            verbose=False,
        )[0]
        if result.boxes is None or result.masks is None:
            return ()

        boxes = result.boxes.xyxy.detach().cpu().numpy()
        scores = result.boxes.conf.detach().cpu().numpy()
        class_ids = result.boxes.cls.detach().cpu().numpy().astype(int)
        masks = result.masks.data.detach().cpu().numpy()
        detections = []
        for index, class_id in enumerate(class_ids):
            category = str(result.names[int(class_id)]).lower()
            if category not in ALLOWED_CATEGORIES or index >= len(masks):
                continue

            mask = masks[index].astype(np.uint8)
            if mask.shape != (height, width):
                mask = cv2.resize(mask, (width, height), interpolation=cv2.INTER_NEAREST)
            contours, _ = cv2.findContours(
                mask,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE,
            )
            if not contours:
                continue
            contour = max(contours, key=cv2.contourArea)
            if len(contour) < 3:
                continue

            x1, y1, x2, y2 = boxes[index]
            left = max(0, min(width, int(x1)))
            top = max(0, min(height, int(y1)))
            right = max(left, min(width, int(x2)))
            bottom = max(top, min(height, int(y2)))
            detections.append(
                ObjectDetection(
                    category=category,
                    score=float(scores[index]),
                    box=(left, top, right - left, bottom - top),
                    contour=tuple(
                        (int(point[0][0]), int(point[0][1]))
                        for point in contour
                    ),
                )
            )
        return tuple(detections)

    def snapshot(self) -> tuple[tuple[ObjectDetection, ...], str | None]:
        with self._lock:
            future = self._future
            if future is None or not future.done():
                return self._detections, self._error
            self._future = None

        try:
            detections = future.result()
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            with self._lock:
                self._detections = ()
                self._error = f"Fallo la inferencia de segmentacion: {exc}"
                return self._detections, self._error

        with self._lock:
            self._detections = detections
            self._error = None
            return self._detections, self._error

    @staticmethod
    def computer_setup_summary(
        detections: tuple[ObjectDetection, ...],
    ) -> str | None:
        laptops = [item for item in detections if item.category == "laptop"]
        if laptops:
            return "COMPUTADORA: LAPTOP (deteccion general)"

        screens = [item for item in detections if item.category == "tv"]
        keyboards = [item for item in detections if item.category == "keyboard"]
        for screen in screens:
            sx, sy, sw, sh = screen.box
            screen_center_y = sy + sh / 2
            for keyboard in keyboards:
                kx, ky, kw, kh = keyboard.box
                keyboard_center_y = ky + kh / 2
                horizontal_overlap = max(0, min(sx + sw, kx + kw) - max(sx, kx))
                overlap_ratio = horizontal_overlap / max(1, min(sw, kw))
                if keyboard_center_y > screen_center_y and overlap_ratio >= 0.25:
                    return (
                        "COMPONENTES: PANTALLA/TV + TECLADO "
                        "(TORRE O AIO NO CONFIRMADOS)"
                    )
        return None

    def close(self) -> None:
        self._executor.shutdown(wait=True, cancel_futures=True)
