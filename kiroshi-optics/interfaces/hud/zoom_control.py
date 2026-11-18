"""Control de zoom continuo por distancia entre indice y pulgar."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ZoomGestureStatus:
    zoom: float
    message: str
    progress: float


class ZoomGestureController:
    """Convierte la apertura de los dedos en una escala fluida."""

    MIN_GAP_RATIO = 0.12
    MAX_GAP_RATIO = 0.68
    SMOOTHING = 0.24

    def __init__(self, initial_zoom: float = 1.0) -> None:
        self.zoom = min(3.0, max(0.7, initial_zoom))
        self._last_gap_ratio: float | None = None

    def update(self, finger_gap_ratio: float | None, now: float) -> ZoomGestureStatus:
        """Actualiza el zoom directamente con cada lectura de la pinza."""
        if finger_gap_ratio is None:
            self._last_gap_ratio = None
            return ZoomGestureStatus(self.zoom, "MUESTRA LA MANO", 0.0)

        gap = min(
            self.MAX_GAP_RATIO,
            max(self.MIN_GAP_RATIO, finger_gap_ratio),
        )
        normalized = (gap - self.MIN_GAP_RATIO) / (
            self.MAX_GAP_RATIO - self.MIN_GAP_RATIO
        )
        target_zoom = 0.7 + normalized * (3.0 - 0.7)

        if self._last_gap_ratio is None:
            self.zoom = target_zoom
        else:
            self.zoom += (target_zoom - self.zoom) * self.SMOOTHING
        self.zoom = min(3.0, max(0.7, self.zoom))
        self._last_gap_ratio = gap

        progress = (self.zoom - 0.7) / (3.0 - 0.7)
        if finger_gap_ratio <= self.MIN_GAP_RATIO + 0.04:
            message = "PINZA CERRADA // ALEJA"
        elif finger_gap_ratio >= self.MAX_GAP_RATIO - 0.04:
            message = "PINZA ABIERTA // ACERCA"
        else:
            message = "PINZA FLUIDA // ZOOM"
        return ZoomGestureStatus(self.zoom, message, progress)
