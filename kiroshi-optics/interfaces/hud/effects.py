"""Efectos de imagen para el visor HUD."""

import cv2
import numpy as np


class CyberpunkEffects:
    """Aplica gradacion de color, distorsion de lente y scanlines."""

    def __init__(self) -> None:
        self._map_size: tuple[int, int] | None = None
        self._map_x: np.ndarray | None = None
        self._map_y: np.ndarray | None = None

    def _get_lens_maps(self, width: int, height: int) -> tuple[np.ndarray, np.ndarray]:
        if self._map_size != (width, height):
            x, y = np.meshgrid(
                np.arange(width, dtype=np.float32),
                np.arange(height, dtype=np.float32),
            )
            center_x, center_y = width / 2, height / 2
            normalized_x = (x - center_x) / max(center_x, 1)
            normalized_y = (y - center_y) / max(center_y, 1)
            radius_squared = normalized_x**2 + normalized_y**2
            strength = 0.025
            self._map_x = x + (x - center_x) * radius_squared * strength
            self._map_y = y + (y - center_y) * radius_squared * strength
            self._map_size = (width, height)
        assert self._map_x is not None and self._map_y is not None
        return self._map_x, self._map_y

    def apply(self, frame: np.ndarray, danger_mode: bool, glitch_enabled: bool) -> np.ndarray:
        height, width = frame.shape[:2]
        map_x, map_y = self._get_lens_maps(width, height)
        distorted = cv2.remap(
            frame,
            map_x,
            map_y,
            interpolation=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT,
        )

        graded = cv2.convertScaleAbs(distorted, alpha=1.12, beta=4)
        if danger_mode:
            gray = cv2.cvtColor(graded, cv2.COLOR_BGR2GRAY)
            danger_tint = cv2.applyColorMap(gray, cv2.COLORMAP_HOT)
            graded = cv2.addWeighted(graded, 0.72, danger_tint, 0.28, 0)

        if glitch_enabled:
            graded[::4] = (graded[::4].astype(np.float32) * 0.78).astype(np.uint8)
            if np.random.random() < 0.035:
                offset = np.random.randint(-8, 9)
                graded = np.roll(graded, offset, axis=1)
        return graded
