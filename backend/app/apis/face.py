import base64
from io import BytesIO
import numpy as np
from PIL import Image
import face_recognition
from flask import Blueprint, request, jsonify
from app.models.user import User
from app.exts import db
from flask_login import login_user

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
        # 去掉 "data:image/jpeg;base64," 这部分 header
        header, encoded = image_data.split(',', 1)
        img_bytes = base64.b64decode(encoded)
        image = Image.open(BytesIO(img_bytes)).convert('RGB')
        # 将 PIL 图像转换为 numpy 数组，这是 face_recognition 需要的格式
        image_np = np.array(image)
    except Exception as e:
        return jsonify(message=f"图像解码失败: {e}"), 400

    # 3. 使用 face_recognition 检测人脸并提取编码
    # image_np 是 RGB 格式
    face_locations = face_recognition.face_locations(image_np)

    # 业务规则：确保图片中只有一张清晰的人脸
    if len(face_locations) == 0:
        return jsonify(message="未检测到人脸，请确保面部正对摄像头且光线充足"), 400
    if len(face_locations) > 1:
        return jsonify(message="检测到多张人脸，请确保只有您一人在画面中"), 400

    # 提取第一张（也是唯一一张）人脸的编码
    # 这是一个包含 128 个浮点数的列表
    face_encodings = face_recognition.face_encodings(image_np, face_locations)
    if not face_encodings:
        return jsonify(message="无法提取人脸特征，请更换姿势或环境后重试"), 400

    # 4. 将编码（numpy 数组）转换为二进制数据以便存入数据库
    face_encoding_binary = face_encodings[0].tobytes()

    # 5. 更新员工记录并保存到数据库
    try:
        user.face_encoding = face_encoding_binary  # 直接赋值给 user 对象
        db.session.commit()  # 提交更改
    except Exception as e:
        db.session.rollback()
        return jsonify(message=f"数据库保存失败: {e}"), 500

    return jsonify(message="人脸录入成功"), 200


@face_bp.route('/face_verify/', methods=['POST'])
def face_verify():
    """
    人脸二次验证接口
    """
    data = request.get_json()
    if not data or 'username' not in data or 'image' not in data:
        return jsonify(message="缺少用户名或图像数据"), 400

    username = data['username']
    image_data = data['image']

    # 1. 查找用户并获取已存储的人脸编码
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify(message="用户不存在"), 404

    if not user.face_encoding:
        return jsonify(message="该用户未录入人脸信息，无法进行验证"), 400

    # 将数据库中的二进制编码转换回 numpy 数组
    known_face_encoding = np.frombuffer(user.face_encoding, dtype=np.float64)

    # 2. 解码前端上传的图像
    try:
        header, encoded = image_data.split(',', 1)
        img_bytes = base64.b64decode(encoded)
        image = Image.open(BytesIO(img_bytes)).convert('RGB')
        image_np = np.array(image)
    except Exception as e:
        return jsonify(message=f"图像解码失败: {e}"), 400

    # 3. 提取新图像中的人脸编码
    face_locations = face_recognition.face_locations(image_np)
    if len(face_locations) != 1:
        return jsonify(message="请确保画面中仅有您一人且面部清晰"), 400

    unknown_face_encodings = face_recognition.face_encodings(image_np, face_locations)
    if not unknown_face_encodings:
        return jsonify(message="无法从图像中提取人脸特征"), 400

    unknown_face_encoding = unknown_face_encodings[0]

    # 4. 比对人脸
    # compare_faces 返回一个布尔值列表 [True] 或 [False]
    # tolerance 参数可以调整比对的严格程度，默认是 0.6。值越小越严格。
    matches = face_recognition.compare_faces([known_face_encoding], unknown_face_encoding, tolerance=0.5)

    if matches and matches[0]:

        login_user(user)  # 建立会话

        return jsonify({
            'message': '人脸验证成功',
        }), 200
    else:
        return jsonify(message="人脸不匹配"), 401  # 401 Unauthorized