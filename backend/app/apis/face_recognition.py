# backend/app/apis/face_recognition.py

import numpy as np
import pickle
import logging
import os
import uuid
from flask import Blueprint, request, jsonify, current_app  # 1. 导入 current_app
from deepface import DeepFace
from flask import g
from app.decorators import token_required
from config import BASE_DIR
from app.models.user import User

face_recognition_bp = Blueprint('face_recognition_bp', __name__)

# 2. 删除文件级别的硬编码常量
# MODEL_NAME = "Facenet512"
# THRESHOLD = 0.80

TEMP_FOLDER = os.path.join(BASE_DIR, 'temp_images')
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)


def find_cosine_distance(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
        return 1.0
    return 1 - np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


@face_recognition_bp.route('/recognize_batch', methods=['POST'])
@token_required
def recognize_batch():
    # 3. 在函数内部从配置中获取常量
    model_name = current_app.config['FACE_MODEL_NAME']
    detector_backend = current_app.config['FACE_DETECTOR_BACKEND']
    threshold = current_app.config['FACE_VERIFY_THRESHOLD']

    face_files = request.files.getlist('faces')
    if not face_files: return jsonify(results=[])

    users_with_faces = User.query.filter(User.face_encoding.isnot(None)).all()
    logging.info(f"从数据库中加载到 {len(users_with_faces)} 条已录入人脸的用户记录。")

    known_faces = []
    for user in users_with_faces:
        try:
            stored_embedding = pickle.loads(user.face_encoding)
            known_faces.append({'name': user.username, 'encoding': stored_embedding})
        except Exception:
            continue

    if not known_faces:
        logging.warning("数据库中没有任何有效的人脸编码可供比对！")

    results = []
    for i, file in enumerate(face_files):
        temp_image_path = None
        try:
            temp_image_path = os.path.join(TEMP_FOLDER, f"{uuid.uuid4()}.jpg")
            file.save(temp_image_path)

            # 使用从配置中获取的参数
            embedding_objs = DeepFace.represent(img_path=temp_image_path, model_name=model_name,
                                                detector_backend=detector_backend, enforce_detection=False)

            if not embedding_objs:
                results.append({'name': '识别失败', 'distance': 99.0})
                continue

            target_embedding = embedding_objs[0]['embedding']

            if not known_faces:
                results.append({'name': '陌生人', 'distance': 2.0})
                continue

            min_distance = float('inf')
            best_match_name = '陌生人'

            for known_face in known_faces:
                distance = find_cosine_distance(target_embedding, known_face['encoding'])
                logging.info(f"实时人脸(#{i}) vs. 数据库用户'{known_face['name']}' -> 距离: {distance:.4f}")

                if distance < min_distance:
                    min_distance = distance
                    if distance <= threshold:  # 使用从配置中获取的阈值
                        best_match_name = known_face['name']

            logging.info(f"=> 实时人脸(#{i}) 的最终识别结果: '{best_match_name}' (最小距离: {min_distance:.4f})")
            results.append({'name': best_match_name, 'distance': min_distance})

        except Exception as e:
            logging.error(f"处理实时人脸(#{i})时出错: {e}", exc_info=True)
            results.append({'name': '识别错误', 'distance': 99.0})
        finally:
            if temp_image_path and os.path.exists(temp_image_path):
                os.remove(temp_image_path)

    return jsonify(results=results)