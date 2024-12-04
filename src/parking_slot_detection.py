import os 
import cv2
import pickle 
import pandas as pd
from ultralytics import YOLO
import cvzone
import websockets
import asyncio
import json
import time
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

WEBSOCKET_HOST = os.getenv("WEBSOCKET_HOST")
WEBSOCKET_PORT = os.getenv("WEBSOCKET_PORT")
CAMERA_STREAM_URL = os.getenv("CAMERA_STREAM_URL")

if not WEBSOCKET_HOST or not WEBSOCKET_PORT:
    raise EnvironmentError("Either WEBSOCKET_HOST or WEBSOCKET_PORT environment variable is not set!")

if not CAMERA_STREAM_URL:
    raise EnvironmentError("CAMERA_STREAM_URL environment variable is not set!")

WEBSOCKET_URL = f"ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}/update_slot_status"

PROCESS_INTERVAL = 4.0  # YOLO processing interval in seconds

async def emit_socket_event(reason, filled_slots, free_slots, current_time=0):
    async with websockets.connect(WEBSOCKET_URL) as websocket:
        data = {
            "filled_slots": filled_slots,
            "free_slots": free_slots,
            "timestamp": int(time.time()),
        }
        await websocket.send(json.dumps(data))
        print(f"Sent data: {data}")

try:
    with open("parkease", "rb") as f:
        data = pickle.load(f)
        polylines, area_names = data["polylines"], data["area_names"]
except FileNotFoundError:
    print("Error: 'parkease' file not found. Run 'mark_slots.py' first.")
    exit(1)

try:
    with open("coco.txt", "r") as my_file:
        class_list = my_file.read().split("\n")
    model = YOLO("yolo11m.pt")
except Exception as e:
    print(f"Error loading YOLO model or class list: {e}")
    exit(1)

cap = cv2.VideoCapture(CAMERA_STREAM_URL)

if not cap.isOpened():
    print("Failed to open video capture.")
    exit(1)

last_emit_time = time.time()
last_sent_slots = []
last_yolo_time = 0

async def main():
    global last_emit_time, last_sent_slots, last_yolo_time
    while True:
        try:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("Frame is None.")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            frame = cv2.resize(frame, (1020, 500))
            current_time = time.time()

            # Run YOLO analysis only after the specified interval
            if current_time - last_yolo_time >= PROCESS_INTERVAL:
                last_yolo_time = current_time

                results = model.predict(frame,conf=0.7)
                detections = results[0].boxes.data
                px = pd.DataFrame(detections).astype("float")

                detected_cars = []
                for _, row in px.iterrows():
                    x1, y1, x2, y2, d = int(row[0]), int(row[1]), int(row[2]), int(row[3]), int(row[5])

                    c = class_list[d]
                    cx = int(x1 + x2) // 2
                    cy = int(y1 + y2) // 2

                    if "car" in c:
                        detected_cars.append([cx, cy])

                total_slots = 0
                filled_slots = []
                free_slots = []

                for i, polyline in enumerate(polylines):
                    total_slots += 1
                    for cx, cy in detected_cars:
                        result = cv2.pointPolygonTest(polyline, (cx, cy), False)
                        if result >= 0:
                            filled_slots.append(area_names[i])

                free_slots = [area_name for area_name in area_names if area_name not in filled_slots]

                # Update slot status if changed
                if filled_slots != last_sent_slots:
                    await emit_socket_event("update", filled_slots, free_slots)
                    last_sent_slots = filled_slots
                    last_emit_time = current_time

            # Visualization
            for i, polyline in enumerate(polylines):
                color = (0, 0, 255) if area_names[i] in last_sent_slots else (0, 255, 0)
                cv2.polylines(frame, [polyline], True, color, 2)
                cvzone.putTextRect(frame, f"{area_names[i]}", tuple(polyline[0]), 1, 1)

            filled_text = f"Filled Slots: [{', '.join(last_sent_slots)}]" if last_sent_slots else "Filled Slots: [None]"
            cvzone.putTextRect(frame, filled_text, (50, 100), 2, 2, offset=10, colorB=(4, 217, 252))

            cvzone.putTextRect(frame, f"Free Slots: {len(area_names) - len(last_sent_slots)}", (50, 50), 2, 2, offset=10, colorB=(4, 217, 252))

            cv2.imwrite("Real_Time_Stream.jpeg", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

        except Exception as e:
            print(f"Error processing stream: {e}")
            break

asyncio.run(main())

cap.release()
cv2.destroyAllWindows()
