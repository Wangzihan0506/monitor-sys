# backend/app/apis/faceEnrollandLogin.py
import base64
from datetime import datetime, timedelta
import pickle
import logging
import uuid
import os
import jwt
from flask import Blueprint, request, jsonify, current_app
from app.models.user import User
from app.exts import db
from flask_login import login_user, current_user as login_current_user  # 重命名以避免与 flask.current_app 混淆
from deepface import DeepFace
from config import BASE_DIR

face_bp = Blueprint("face_bp", __name__)

# 1. 删除文件级别的硬编码常量
# MODEL_NAME = "Facenet512"
# DETECTOR_BACKEND = "retinaface"
# DISTANCE_METRIC = "cosine"

TEMP_FOLDER = os.path.join(BASE_DIR, 'temp_images')
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)


@face_bp.route('/face_enroll/', methods=['POST'])
def face_enroll():
    # 2. 在函数内部从配置中获取常量
    model_name = 'SFace'
    detector_backend = current_app.config['FACE_DETECTOR_BACKEND']

    data = request.get_json()
    if not data or 'username' not in data or 'image' not in data:
        return jsonify(success=False, message="缺少用户名或图像数据"), 400

    username = data['username']
    image_data_base64 = data['image']

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify(success=False, message="用户不存在"), 404

    temp_image_path = None
    try:
        # ... (解码和保存文件的逻辑不变) ...
        if ',' in image_data_base64:
            _, encoded = image_data_base64.split(',', 1)
        else:
            encoded = image_data_base64
        img_bytes = base64.b64decode(encoded)
        temp_image_path = os.path.join(TEMP_FOLDER, f"{uuid.uuid4()}.jpg")
        with open(temp_image_path, 'wb') as f:
            f.write(img_bytes)

        # 使用从配置中获取的参数
        embedding_objs = DeepFace.represent(
            img_path=temp_image_path,
            model_name=model_name,
            detector_backend=detector_backend,
            enforce_detection=True
        )
        # ... (后续逻辑不变) ...
        embedding = embedding_objs[0]['embedding']
        face_encoding_binary = pickle.dumps(embedding)
        user.face_encoding = face_encoding_binary
        db.session.commit()
        logging.info(f"用户 {username} 的人脸信息已成功录入/更新 (模型: {model_name})。")
        return jsonify(code=0,msg="人脸录入成功！")

    except ValueError as e:
        # ... (错误处理逻辑不变) ...
        if "Face could not be detected" in str(e):
            return jsonify(code=1,msg="未检测到清晰人脸...")
        else:
            return jsonify(code=-1,msg="特征提取失败...")
    except Exception as e:
        # ... (错误处理逻辑不变) ...
        return jsonify(code=-1,msg="服务器内部错误...")
    finally:
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)

def generate_token(user_id):
    payload = {
        'exp': datetime.utcnow() + timedelta(days=1),
        'iat': datetime.utcnow(),
         'sub': str(user_id)
    }
    secret = current_app.config['SECRET_KEY']
    print(f"【Token 生成】使用的 SECRET_KEY 是: '{secret}'")
    return jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )

@face_bp.route('/face_verify/', methods=['POST'])
def face_verify():
    current_app.logger.info("--- 开始人脸验证请求 ---")
    # 2. 在函数内部从配置中获取常量
    model_name = 'SFace'
    detector_backend = current_app.config['FACE_DETECTOR_BACKEND']
    distance_metric = current_app.config['DISTANCE_METRIC']
    # 注意: DeepFace.verify 有自己的默认阈值，如果想覆盖，需要在这里获取并传入
    # threshold = current_app.config['FACE_VERIFY_THRESHOLD']

    data = request.get_json()
    if not data or 'username' not in data or 'image' not in data:
        return jsonify(...), 400
    current_app.logger.info("1. JSON 数据获取成功。")
    # ... (获取 username, user, image 等逻辑不变) ...
    username = data['username']
    user = User.query.filter_by(username=username).first()
    if not user or not user.face_encoding:
        return jsonify(success=False, message="该用户未录入人脸信息..."), 400
    known_face_encoding = pickle.loads(user.face_encoding)
    image_data_base64 = data['image']
    temp_image_path = None

    try:
        # ... (解码和保存文件的逻辑不变) ...
        if ',' in image_data_base64:
            _, encoded = image_data_base64.split(',', 1)
        else:
            encoded = image_data_base64
        img_bytes = base64.b64decode(encoded)
        current_app.logger.info("2. Base64 解码成功。")
        temp_image_path = os.path.join(TEMP_FOLDER, f"{uuid.uuid4()}.jpg")
        with open(temp_image_path, 'wb') as f:
            f.write(img_bytes)

        current_app.logger.info("4. 准备调用 DeepFace.verify...")
        # 使用从配置中获取的参数
        result = DeepFace.verify(
            img1_path=temp_image_path,
            img2_path=known_face_encoding,
            model_name=model_name,
            detector_backend=detector_backend,
            distance_metric=distance_metric,
            enforce_detection=True
            # threshold=threshold, # 如果需要自定义阈值
        )

        current_app.logger.info(f"用户 {username} 人脸验证结果: {result}")
        if result.get("verified", True):
            #login_user(user)
            token = generate_token(user.id)
            return jsonify({'code': 0, 'msg': '验证成功', 'verified': True, 'token': token,  'username': user.username})
        else:
            return jsonify({'code': 1, 'msg': '人脸不匹配，请重试', 'verified': False})

    except ValueError as e:
        # ... (错误处理逻辑不变) ...
        return jsonify(success=False, message="验证失败..."), 400
    except Exception as e:
        # ... (错误处理逻辑不变) ...
        current_app.logger.info(f"人脸验证时发生异常: {e}")
        return jsonify({'code': -1, 'msg': '无法在图片中检测到人脸，请调整姿势重试'})
    finally:
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)