import base64
from io import BytesIO
import numpy as np
from PIL import Image
import pickle
import logging
import uuid
import os

from flask import Blueprint, request, jsonify, current_app
from app.models.user import User
from app.exts import db
from flask_login import login_user

# 导入 deepface 和我们需要的配置
from deepface import DeepFace
from config import BASE_DIR

# 创建蓝图
face_bp = Blueprint("face_bp", __name__)  # 建议蓝图名和文件名一致

# --- 与实时识别部分共享的配置 ---
MODEL_NAME = "VGG-Face"
DETECTOR_BACKEND = "mtcnn"

# 创建可控的临时文件夹
TEMP_FOLDER = os.path.join(BASE_DIR, 'temp_images')
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)


# --- 人脸录入 API (使用 DeepFace 重写) ---
@face_bp.route('/face_enroll/', methods=['POST'])
def face_enroll():
    """
    人脸信息录入接口 (使用 DeepFace)
    """
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
        # 1. 解码 Base64 并保存为临时文件 (这是最稳妥的做法)
        header, encoded = image_data_base64.split(',', 1)
        img_bytes = base64.b64decode(encoded)

        temp_image_path = os.path.join(TEMP_FOLDER, f"{uuid.uuid4()}.jpg")
        with open(temp_image_path, 'wb') as f:
            f.write(img_bytes)

        # 2. 使用 DeepFace 提取特征向量
        embedding_objs = DeepFace.represent(
            img_path=temp_image_path,
            model_name=MODEL_NAME,  # 必须和识别时用的模型一样
            detector_backend=DETECTOR_BACKEND,  # 必须和识别时用的检测器一样
            enforce_detection=True  # 录入时必须检测到人脸
        )

        # 这是一个包含了 N 个元素的列表，我们只需要特征向量
        embedding = embedding_objs[0]['embedding']

        # 3. 使用 pickle 将特征向量（一个Python列表）序列化为二进制数据
        face_encoding_binary = pickle.dumps(embedding)

        # 4. 更新用户记录并保存
        user.face_encoding = face_encoding_binary
        db.session.commit()

        logging.info(f"用户 {user.username} (ID: {user.id}) 的人脸信息已成功录入/更新。")
        return jsonify(success=True, message=f"人脸录入成功！")

    except ValueError as e:
        if "Face could not be detected" in str(e):
            return jsonify(success=False, message="未检测到清晰人脸，请重试"), 400
        else:
            current_app.logger.error(f"为用户 {user.id} 注册人脸时提取特征失败: {e}", exc_info=True)
            return jsonify(success=False, message=f"特征提取失败: {e}"), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"为用户 {user.id} 注册人脸时发生未知错误: {e}", exc_info=True)
        return jsonify(success=False, message="服务器内部错误，录入人脸失败"), 500
    finally:
        # 5. 清理临时文件
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)


# --- 人脸二次验证 API (使用 DeepFace 重写) ---
# 注意：这个接口现在和你的实时识别逻辑有些重叠，但我们还是重写它以保持一致性
@face_bp.route('/face_verify/', methods=['POST'])
def face_verify():
    """
    人脸二次验证接口 (使用 DeepFace)
    """
    data = request.get_json()
    if not data or 'username' not in data or 'image' not in data:
        return jsonify(success=False, message="缺少用户名或图像数据"), 400

    username = data['username']

    # 1. 查找用户并获取已存储的人脸编码
    user = User.query.filter_by(username=username).first()
    if not user or not user.face_encoding:
        return jsonify(success=False, message="该用户未录入人脸信息"), 400

    # 使用 pickle 反序列化出已知的特征向量
    known_face_encoding = pickle.loads(user.face_encoding)

    # 2. 处理上传的图片并提取特征
    image_data_base64 = data['image']
    temp_image_path = None
    try:
        header, encoded = image_data_base64.split(',', 1)
        img_bytes = base64.b64decode(encoded)

        temp_image_path = os.path.join(TEMP_FOLDER, f"{uuid.uuid4()}.jpg")
        with open(temp_image_path, 'wb') as f:
            f.write(img_bytes)

        # 使用 DeepFace.verify 函数，它专门用于 1:1 比对
        # 它会自动完成提取特征和比对的全过程
        result = DeepFace.verify(
            img1_path=temp_image_path,
            img2_path=known_face_encoding,  # 可以直接传入特征向量
            model_name=MODEL_NAME,
            detector_backend=DETECTOR_BACKEND
        )

        # 3. 根据比对结果返回响应
        if result["verified"]:
            login_user(user)
            return jsonify(success=True, message="人脸验证成功"), 200
        else:
            return jsonify(success=False, message="人脸不匹配"), 401

    except Exception as e:
        current_app.logger.error(f"验证用户 {user.id} 时发生错误: {e}", exc_info=True)
        return jsonify(success=False, message="验证过程中发生服务器错误"), 500
    finally:
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)