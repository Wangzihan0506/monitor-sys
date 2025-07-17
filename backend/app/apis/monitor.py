from flask import Blueprint, request, jsonify,current_app
from flask_login import login_required
from ultralytics import YOLO
from shapely.geometry import Point, Polygon
from app.models.abnormalEvent import AbnormalEvent
from app.models.alert import Alert
from app.exts import db
import cv2
import numpy as np
import time
import os
import json
from datetime import datetime
import base64
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

monitor_bp = Blueprint("monitor", __name__)

model = YOLO("yolov8n.pt")
danger_zones = {}


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


@monitor_bp.route('/api/detect_base64', methods=['POST'])
def detect_base64():
    data = request.get_json()
    img_base64 = data.get("image")
    if not img_base64:
        return jsonify({"code": 1, "msg": "图像数据缺失"}), 400

    try:
        # 解码图像
        img_data = base64.b64decode(img_base64)
        img_np = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
    except Exception as e:
        return jsonify({"code": 2, "msg": f"图像解码失败: {str(e)}"}), 400

    alerts = []
    persons = detect_persons(frame)
    for person in persons:
        for zone_id, zone in danger_zones.items():
            result = check_danger_zone(person, zone)
            if result:
                # 保存截图
                timestamp_str = time.strftime("%Y%m%d_%H%M%S")
                save_dir = "static/frames"
                os.makedirs(save_dir, exist_ok=True)
                filename = f"alert_{zone_id}_{timestamp_str}.jpg"
                img_path = os.path.join(save_dir, filename)
                cv2.imwrite(img_path, frame)

                # 保存数据库记录
                alert = Alert(
                    zone_id=zone_id,
                    message=result,
                    person_box=json.dumps(person),
                    frame_path=img_path,
                    timestamp=datetime.utcnow()
                )
                db.session.add(alert)

                alerts.append({
                    "zone_id": zone_id,
                    "message": result,
                    "person_box": person,
                    "frame_path": img_path
                })

    if alerts:
        db.session.commit()

    return jsonify({"code": 0, "alerts": alerts})

# 【新增接口】用于接收前端发送的常规告警（进入/停留危险区域）
@monitor_bp.route('/api/alert_normal', methods=['POST'])
def receive_normal_alert():
    data = request.get_json()
    zone_id = data.get('zone_id', 'unknown_zone') # 前端可能传递固定的zone_id，或者后续动态生成
    message = data.get('message')
    person_box_str = data.get('person_box') # JSON 字符串
    frame_base64 = data.get('frame_image') # Base64 图像数据

    if not message or not person_box_str or not frame_base64:
        logging.error(f"接收常规告警失败: 缺少必要参数. Data: {data}")
        return jsonify({"code": 1, "msg": "缺少必要参数"}), 400

    try:
        person_box = json.loads(person_box_str)
    except json.JSONDecodeError:
        logging.error(f"接收常规告警失败: person_box解码失败. person_box_str: {person_box_str}")
        return jsonify({"code": 1, "msg": "person_box格式错误"}), 400

    # 保存截图
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f") # 增加微秒防止重复

    fs_save_dir_base = current_app.static_folder
    fs_save_dir_alert = os.path.join(fs_save_dir_base, "alert_frames")

    os.makedirs(fs_save_dir_alert, exist_ok=True)
    filename = f"normal_alert_{timestamp_str}.jpg"
    fs_img_path = os.path.join(fs_save_dir_alert, filename)  # 文件系统路径
    db_frame_path = os.path.join(current_app.static_url_path, "alert_frames", filename).replace('\\', '/')

    try:
        img_data = base64.b64decode(frame_base64)
        with open(fs_img_path, 'wb') as f:
            f.write(img_data)
        logging.info(f"常规告警截图已保存到文件系统: {fs_img_path}")
    except Exception as e:
        logging.error(f"保存常规告警截图失败: {e}", exc_info=True)
        return jsonify({"code": 2, "msg": f"图片保存失败: {str(e)}"}), 500

    # 保存到数据库
    try:
        alert = Alert(
            zone_id=zone_id,
            message=message,
            person_box=person_box_str, # 存储JSON字符串
            frame_path=db_frame_path,
            timestamp=datetime.utcnow()
        )
        db.session.add(alert)
        db.session.commit()
        logging.info(f"常规告警已写入数据库: {message}")
        return jsonify({"code": 0, "msg": "常规告警接收成功并已写入数据库"})
    except Exception as e:
        db.session.rollback()
        logging.error(f"常规告警写入数据库失败: {e}", exc_info=True)
        return jsonify({"code": 3, "msg": f"数据库写入失败: {str(e)}"}), 500


# 【新增接口】用于接收前端发送的异常行为告警（例如陌生人）
@monitor_bp.route('/api/alert_abnormal', methods=['POST'])
@login_required
def receive_abnormal_alert():
    data = request.get_json()
    label = data.get('label') # 例如 '陌生人'
    box_str = data.get('box') # JSON 字符串
    frame_base64 = data.get('frame_image') # Base64 图像数据
    message = data.get('message', '未知异常行为')

    if not label or not box_str or not frame_base64:
        logging.error(f"接收异常告警失败: 缺少必要参数. Data: {data}")
        return jsonify({"code": 1, "msg": "缺少必要参数"}), 400

    try:
        box = json.loads(box_str)
    except json.JSONDecodeError:
        logging.error(f"接收异常告警失败: box解码失败. box_str: {box_str}")
        return jsonify({"code": 1, "msg": "box格式错误"}), 400

    # 保存截图
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    fs_save_dir_base = current_app.static_folder
    fs_save_dir_abnormal = os.path.join(fs_save_dir_base, "abnormal_frames")

    os.makedirs(fs_save_dir_abnormal, exist_ok=True)
    filename = f"abnormal_event_{label}_{timestamp_str}.jpg"
    fs_img_path = os.path.join(fs_save_dir_abnormal, filename)  # 文件系统路径

    db_frame_path = os.path.join(current_app.static_url_path, "abnormal_frames", filename).replace('\\', '/')

    try:
        img_data = base64.b64decode(frame_base64)
        with open(fs_img_path, 'wb') as f:
            f.write(img_data)
        logging.info(f"异常告警截图已保存到文件系统: {fs_img_path}")
    except Exception as e:
        logging.error(f"保存异常告警截图失败: {e}", exc_info=True)
        return jsonify({"code": 2, "msg": f"图片保存失败: {str(e)}"}), 500

    # 保存到数据库
    try:
        abnormal_event = AbnormalEvent(
            label=label,
            box=box_str, # 存储JSON字符串
            frame_path=db_frame_path,
            timestamp=datetime.utcnow(),
            # 这里的message字段，你可以选择是否将其存储到db.models.alert的message字段
            # 如果AbnormalEvent模型没有message字段，你需要调整，或者将message合并到label中
            # 例如：message=f"{label}: {message}"
        )
        db.session.add(abnormal_event)
        db.session.commit()
        logging.info(f"异常告警已写入数据库: {label}")
        return jsonify({"code": 0, "msg": "异常告警接收成功并已写入数据库"})
    except Exception as e:
        db.session.rollback()
        logging.error(f"异常告警写入数据库失败: {e}", exc_info=True)
        return jsonify({"code": 3, "msg": f"数据库写入失败: {str(e)}"}), 500