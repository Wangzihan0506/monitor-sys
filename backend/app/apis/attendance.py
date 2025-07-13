from flask import Blueprint, jsonify
from ultralytics import YOLO
from shapely.geometry import Point, Polygon
from app.models.alert import Alert
from app.exts import db
import cv2
import numpy as np
import time
import os
import json
from datetime import datetime
import threading

monitor_bp = Blueprint("monitor", __name__)

model = YOLO("yolov8n.pt")
danger_zones = {}
detection_active = False


def detect_persons(frame):
    results = model(frame)[0]
    person_boxes = []
    for box in results.boxes:
        cls_id = int(box.cls[0])
        if model.names[cls_id] == 'person':
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            w, h = x2 - x1, y2 - y1
            person_boxes.append((x1, y1, w, h))
    return person_boxes


def check_danger_zone(person_box, danger_zone):
    x, y, w, h = person_box
    center = (x + w // 2, y + h // 2)
    point = Point(center)
    polygon = Polygon(danger_zone['polygon'])

    if polygon.contains(point):
        return "进入危险区域"
    elif point.distance(polygon) <= danger_zone['safe_distance']:
        return "接近危险边界"
    return None


def monitor_camera():
    cap = cv2.VideoCapture(0)
    while detection_active:
        ret, frame = cap.read()
        if not ret:
            continue

        persons = detect_persons(frame)
        for person in persons:
            for zone_id, zone in danger_zones.items():
                result = check_danger_zone(person, zone)
                if result:
                    timestamp_str = time.strftime("%Y%m%d_%H%M%S")
                    save_dir = "static/frames"
                    os.makedirs(save_dir, exist_ok=True)
                    filename = f"alert_{zone_id}_{timestamp_str}.jpg"
                    img_path = os.path.join(save_dir, filename)
                    cv2.imwrite(img_path, frame)

                    alert = Alert(
                        zone_id=zone_id,
                        message=result,
                        person_box=json.dumps(person),
                        frame_path=img_path,
                        timestamp=datetime.utcnow()
                    )
                    db.session.add(alert)
                    db.session.commit()

        time.sleep(0.5)
    cap.release()


@monitor_bp.route('/api/set_danger_zone', methods=['POST'])
def set_danger_zone():
    data = request.json
    zone_id = data.get('zone_id')
    polygon = data.get('polygon')
    safe_distance = data.get('safe_distance', 50)
    max_stay = data.get('max_stay', 3)

    if not zone_id or not polygon:
        return jsonify({'code': 1, 'msg': 'zone_id 和 polygon 必填'}), 400

    danger_zones[zone_id] = {
        'polygon': polygon,
        'safe_distance': safe_distance,
        'max_stay': max_stay
    }
    return jsonify({'code': 0, 'msg': '区域设置成功'})


@monitor_bp.route('/api/start_monitor', methods=['POST'])
def start_monitor():
    global detection_active
    if detection_active:
        return jsonify({"code": 1, "msg": "检测已在运行"})

    detection_active = True
    thread = threading.Thread(target=monitor_camera)
    thread.start()
    return jsonify({"code": 0, "msg": "摄像头检测已启动"})


@monitor_bp.route('/api/stop_monitor', methods=['POST'])
def stop_monitor():
    global detection_active
    detection_active = False
    return jsonify({"code": 0, "msg": "检测已停止"})
