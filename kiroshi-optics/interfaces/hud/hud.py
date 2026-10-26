"""Composicion visual y ciclo principal del Kiroshi HUD."""

from contextlib import ExitStack
from dataclasses import dataclass
from datetime import datetime
import random
import time

import cv2
import numpy as np

from interfaces.hud.effects import CyberpunkEffects
from interfaces.hud.face_scanner import MediaPipeFaceScanner
from interfaces.hud.hand_scanner import HandScanResult, MediaPipeHandScanner
from interfaces.hud.object_scanner import ObjectDetection, YoloSegmentationScanner
from interfaces.hud.zoom_control import ZoomGestureController, ZoomGestureStatus


CYAN = (255, 230, 45)
RED = (40, 55, 255)
WHITE = (220, 245, 245)
PANEL = (18, 28, 31)

NPC_NAMES = ("PERSONA",)
AFFILIATIONS = ("UNIMINUTO",)


@dataclass(frozen=True)
class FictionalProfile:
    name: str
    affiliation: str
    bounty: int


class KiroshiHUD:
    """Muestra video en vivo con escaneo facial y elementos HUD ficticios."""

    def __init__(self, camera_source: int | str = 0) -> None:
        with ExitStack() as resources:
            camera = cv2.VideoCapture(camera_source)
            if not camera.isOpened():
                camera.release()
                raise RuntimeError(
                    f"No se pudo abrir la fuente de video {camera_source!r}. "
                    "Comprueba el indice de la camara o la URL de streaming, "
                    "que el dispositivo este en la misma red y que la URL sea "
                    "accesible desde este equipo."
                )
            resources.callback(camera.release)
            scanner = MediaPipeFaceScanner()
            resources.callback(scanner.close)
            self._camera = camera
            self._scanner = scanner
            self._resources = resources.pop_all()

        self._effects = CyberpunkEffects()
        self._danger_mode = False
        self._glitch_enabled = True
        self._scan_mode = False
        self._object_scanner: YoloSegmentationScanner | None = None
        self._object_scan_error: str | None = None
        self._zoom_enabled = False
        self._hand_scanner: MediaPipeHandScanner | None = None
        self._hand_scan_error: str | None = None
        self._zoom_controller = ZoomGestureController()
        self._zoom_status = ZoomGestureStatus(1.0, "MUESTRA LA MANO", 0.0)
        self._profiles: list[FictionalProfile] = []
        self._started_at = time.monotonic()
        self._last_frame_at = self._started_at
        self._fps = 0.0

    @property
    def _accent(self) -> tuple[int, int, int]:
        return RED if self._danger_mode else CYAN

    def _profile_for(self, index: int) -> FictionalProfile:
        while len(self._profiles) <= index:
            self._profiles.append(FictionalProfile(
                name=random.choice(NPC_NAMES),
                affiliation=random.choice(AFFILIATIONS),
                bounty=random.randrange(1_000, 75_001, 500),
            ))
        return self._profiles[index]

    def _draw_text(
        self,
        frame: np.ndarray,
        text: str,
        origin: tuple[int, int],
        color: tuple[int, int, int],
        scale: float = 0.48,
        thickness: int = 1,
    ) -> None:
        cv2.putText(
            frame, text, origin, cv2.FONT_HERSHEY_DUPLEX, scale, color,
            thickness, cv2.LINE_AA,
        )

    def _draw_frame_corners(self, frame: np.ndarray) -> None:
        height, width = frame.shape[:2]
        inset, length = 22, 42
        color = self._accent
        for x, y, horizontal, vertical in (
            (inset, inset, 1, 1),
            (width - inset, inset, -1, 1),
            (inset, height - inset, 1, -1),
            (width - inset, height - inset, -1, -1),
        ):
            cv2.line(frame, (x, y), (x + horizontal * length, y), color, 2)
            cv2.line(frame, (x, y), (x, y + vertical * length), color, 2)

    def _draw_reticle(self, frame: np.ndarray) -> None:
        height, width = frame.shape[:2]
        center = (width // 2, height // 2)
        color = self._accent
        cv2.circle(frame, center, 17, color, 1, cv2.LINE_AA)
        cv2.circle(frame, center, 3, color, -1, cv2.LINE_AA)
        cv2.line(frame, (center[0] - 28, center[1]), (center[0] - 7, center[1]), color, 1)
        cv2.line(frame, (center[0] + 7, center[1]), (center[0] + 28, center[1]), color, 1)
        cv2.line(frame, (center[0], center[1] - 28), (center[0], center[1] - 7), color, 1)
        cv2.line(frame, (center[0], center[1] + 7), (center[0], center[1] + 28), color, 1)

    def _draw_face(self, frame: np.ndarray, box: tuple[int, int, int, int], index: int) -> None:
        x, y, width, height = box
        color = self._accent
        corner = max(12, min(width, height) // 5)
        right, bottom = x + width, y + height
        for start, end in (
            ((x, y), (x + corner, y)), ((x, y), (x, y + corner)),
            ((right, y), (right - corner, y)), ((right, y), (right, y + corner)),
            ((x, bottom), (x + corner, bottom)), ((x, bottom), (x, bottom - corner)),
            ((right, bottom), (right - corner, bottom)),
            ((right, bottom), (right, bottom - corner)),
        ):
            cv2.line(frame, start, end, color, 2, cv2.LINE_AA)

        profile = self._profile_for(index)
        panel_width, panel_height = 224, 85
        panel_x = min(max(x, 6), max(6, frame.shape[1] - panel_width - 6))
        panel_y = y - panel_height - 8
        if panel_y < 36:
            panel_y = min(bottom + 8, frame.shape[0] - panel_height - 34)
        panel_y = max(30, panel_y)
        cv2.rectangle(
            frame, (panel_x, panel_y), (panel_x + panel_width, panel_y + panel_height),
            PANEL, -1,
        )
        cv2.rectangle(
            frame, (panel_x, panel_y), (panel_x + panel_width, panel_y + panel_height),
            color, 1,
        )
        self._draw_text(frame, "SIMULATED // NOT IDENTIFIED", (panel_x + 7, panel_y + 15), color, 0.34)
        self._draw_text(frame, f"NAME: {profile.name}", (panel_x + 7, panel_y + 34), WHITE, 0.39)
        self._draw_text(frame, f"AFFIL: {profile.affiliation}", (panel_x + 7, panel_y + 52), WHITE, 0.34)
        self._draw_text(frame, f"BOUNTY: ${profile.bounty:,} EDDIES", (panel_x + 7, panel_y + 70), WHITE, 0.34)

    def _draw_status(self, frame: np.ndarray, face_count: int, object_count: int) -> None:
        height, width = frame.shape[:2]
        color = self._accent
        self._draw_text(frame, "KIROSHI OPTICS v3.2.1 // CONNECTED", (30, 34), color, 0.55, 1)
        self._draw_text(frame, "SIMULATED DATA // NO IDENTITY ANALYSIS", (30, 53), WHITE, 0.35)
        status = f"{self._fps:04.1f} FPS  //  {datetime.now():%Y-%m-%d %H:%M:%S}"
        self._draw_text(frame, status, (max(30, width - 370), 34), color, 0.43)
        self._draw_text(frame, "N 35°40' / E 139°45'  //  GPS SIM", (max(30, width - 315), 53), WHITE, 0.38)

        elapsed = time.monotonic() - self._started_at
        progress = (elapsed % 3.0) / 3.0
        bar_x, bar_y, bar_width = 30, height - 31, min(220, width // 3)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + 8), WHITE, 1)
        cv2.rectangle(
            frame, (bar_x + 1, bar_y + 1),
            (bar_x + max(1, int((bar_width - 2) * progress)), bar_y + 7),
            color, -1,
        )
        self._draw_text(
            frame,
            (
                f"SCANNING...  PERSONS {face_count:02d}  OBJECTS {object_count:02d}"
                if self._scan_mode
                else f"PERSONS {face_count:02d}  //  OBJECT SCAN OFF"
            ),
            (bar_x + bar_width + 12, height - 23),
            color,
            0.35,
        )
        self._draw_text(
            frame,
            (
                f"E: SCAN {'ON' if self._scan_mode else 'OFF'}  "
                f"Z: ZOOM {'ON' if self._zoom_enabled else 'OFF'}  "
                "C: COLOR  G: GLITCH  Q: EXIT"
            ),
            (max(30, width - 500), height - 42),
            WHITE,
            0.32,
        )
        if self._object_scan_error and (
            self._scan_mode or self._object_scanner is None
        ):
            self._draw_text(
                frame,
                f"OBJECT SCAN: {self._object_scan_error[:90]}",
                (30, 78),
                RED,
                0.36,
            )
        elif self._hand_scan_error:
            self._draw_text(frame, f"SCAN: {self._hand_scan_error[:90]}", (30, 78), RED, 0.36)
        elif self._scan_mode:
            scan_status = "OBJECT SCAN // ACTIVE"
            if self._zoom_enabled:
                scan_status = (
                    f"ZOOM // {self._zoom_status.message} "
                    f"{self._zoom_status.progress * 100:03.0f}% "
                    f"{self._zoom_status.zoom:.2f}X"
                )
            if self._object_scanner is not None:
                scan_status = f"{scan_status} // {self._object_scanner.device_name}"
            self._draw_text(frame, scan_status, (30, 78), self._accent, 0.38)
            if self._zoom_enabled:
                bar_x, bar_y, bar_width = 30, 87, 220
                cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + 6), WHITE, 1)
            if self._zoom_enabled and self._zoom_status.progress > 0:
                cv2.rectangle(
                    frame,
                    (bar_x + 1, bar_y + 1),
                    (bar_x + max(1, int((bar_width - 2) * self._zoom_status.progress)), bar_y + 5),
                    self._accent,
                    -1,
                )

    @staticmethod
    def _apply_zoom(frame: np.ndarray, zoom: float) -> np.ndarray:
        """Simula zoom digital centrado conservando el tamano original del cuadro."""
        height, width = frame.shape[:2]
        if abs(zoom - 1.0) < 0.01:
            return frame
        if zoom > 1.0:
            crop_width = max(1, int(width / zoom))
            crop_height = max(1, int(height / zoom))
            x = (width - crop_width) // 2
            y = (height - crop_height) // 2
            crop = frame[y:y + crop_height, x:x + crop_width]
            return cv2.resize(crop, (width, height), interpolation=cv2.INTER_LINEAR)

        scaled_width = max(1, int(width * zoom))
        scaled_height = max(1, int(height * zoom))
        scaled = cv2.resize(
            frame,
            (scaled_width, scaled_height),
            interpolation=cv2.INTER_AREA,
        )
        canvas = np.zeros_like(frame)
        x = (width - scaled_width) // 2
        y = (height - scaled_height) // 2
        canvas[y:y + scaled_height, x:x + scaled_width] = scaled
        return canvas

    def _draw_hand_gesture(
        self,
        frame: np.ndarray,
        result: HandScanResult | None,
    ) -> None:
        if result is None:
            return
        color = self._accent
        cv2.line(frame, result.thumb_tip, result.index_tip, color, 2, cv2.LINE_AA)
        for point in (result.thumb_tip, result.index_tip):
            cv2.circle(frame, point, 9, color, 2, cv2.LINE_AA)

    def _draw_objects(
        self,
        frame: np.ndarray,
        detections: tuple[ObjectDetection, ...],
    ) -> None:
        labels = {
            "person": "PERSONA",
            "bottle": "BOTELLA",
            "cup": "TAZA/POCILLO",
            "laptop": "LAPTOP",
            "keyboard": "TECLADO",
            "tv": "PANTALLA/TV",
            "cat": "GATO",
            "dog": "PERRO",
            "teddy bear": "JUGUETE (PELUCHE)",
        }
        for detection in detections:
            x, y, width, height = detection.box
            color = self._accent
            contour = np.asarray(detection.contour, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [contour], True, color, 2, cv2.LINE_AA)
            text = f"{labels.get(detection.category, detection.category.upper())} {detection.score:.0%}"
            text_y = max(18, y - 6)
            self._draw_text(frame, text, (x, text_y), color, 0.38)

        summary = YoloSegmentationScanner.computer_setup_summary(detections)
        if summary:
            self._draw_text(frame, summary, (30, 108), self._accent, 0.38)

    def run(self) -> None:
        """Ejecuta el visor hasta pulsar q; libera los recursos al salir."""
        try:
            while True:
                success, frame = self._camera.read()
                if not success:
                    raise RuntimeError("La camara dejo de entregar fotogramas.")
                frame = cv2.flip(frame, 1)
                now = time.monotonic()
                delta = now - self._last_frame_at
                self._last_frame_at = now
                if delta > 0:
                    instant_fps = 1 / delta
                    self._fps = instant_fps if self._fps == 0 else self._fps * 0.88 + instant_fps * 0.12

                hand_result = None
                if self._zoom_enabled and self._hand_scanner is not None:
                    hand_result = self._hand_scanner.detect(frame)
                    self._zoom_status = self._zoom_controller.update(
                        hand_result.finger_gap_ratio if hand_result else None,
                        now,
                    )

                if self._zoom_enabled:
                    self._draw_hand_gesture(frame, hand_result)
                frame = self._apply_zoom(
                    frame,
                    self._zoom_controller.zoom if self._zoom_enabled else 1.0,
                )
                object_detections: tuple[ObjectDetection, ...] = ()
                if self._scan_mode and self._object_scanner is not None:
                    try:
                        self._object_scanner.submit(frame, now)
                    except RuntimeError as exc:
                        self._object_scan_error = str(exc)
                    object_detections, self._object_scan_error = self._object_scanner.snapshot()
                frame = self._effects.apply(frame, self._danger_mode, self._glitch_enabled)
                boxes = self._scanner.detect(frame)
                if self._scan_mode:
                    self._draw_objects(frame, object_detections)
                for index, box in enumerate(boxes):
                    self._draw_face(frame, box, index)
                self._draw_reticle(frame)
                self._draw_frame_corners(frame)
                self._draw_status(frame, len(boxes), len(object_detections))

                cv2.imshow("KIROSHI OPTICS // HUD SIMULATION", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                if key == ord("c"):
                    self._danger_mode = not self._danger_mode
                if key == ord("g"):
                    self._glitch_enabled = not self._glitch_enabled
                if key == ord("e"):
                    if self._scan_mode:
                        self._scan_mode = False
                        self._zoom_enabled = False
                        self._hand_scan_error = None
                    else:
                        try:
                            if self._object_scanner is None:
                                self._object_scanner = YoloSegmentationScanner()
                                self._resources.callback(self._object_scanner.close)
                            self._object_scan_error = None
                            self._scan_mode = True
                        except RuntimeError as exc:
                            self._object_scan_error = str(exc)
                if key == ord("z") and self._scan_mode:
                    if self._zoom_enabled:
                        self._zoom_enabled = False
                        self._hand_scan_error = None
                    else:
                        try:
                            if self._hand_scanner is None:
                                self._hand_scanner = MediaPipeHandScanner()
                                self._resources.callback(self._hand_scanner.close)
                            self._hand_scan_error = None
                            self._zoom_enabled = True
                        except RuntimeError as exc:
                            self._hand_scan_error = str(exc)
        finally:
            try:
                self._resources.close()
            finally:
                cv2.destroyAllWindows()
