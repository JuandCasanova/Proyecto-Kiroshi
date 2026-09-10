import time
import torch
import cv2
from ultralytics import YOLO

model = YOLO("yolov8n.pt")
model.to("cuda")

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

cap.read()
print("Warmup inference...", flush=True)
model(cap.read()[1], conf=0.5, verbose=False, device=0)
print("Warmup done", flush=True)

times = []
for i in range(10):
    ret, frame = cap.read()
    start = time.time()
    results = model(frame, conf=0.5, verbose=False, device=0)
    elapsed = (time.time() - start) * 1000
    times.append(elapsed)
    print(f"Frame {i+1}: {elapsed:.1f} ms | fps={1000/elapsed:.1f}", flush=True)

avg = sum(times) / len(times)
print(f"\nPromedio: {avg:.1f} ms | fps max posible: {1000/avg:.1f}", flush=True)
cap.release()