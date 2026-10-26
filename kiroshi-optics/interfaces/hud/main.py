"""Punto de entrada ejecutable para la interfaz HUD."""

import argparse
import sys


def parse_camera_source(value: str) -> int | str:
    """Interpreta numeros como indices de camara y otros valores como URLs."""
    try:
        return int(value)
    except ValueError:
        return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Kiroshi Optics webcam HUD")
    parser.add_argument(
        "--camera",
        default="0",
        type=parse_camera_source,
        metavar="INDEX_OR_URL",
        help=(
            "indice de camara local (por defecto: 0) o URL de streaming "
            "de la camara del telefono (por ejemplo, http://192.168.1.50:8080/video)"
        ),
    )
    args = parser.parse_args()

    try:
        from interfaces.hud.hud import KiroshiHUD

        KiroshiHUD(camera_source=args.camera).run()
    except (ImportError, OSError, RuntimeError) as exc:
        print(f"Kiroshi HUD: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
