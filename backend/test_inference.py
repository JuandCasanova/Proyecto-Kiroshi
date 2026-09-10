import time
import torch

import cv2
from ultralytics import YOLO

print("=== TEST INFERENCIA KIROSHI ===")
print(f"CUDA disponible: {torch.cuda.is_available()}", flush=True)
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}", flush=True)

model = YOLO("yolov8n.pt")
model.to("cuda")
print(f"Modelo en: {model.device}", flush=True)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
print(f"Camara abierta: {cap.isOpened()}", flush=True)

ret, frame = cap.read()
print(f"Frame capturado: {ret}, shape={frame.shape if ret else 'N/A'}", flush=True)

start = time.time()
results = model(frame, conf=0.5, verbose=False, device=0)
infer_ms = (time.time() - start) * 1000
print(f"Inferencia: {infer_ms:.1f} ms", flush=True)

for r in results:
    if r.boxes is not None:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            print(f"  Clase={model.names[cls_id]:12s} conf={conf:.2f}", flush=True)
    else:
        print("  Sin detecciones", flush=True)

cap.release()
print("=== TEST COMPLETADO OK ===", flush=True)