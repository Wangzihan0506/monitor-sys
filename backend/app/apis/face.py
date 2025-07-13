import base64
from io import BytesIO
import numpy as np
from PIL import Image
import face_recognition
from flask import Blueprint, request, jsonify
from app.models.user import User
from app.models.alert import Alert
from app.exts import db
from flask_login import login_user
from datetime import datetime
import json
import os
import cv2

# 创建一个新的蓝图
face_bp = Blueprint("face", __name__)


@face_bp.route('/face_enroll/', methods=['POST'])
def face_enroll():
    """
    人脸信息录入接口
    """
    data = request.get_json()
    if not data or 'username' not in data or 'image' not in data:
        return jsonify(message="缺少用户名或图像数据"), 400

    username = data['username']
    image_data = data['image']

    # 1. 根据 username 查找员工
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify(message="用户不存在"), 404

    # 通过 user 找到关联的 employee
    employee = user.employee
    if not employee:
        return jsonify(message="关联的员工记录不存在"), 404

    # 2. 解码 Base64 图像
    try:
        header, encoded = image_data.split(',', 1)
        img_bytes = base64.b64decode(encoded)
        image = Image.open(BytesIO(img_bytes)).convert('RGB')
        image_np = np.array(image)
    except Exception as e:
        return jsonify(message=f"图像解码失败: {e}"), 400

    # 3. 使用 face_recognition 检测人脸并提取编码
    face_locations = face_recognition.face_locations(image_np)

    if len(face_locations) == 0:
        return jsonify(message="未检测到人脸，请确保面部正对摄像头且光线充足"), 400
    if len(face_locations) > 1:
        return jsonify(message="检测到多张人脸，请确保只有您一人在画面中"), 400

    face_encodings = face_recognition.face_encodings(image_np, face_locations)
    if not face_encodings:
        return jsonify(message="无法提取人脸特征，请更换姿势或环境后重试"), 400

    face_encoding_binary = face_encodings[0].tobytes()

    try:
        user.face_encoding = face_encoding_binary
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(message=f"数据库保存失败: {e}"), 500

    return jsonify(message="人脸录入成功"), 200


@face_bp.route('/face_verify/', methods=['POST'])
def face_verify():
    """
    人脸二次验证接口：匹配失败则记录陌生访客告警
    """
    data = request.get_json()
    if not data or 'username' not in data or 'image' not in data:
        return jsonify(message="缺少用户名或图像数据"), 400

    username = data['username']
    image_data = data['image']

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify(message="用户不存在"), 404

    if not user.face_encoding:
        return jsonify(message="该用户未录入人脸信息，无法进行验证"), 400

    known_face_encoding = np.frombuffer(user.face_encoding, dtype=np.float64)

    try:
        header, encoded = image_data.split(',', 1)
        img_bytes = base64.b64decode(encoded)
        image = Image.open(BytesIO(img_bytes)).convert('RGB')
        image_np = np.array(image)
    except Exception as e:
        return jsonify(message=f"图像解码失败: {e}"), 400

    face_locations = face_recognition.face_locations(image_np)
    if len(face_locations) != 1:
        return jsonify(message="请确保画面中仅有您一人且面部清晰"), 400

    unknown_face_encodings = face_recognition.face_encodings(image_np, face_locations)
    if not unknown_face_encodings:
        return jsonify(message="无法从图像中提取人脸特征"), 400

    unknown_face_encoding = unknown_face_encodings[0]

    matches = face_recognition.compare_faces([known_face_encoding], unknown_face_encoding, tolerance=0.5)

    if matches and matches[0]:
        login_user(user)
        return jsonify({'message': '人脸验证成功'}), 200
    else:
        # 人脸不匹配 - 记录陌生人告警
        timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        save_dir = "static/stranger"
        os.makedirs(save_dir, exist_ok=True)
        filename = f"stranger_{username}_{timestamp_str}.jpg"
        img_path = os.path.join(save_dir, filename)

        # 使用 OpenCV 保存图像
        cv2_img = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        cv2.imwrite(img_path, cv2_img)

        stranger_box = face_locations[0]
        top, right, bottom, left = stranger_box
        box_data = json.dumps([left, top, right - left, bottom - top])

        alert = Alert(
            zone_id="face_recognition",
            message="人脸识别失败：疑似陌生访客",
            person_box=box_data,
            frame_path=img_path,
            timestamp=datetime.utcnow()
        )
        db.session.add(alert)
        db.session.commit()

        return jsonify(message="人脸不匹配，已记录陌生人告警"), 401
