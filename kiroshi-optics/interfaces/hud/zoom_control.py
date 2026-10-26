"""Control de zoom con gestos sostenidos de pinza entre indice y pulgar."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ZoomGestureStatus:
    zoom: float
    message: str
    progress: float


class ZoomGestureController:
    """Interpreta cambios entre dedos separados y juntos durante un segundo."""

    GESTURE_DURATION = 1.0
    COOLDOWN_DURATION = 1.5
    PINCH_THRESHOLD = 0.22
    OPEN_THRESHOLD = 0.48

    def __init__(self, initial_zoom: float = 1.0) -> None:
        self.zoom = min(3.0, max(0.7, initial_zoom))
        self._reference_pose: str | None = None
        self._candidate_pose: str | None = None
        self._candidate_since: float | None = None
        self._missing_since: float | None = None
        self._cooldown_until: float | None = None

    @staticmethod
    def _classify_pose(finger_gap_ratio: float) -> str | None:
        if finger_gap_ratio <= ZoomGestureController.PINCH_THRESHOLD:
            return "pinch"
        if finger_gap_ratio >= ZoomGestureController.OPEN_THRESHOLD:
            return "open"
        return None

    def update(self, finger_gap_ratio: float | None, now: float) -> ZoomGestureStatus:
        """Actualiza el gesto con un segundo de confirmacion y pausa entre acciones."""
        if self._cooldown_until is not None:
            if now < self._cooldown_until:
                self._candidate_pose = None
                self._candidate_since = None
                self._missing_since = None
                progress = 1 - (self._cooldown_until - now) / self.COOLDOWN_DURATION
                return ZoomGestureStatus(
                    self.zoom,
                    "PAUSA // POSICIONA LOS DEDOS",
                    min(1.0, max(0.0, progress)),
                )

            self._cooldown_until = None
            self._candidate_pose = None
            self._candidate_since = None
            self._reference_pose = (
                self._classify_pose(finger_gap_ratio)
                if finger_gap_ratio is not None
                else None
            )
            self._missing_since = now if finger_gap_ratio is None else None
            message = "GESTO LISTO" if self._reference_pose is not None else "MUESTRA LA MANO"
            return ZoomGestureStatus(self.zoom, message, 0.0)

        if finger_gap_ratio is None:
            self._candidate_pose = None
            self._candidate_since = None
            if self._missing_since is None:
                self._missing_since = now
            elif now - self._missing_since >= 0.6:
                self._reference_pose = None
            return ZoomGestureStatus(self.zoom, "MUESTRA LA MANO", 0.0)

        self._missing_since = None
        pose = self._classify_pose(finger_gap_ratio)
        if pose is None:
            self._candidate_pose = None
            self._candidate_since = None
            return ZoomGestureStatus(self.zoom, "SEPARA O JUNTA INDICE Y PULGAR", 0.0)

        if self._reference_pose is None:
            self._reference_pose = pose
            self._candidate_pose = None
            self._candidate_since = None
            return ZoomGestureStatus(self.zoom, "GESTO INICIAL DETECTADO", 0.0)

        if pose == self._reference_pose:
            self._candidate_pose = None
            self._candidate_since = None
            return ZoomGestureStatus(self.zoom, "GESTO LISTO", 0.0)

        if pose != self._candidate_pose:
            self._candidate_pose = pose
            self._candidate_since = now

        assert self._candidate_since is not None
        elapsed = now - self._candidate_since
        progress = min(1.0, elapsed / self.GESTURE_DURATION)
        if elapsed < self.GESTURE_DURATION:
            message = (
                "JUNTA LOS DEDOS // ZOOM OUT"
                if self._reference_pose == "open"
                else "SEPARA LOS DEDOS // ZOOM IN"
            )
            return ZoomGestureStatus(self.zoom, message, progress)

        if self._reference_pose == "open":
            self.zoom = max(0.7, self.zoom / 1.2)
            action = "ZOOM OUT"
        else:
            self.zoom = min(3.0, self.zoom * 1.2)
            action = "ZOOM IN"
        self._reference_pose = None
        self._candidate_pose = None
        self._candidate_since = None
        self._cooldown_until = now + self.COOLDOWN_DURATION
        return ZoomGestureStatus(self.zoom, action, 1.0)
