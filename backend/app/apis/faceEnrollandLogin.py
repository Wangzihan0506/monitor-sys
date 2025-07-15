import base64
import pickle
import logging
import uuid
import os
from flask import Blueprint, request, jsonify, current_app
from app.models.user import User
from app.exts import db
from flask_login import login_user
from deepface import DeepFace
from config import BASE_DIR

face_bp = Blueprint("face_bp", __name__)


MODEL_NAME = "Facenet512"
# 'opencv' 通常比 'mtcnn' 快得多
DETECTOR_BACKEND = "retinaface"
# 使用 'cosine' 距离进行比对
DISTANCE_METRIC = "cosine"

TEMP_FOLDER = os.path.join(BASE_DIR, 'temp_images')
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)

# --- 人脸录入 API ---
@face_bp.route('/face_enroll/', methods=['POST'])
def face_enroll():
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
        # 解码并保存为临时文件
        if ',' in image_data_base64:
            header, encoded = image_data_base64.split(',', 1)
        else:
            encoded = image_data_base64

        img_bytes = base64.b64decode(encoded)
        temp_image_path = os.path.join(TEMP_FOLDER, f"{uuid.uuid4()}.jpg")
        with open(temp_image_path, 'wb') as f:
            f.write(img_bytes)

        # 提取特征向量
        embedding_objs = DeepFace.represent(
            img_path=temp_image_path,
            model_name=MODEL_NAME,
            detector_backend=DETECTOR_BACKEND,
            enforce_detection=True
        )
        embedding = embedding_objs[0]['embedding']
        face_encoding_binary = pickle.dumps(embedding)

        # 更新数据库
        user.face_encoding = face_encoding_binary
        db.session.commit()

        logging.info(f"用户 {username} 的人脸信息已成功录入/更新 (模型: {MODEL_NAME})。")
        return jsonify(success=True, message="人脸录入成功！")

    except ValueError as e:
        # 更具体的错误处理
        if "Face could not be detected" in str(e) or "No face detected" in str(e):
            return jsonify(success=False, message="未检测到清晰人脸，请调整姿势或光线后重试。"), 400
        else:
            current_app.logger.error(f"为用户 {username} 提取特征失败: {e}", exc_info=True)
            return jsonify(success=False, message=f"特征提取失败，可能是图像问题。"), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"为用户 {username} 录入人脸时发生未知错误: {e}", exc_info=True)
        return jsonify(success=False, message="服务器内部错误，录入失败。"), 500
    finally:
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)


# --- 人脸二次验证 API ---
@face_bp.route('/face_verify/', methods=['POST'])
def face_verify():
    data = request.get_json()
    if not data or 'username' not in data or 'image' not in data:
        return jsonify(success=False, message="缺少用户名或图像数据"), 400

    username = data['username']

    user = User.query.filter_by(username=username).first()
    if not user or not user.face_encoding:
        return jsonify(success=False, message="该用户未录入人脸信息，请先录入。"), 400

    known_face_encoding = pickle.loads(user.face_encoding)
    image_data_base64 = data['image']
    temp_image_path = None

    try:
        if ',' in image_data_base64:
            header, encoded = image_data_base64.split(',', 1)
        else:
            encoded = image_data_base64

        img_bytes = base64.b64decode(encoded)
        temp_image_path = os.path.join(TEMP_FOLDER, f"{uuid.uuid4()}.jpg")
        with open(temp_image_path, 'wb') as f:
            f.write(img_bytes)

        # 【核心优化】使用 DeepFace.verify 进行比对
        # 它会自动处理特征提取和比对
        result = DeepFace.verify(
            img1_path=temp_image_path,  # 待验证的图片
            img2_path=known_face_encoding,  # 已存储的特征向量，可以直接传入
            model_name=MODEL_NAME,
            detector_backend=DETECTOR_BACKEND,
            distance_metric=DISTANCE_METRIC,
            enforce_detection=True  # 验证时也必须检测到人脸
            # threshold=THRESHOLD, # 如果需要自定义阈值，取消这行注释
        )

        current_app.logger.info(f"用户 {username} 人脸验证结果: {result}")

        # 根据比对结果返回响应
        if result.get("verified", False):
            login_user(user)  # 验证成功后，维持登录状态
            return jsonify(success=True, message="人脸验证成功", distance=result.get("distance")), 200
        else:
            return jsonify(success=False, message="人脸不匹配，请重试", distance=result.get("distance")), 401

    except ValueError as e:
        if "Face could not be detected" in str(e) or "No face detected" in str(e):
            return jsonify(success=False, message="验证失败：未检测到清晰人脸。"), 400
        else:
            current_app.logger.error(f"验证用户 {username} 时发生值错误: {e}", exc_info=True)
            return jsonify(success=False, message="验证失败，可能是图像质量问题。"), 500
    except Exception as e:
        current_app.logger.error(f"验证用户 {username} 时发生未知错误: {e}", exc_info=True)
        return jsonify(success=False, message="服务器内部错误，验证失败。"), 500
    finally:
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)