#行为识别接口
from datetime import datetime
import base64
from urllib import request

import face_recognition
from flask import Blueprint, jsonify, current_app

from app.models.employee import Employee,Behavior
from app.exts import db
import pytz
from datetime import timedelta
from flask_login import login_required
import os
import numpy as np
import cv2
from utils.configUtils import recognize_employee_behavior

beh_bp = Blueprint('beh_bp',__name__)

@beh_bp.route('/attendance/dection/', methods=['POST'])
@login_required
def attendance_detection():
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400

        image_data = data['image']
        if ',' in image_data:
            _, encoded = image_data.split(',', 1)
        else:
            encoded = image_data

        try:
            img_bytes = base64.b64decode(encoded)
        except Exception as e:
            return jsonify({'error': 'Invalid base64 data', 'detail': str(e)}), 400

        nparr = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return jsonify({'error': 'Failed to decode image'}), 400

        # 构造保存目录
        save_dir = os.path.join(current_app.root_path, 'local_images')
        os.makedirs(save_dir, exist_ok=True)

        # 用 datetime 生成文件名
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}.jpg"
        img_path = os.path.join(save_dir, filename)

        # 使用 cv2.imencode 绕过 cv2.imwrite 的路径问题
        success, encoded_img = cv2.imencode('.jpg', img)
        if not success:
            # 如果编码也失败，说明 img 可能有问题
            return jsonify({'error': 'Failed to encode image to JPEG'}), 500

        # 将内存中的字节写到磁盘
        try:
            with open(img_path, 'wb') as f:
                f.write(encoded_img.tobytes())
            employees = Employee.query.all()
            if not employees:
                print("未找到任何员工，请先插入员工数据。")
                return jsonify({'error': '未找到任何员工，请先插入员工数据。'}), 500
            behavior = recognize_employee_behavior(emp = random.choice(employees))
            db.session.add(behavior)

            db.session.commit()
        except Exception as e:
            print(e)
            return jsonify({'error': 'Failed to write image file', 'detail': str(e)}), 500

        print(f"[DEBUG] Saved image via imencode, path: {img_path}")

        # 模拟行为检测结果
        result = {
            'behavior': 'normal',
            'confidence': 0.92,
            'timestamp': int(np.floor(cv2.getTickCount() / cv2.getTickFrequency()))
        }

        return jsonify({'status': 'success', 'data': result}), 200

    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'detail': str(e)}), 500

def recognize_face(image_np: np.ndarray) -> int | None:
    # 加载所有已注册员工的编码
    known_encodings = []
    known_ids = []
    for emp in Employee.query.all():
        # 假定 face_encoding 存储为二进制，可用 frombuffer 转换
        enc = np.frombuffer(emp.face_encoding, dtype=np.float64)
        known_encodings.append(enc)
        known_ids.append(emp.id)

    # 检测图像中的人脸并提取编码
    face_locations = face_recognition.face_locations(image_np)
    if not face_locations:
        return None
    face_encodings = face_recognition.face_encodings(image_np, face_locations)

    # 匹配第一个人脸
    for encoding in face_encodings:
        matches = face_recognition.compare_faces(known_encodings, encoding)
        if True in matches:
            best_index = np.argmin(face_recognition.face_distance(known_encodings, encoding))
            return known_ids[best_index]
    return None


@beh_bp.route('/behavior/recognize/', methods=['POST'])
# @login_required
def recognize_behavior():
    """
    员工行为识别接口：
    1. 前端上传 Base64 图像
    2. 人脸识别确定员工 ID
    3. 调用行为模型预测该员工行为
    4. 将结果存库并返回
    """
    tz = pytz.timezone("Asia/Shanghai")
    now = datetime.now(tz)
    # —— 4. 返回给前端 ——
    return jsonify({
        'employeeName': "user01",
        'behavior': "喝水",
        'time': now.strftime('%Y-%m-%d %H:%M:%S')
    }), 200



@beh_bp.route('/behaviorRecognition', methods=['GET'])
def list_behavior_recognitions():
    """
    分页获取行为识别记录，支持按日期区间过滤。
    前端请求参数：
      - page: 当前页码（默认1）
      - size: 每页条数（默认10）
      - startDate: 起始日期，格式 YYYY-MM-DD（可选）
      - endDate: 结束日期，格式 YYYY-MM-DD（可选）
    返回 JSON：
    {
      "items": [
        {
          "id": ...,
          "employeeName": "...",
          "behavior": "...",
          "time": "YYYY-MM-DD HH:mm:ss"
        },
        ...
      ],
      "total": 总记录数
    }
    """
    # 1. 解析分页参数
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
    except ValueError:
        return jsonify({"message": "分页参数必须为整数"}), 400

    # 2. 构建基础查询
    query = Behavior.query

    # 3. 如果提供了日期区间，则按 timestamp 过滤
    start_date = request.args.get('startDate')
    end_date   = request.args.get('endDate')
    if start_date:
        try:
            dt_start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Behavior.timestamp >= dt_start)
        except ValueError:
            return jsonify({"message": f"无法解析的 startDate: {start_date}"}), 400
    if end_date:
        try:
            # 将 endDate 的下一个零点作为上限，不包含当天之后的数据
            dt_end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Behavior.timestamp < dt_end)
        except ValueError:
            return jsonify({"message": f"无法解析的 endDate: {end_date}"}), 400

    # 4. 分页并按时间倒序
    pagination = query.order_by(Behavior.timestamp.desc()) \
                      .paginate(page=page, per_page=size, error_out=False)

    # 5. 构造返回列表
    items = []
    for b in pagination.items:
        items.append({
            "id": b.id,
            "employeeName": b.employee.name,
            "behavior": b.behavior.value,
            "time": b.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })

    # 6. 返回 JSON
    return jsonify({
        "items": items,
        "total": pagination.total
    }), 200