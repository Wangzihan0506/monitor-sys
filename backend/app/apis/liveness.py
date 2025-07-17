from flask import Blueprint, request, jsonify
import cv2
import numpy as np
import base64
import os

liveness_bp = Blueprint('liveness', __name__)

def decode_base64_image(data):
    header, encoded = data.split(',', 1)
    img_bytes = base64.b64decode(encoded)
    img_array = np.frombuffer(img_bytes, np.uint8)
    return cv2.imdecode(img_array, cv2.IMREAD_COLOR)

def detect_blink(frames):
    # 加载人脸和眼睛检测模型
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    face_cascade = cv2.CascadeClassifier(os.path.join(base_dir, '../../cv2_data/haarcascade_frontalface_default.xml'))
    eye_cascade = cv2.CascadeClassifier(os.path.join(base_dir, '../../cv2_data/haarcascade_eye.xml'))
    eye_counts = []
    for frame_b64 in frames:
        img = decode_base64_image(frame_b64)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            roi_gray = gray[y:y+h, x:x+w]
            eyes = eye_cascade.detectMultiScale(roi_gray)
            eye_counts.append(len(eyes))
    # 检查眼睛数量有明显变化（如2->0->2，表示眨眼）
    for i in range(1, len(eye_counts)-1):
        if eye_counts[i-1] >= 2 and eye_counts[i] == 0 and eye_counts[i+1] >= 2:
            return True
    return False

@liveness_bp.route('/api/face/liveness_check_and_recognize', methods=['POST'])
def liveness_check_and_recognize():
    """
    先做眨眼活体检测，活体通过后再做人脸识别
    """
    data = request.get_json()
    frames = data.get('frames', [])
    if not frames:
        return jsonify({'success': False, 'msg': 'No frames received'})
    is_live = detect_blink(frames)
    if not is_live:
        return jsonify({'success': False, 'msg': '未检测到眨眼动作，请勿使用照片/视频/AI换脸'})
    # 活体通过，取最后一帧做人脸识别
    last_frame = frames[-1]
    # 这里假设你已有人脸识别函数 recognize_face_from_image(img)
    try:
        from .face_recognition import recognize_face_from_image
    except ImportError:
        return jsonify({'success': False, 'msg': '人脸识别函数未找到'})
    img = decode_base64_image(last_frame)
    user_info = recognize_face_from_image(img)
    if user_info:
        return jsonify({'success': True, 'msg': '活体检测和人脸识别通过', 'user': user_info})
    else:
        return jsonify({'success': False, 'msg': '未识别到用户'})