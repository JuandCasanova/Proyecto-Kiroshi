import asyncio
import json
import sys
import time
import websockets


async def test_detection():
    uri = "ws://localhost:8000/ws/detect"
    async with websockets.connect(uri) as ws:
        print("Conectado. Esperando frames...")
        received = 0
        total_fps = 0.0
        start = time.time()

        for _ in range(15):
            raw = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(raw)
            received += 1
            total_fps += data.get("fps", 0)
            if data["detections"]:
                for d in data["detections"]:
                    print(
                        f"  [{d['id']}] {d['class']:12s} conf={d['confidence']:.2f} "
                        f"center=({d['center']['x']}, {d['center']['y']})"
                    )
            else:
                print(f"  ({received}) sin detecciones | fps={data['fps']}")

        elapsed = time.time() - start
        avg_fps = total_fps / max(received, 1)
        frame_size_kb = len(data["frame"]) * 0.75 / 1024

        print(f"\n=== RESUMEN ===")
        print(f"Frames recibidos: {received} en {elapsed:.1f}s")
        print(f"FPS promedio backend: {avg_fps:.1f}")
        print(f"Tamaño aprox frame JPEG: {frame_size_kb:.0f} KB")

        if data["detections"]:
            print("Deteccion de objetos: FUNCIONANDO")
        print("Pipeline completo: OK")


asyncio.run(test_detection())