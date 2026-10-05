"""Integracion pura con APIs de vision (deteccion, segmentacion, OCR).

Sin logica de agente ni de especificidad: solo expone llamadas tipadas.
Las skills de vision se apoyaran en este cliente.
"""

from typing import Any


class VisionApiClient:
    """Envoltura minima sobre proveedores de vision."""

    def detect_objects(self, media_ref: str, labels: list[str] | None = None) -> dict[str, Any]:
        raise NotImplementedError

    def segment(self, media_ref: str, bbox: list[float]) -> dict[str, Any]:
        raise NotImplementedError

    def ocr(self, media_ref: str, bbox: list[float] | None = None) -> dict[str, Any]:
        raise NotImplementedError