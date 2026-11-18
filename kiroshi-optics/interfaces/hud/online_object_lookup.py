"""Verificacion visual puntual con Gemini y busqueda web fundamentada."""

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
import base64
import json
import os
import threading
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import cv2
import numpy as np

from interfaces.hud.object_scanner import ObjectDetection


API_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
MODEL = "gemini-3.1-flash-lite"
MAX_IMAGE_DIMENSION = 768
REQUEST_TIMEOUT = 30


@dataclass(frozen=True)
class WebCitation:
    title: str
    url: str


@dataclass(frozen=True)
class OnlineObjectResult:
    summary: str
    citations: tuple[WebCitation, ...]
    queries: tuple[str, ...]


class GeminiObjectLookup:
    """Envía un recorte por objetivo y conserva la respuesta y sus fuentes."""

    def __init__(self) -> None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "La busqueda visual requiere configurar la variable GEMINI_API_KEY."
            )
        self._api_key = api_key
        self._executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="kiroshi-web-lookup",
        )
        self._lock = threading.Lock()
        self._future: Future[OnlineObjectResult] | None = None

    def submit(self, frame_bgr: np.ndarray, detection: ObjectDetection) -> bool:
        if detection.category == "person":
            return False

        image_bytes = self._crop_target(frame_bgr, detection.box)
        with self._lock:
            if self._future is not None and not self._future.done():
                return False
            self._future = self._executor.submit(
                self._lookup,
                image_bytes,
                detection.category,
                detection.score,
            )
            return True

    @staticmethod
    def _crop_target(
        frame_bgr: np.ndarray,
        box: tuple[int, int, int, int],
    ) -> bytes:
        frame_height, frame_width = frame_bgr.shape[:2]
        x, y, width, height = box
        padding_x = int(width * 0.12)
        padding_y = int(height * 0.12)
        left = max(0, x - padding_x)
        top = max(0, y - padding_y)
        right = min(frame_width, x + width + padding_x)
        bottom = min(frame_height, y + height + padding_y)
        if right <= left or bottom <= top:
            raise ValueError("No se pudo recortar el objetivo para la busqueda visual.")

        crop = frame_bgr[top:bottom, left:right]
        crop_height, crop_width = crop.shape[:2]
        scale = min(
            1.0,
            MAX_IMAGE_DIMENSION / max(crop_width, crop_height),
        )
        if scale < 1.0:
            crop = cv2.resize(
                crop,
                (max(1, int(crop_width * scale)), max(1, int(crop_height * scale))),
                interpolation=cv2.INTER_AREA,
            )

        try:
            encoded, buffer = cv2.imencode(
                ".jpg",
                crop,
                [cv2.IMWRITE_JPEG_QUALITY, 82],
            )
        except cv2.error as exc:
            raise RuntimeError(f"No se pudo preparar la imagen del objetivo: {exc}") from exc
        if not encoded:
            raise RuntimeError("No se pudo codificar el recorte del objetivo.")
        return buffer.tobytes()

    def _lookup(
        self,
        image_bytes: bytes,
        category: str,
        confidence: float,
    ) -> OnlineObjectResult:
        prompt = (
            "Identifica con cautela el objeto principal mostrado en la imagen. "
            f"El detector local lo clasifico como '{category}' con confianza "
            f"{confidence:.0%}. Usa Google Search para contrastar posibles "
            "marcas, modelos y caracteristicas visibles. No inventes marca ni "
            "modelo: si la imagen no permite distinguirlos, dilo claramente. "
            "Responde en español en un maximo de 55 palabras y no identifiques "
            "personas. Las afirmaciones deben estar respaldadas por las fuentes "
            "que cites."
        )
        request_body = {
            "model": MODEL,
            "store": False,
            "input": [
                {"type": "text", "text": prompt},
                {
                    "type": "image",
                    "data": base64.b64encode(image_bytes).decode("ascii"),
                    "mime_type": "image/jpeg",
                },
            ],
            "tools": [{"type": "google_search"}],
        }
        request = Request(
            API_URL,
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self._api_key,
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(
                f"Gemini respondio HTTP {exc.code}: {detail or exc.reason}"
            ) from exc
        except URLError as exc:
            raise RuntimeError(f"No se pudo consultar Gemini: {exc.reason}") from exc
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Fallo la consulta web de Gemini: {exc}") from exc

        if not isinstance(payload, dict) or not isinstance(payload.get("steps"), list):
            raise RuntimeError("Gemini devolvio una respuesta con formato inesperado.")

        summary_parts: list[str] = []
        citations: list[WebCitation] = []
        queries: list[str] = []
        for step in payload.get("steps", []):
            if not isinstance(step, dict):
                continue
            if step.get("type") == "google_search_call":
                arguments = step.get("arguments", {})
                if isinstance(arguments, dict):
                    search_queries = arguments.get("queries", [])
                    if isinstance(search_queries, list):
                        queries.extend(
                            item for item in search_queries
                            if isinstance(item, str) and item
                        )
                continue
            if step.get("type") != "model_output":
                continue
            content_blocks = step.get("content", [])
            if not isinstance(content_blocks, list):
                continue
            for content in content_blocks:
                if not isinstance(content, dict) or content.get("type") != "text":
                    continue
                raw_text = content.get("text", "")
                text = raw_text.strip() if isinstance(raw_text, str) else ""
                if text:
                    summary_parts.append(text)
                annotations = content.get("annotations", [])
                if not isinstance(annotations, list):
                    continue
                for annotation in annotations:
                    if (
                        not isinstance(annotation, dict)
                        or annotation.get("type") != "url_citation"
                    ):
                        continue
                    url = annotation.get("url")
                    if not isinstance(url, str):
                        continue
                    if url and not any(item.url == url for item in citations):
                        title = annotation.get("title")
                        citations.append(
                            WebCitation(
                                title=title if isinstance(title, str) and title else url,
                                url=url,
                            )
                        )

        summary = " ".join(summary_parts)
        if not summary:
            raise RuntimeError("Gemini no devolvio una respuesta util para el objetivo.")
        if not queries or not citations:
            raise RuntimeError(
                "Gemini no devolvio una busqueda web con fuentes verificables."
            )
        return OnlineObjectResult(summary, tuple(citations[:3]), tuple(queries[:2]))

    def snapshot(
        self,
    ) -> tuple[bool, OnlineObjectResult | None, str | None]:
        with self._lock:
            future = self._future
            if future is None:
                return False, None, None
            if not future.done():
                return True, None, None
            self._future = None

        try:
            return False, future.result(), None
        except (OSError, RuntimeError, ValueError) as exc:
            return False, None, str(exc)

    def close(self) -> None:
        self._executor.shutdown(wait=True, cancel_futures=True)
