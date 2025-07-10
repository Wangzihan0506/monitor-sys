from flask import (
    Blueprint,make_response,jsonify,request,current_app
)
from flask_wtf.csrf import generate_csrf
from utils import restful
from PIL import Image, ImageDraw, ImageFont
import random,io,uuid,pickle
from config import redis_con,cfg_flask
from datetime import datetime
import base64, requests
from io import BytesIO
from PIL import Image
import numpy as np
import face_recognition
from app.models.employee import Employee,Attendance,CheckTypeEnum,Behavior
from exts import db
from flask_login import login_user,login_required
from app.models.user import User,RoleEnum
import pytz
from datetime import timedelta
from flask_login import login_required,current_user,logout_user
import os
import numpy as np
import cv2
from utils.configUtils import recognize_employee_behavior


api_bp = Blueprint(
    "api", __name__, url_prefix="/api/"
    )


@api_bp.route('/login/', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    verify_code = (data.get('verify_code') or '').upper()
    
    print("data:",data)
    # 1. 验证验证码（同 check_verify_code 逻辑）:contentReference[oaicite:6]{index=6}:contentReference[oaicite:7]{index=7}
    uuid_code = request.cookies.get('uuid')
    key = f"{cfg_flask.get('APP_NAME','flask_app')}_{uuid_code}"
    stored = redis_con.get(key)
    print("verify_code:",verify_code)
    print("stored:",stored)
    # if not stored or pickle.loads(stored).upper() != verify_code:
    #     return jsonify(success=False, message='验证码错误'), 400

    # 2. 验证用户名/密码
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify(success=False, message='用户名或密码错误'), 401

    # 3. 登录用户（如使用 flask-login）
    login_user(user)

    return jsonify(success=True, message='登录成功', data={
        'username': user.username,
        'role': user.role.value
    })


@api_bp.route('/get_verify_code/', methods=['GET', 'OPTIONS'])
def get_verify_code():
    # 支持预检
    if request.method == 'OPTIONS':
        resp = make_response('', 204)
        resp.headers.update({
            'Access-Control-Allow-Origin': request.headers.get('Origin', '*'),
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Allow-Methods': 'GET,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        })
        return resp

    # 从 cookie 里读 uuid
    uuid_code = request.cookies.get('uuid')
    # 验证码字符去掉易混淆的 O、I
    chars = '0123456789ABCDEFGHJKLMNPQRSTUVWXYZ'
    text = ''.join(random.sample(chars, 4))

    # 生成图片
    img = Image.new('RGB', (100, 50), (255, 255, 240))
    font = ImageFont.truetype('fonts/simhei.ttf', 40)
    draw = ImageDraw.Draw(img)
    draw.text((10, 5), text, font=font, fill='red')

    # 写入内存二进制
    buf = io.BytesIO()
    img.save(buf, 'PNG')
    buf.seek(0)
    image_data = buf.read()

    # 如果没有 uuid，就新建一个
    if not uuid_code:
        uuid_code = str(uuid.uuid4())

    # 缓存到 Redis，300 秒后过期

    key = f'{cfg_flask.get("APP_NAME","flask_app")}_{uuid_code}'
    redis_con.set(key, pickle.dumps(text), ex=300)

    # 构造响应
    resp = make_response(image_data)
    resp.headers['Content-Type'] = 'image/png'
    # 把 uuid 写回 cookie，前端就不用自己管理
    resp.set_cookie('uuid', uuid_code, max_age=300, httponly=True)
    # CORS
    resp.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
    resp.headers['Access-Control-Allow-Credentials'] = 'true'
    return resp


@api_bp.route('/check_verify_code/', methods=['POST'])
def check_verify_code():
    data = request.get_json(force=True)
    verify_code = (data.get('verify_code') or '').upper()
    uuid_code = request.cookies.get('uuid')

    if not verify_code:
        return jsonify(success=False, message='请输入验证码'), 400
    if not uuid_code:
        return jsonify(success=False, message='验证码已过期'), 400
    APP_NAME = "app_name"
    key = f'{APP_NAME}_{uuid_code}'
    stored = redis_con.get(key)
    if not stored:
        return jsonify(success=False, message='验证码无效'), 400

    src_text = pickle.loads(stored)
    if verify_code != src_text:
        return jsonify(success=False, message='你输入的验证码有误'), 400

    return jsonify(success=True, message='ok')



@api_bp.route("get_csrftoken/")
def get_csrftoken():
     # 1. 生成一个新的 CSRF token
    token = generate_csrf()
    # 2. 把 token 放到 JSON 里返回
    resp = make_response(jsonify({'csrf_token': token}))
    # 3. （可选）同时设置到 Cookie，方便前端自动携带
    #    httponly=False 允许 JavaScript 读取，如果你要防范 XSS，改为 True
    resp.set_cookie('csrf_token', token, httponly=False, samesite='Lax')
    return resp


# @api_bp.route('/attendance/dection/', methods=['POST'])
# @login_required
# def attendance_detection():
#     """
#     接收前端定时上传的 base64 编码截图，解码为图像后进行相应的处理（如行为检测、存储等），
#     最后返回 JSON 格式的检测结果或状态。
#     """
#     try:
#         data = request.get_json()
#         if not data or 'image' not in data:
#             return jsonify({'error': 'No image provided'}), 400

#         image_data = data['image']
#         # 前端发送的 image 格式类似 "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABA..."
#         # 先去掉 "data:image/jpeg;base64," 这部分
#         if ',' in image_data:
#             header, encoded = image_data.split(',', 1)
#         else:
#             encoded = image_data

#         # 将 Base64 字符串解码为二进制
#         try:
#             img_bytes = base64.b64decode(encoded)
#         except Exception as e:
#             return jsonify({'error': 'Invalid base64 data', 'detail': str(e)}), 400

#         # 转换为 NumPy 数组，再通过 OpenCV 解码为图像
#         nparr = np.frombuffer(img_bytes, dtype=np.uint8)
#         img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
#         if img is None:
#             return jsonify({'error': 'Failed to decode image'}), 400

#         # save_dir = os.path.join(os.getcwd(), 'local_images')

#         save_dir = os.path.join(current_app.root_path, 'local_images')

#         os.makedirs(save_dir, exist_ok=True)
#         now = datetime.now()
#         timestamp = now.strftime("%Y%m%d%H%M%S")
#         img_filename = os.path.join(save_dir, f"{timestamp}.jpg")
    
#         success = cv2.imwrite(img_filename, img)
#         print(f"[DEBUG] cv2.imwrite 返回：{success}, 保存路径：{img_filename}")


#         # 2. TODO: 在这里调用你的行为检测模型，假设模型返回一个 dict 结果
#         #    比如： result = run_behavior_model(img)
#         #    下面我们先模拟一个假检测结果
#         result = {
#             'behavior': 'normal',       # 示例：检测到的行为
#             'confidence': 0.92,         # 示例：模型置信度
#             'timestamp': int(np.floor(cv2.getTickCount() / cv2.getTickFrequency()))
#         }

#         # 3. 将检测结果返回给前端
#         return jsonify({
#             'status': 'success',
#             'data': result
#         }), 200

#     except Exception as e:
#         # 捕获任意异常并返回 500
#         return jsonify({'error': 'Internal Server Error', 'detail': str(e)}), 500




@api_bp.route('/attendance/dection/', methods=['POST'])
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


@api_bp.route('attendance/checkin/', methods=['POST'], strict_slashes=False)
def checkin():
    data = request.get_json() or {}
    image_data = data.get('image')
    latitude = data.get('latitude',None)
    longitude = data.get('longitude',None)
    # check_type = data.get("check_type","self")

    if not image_data:
        return jsonify({'message': '缺少图像数据'}), 400

    # 解码 Base64 图像
    try:
        header, encoded = image_data.split(',', 1)
        img_bytes = base64.b64decode(encoded)
    except Exception:
        return jsonify({'message': '图像解码失败'}), 400

    try:
        image = Image.open(BytesIO(img_bytes)).convert('RGB')
    except Exception:
        return jsonify({'message': '无法读取图像'}), 400

    # 转为 numpy 数组
    image_np = np.array(image)

    # 人脸识别
    emp_id = recognize_face(image_np)
    if not emp_id:
        return jsonify({'message': '识别不到人脸或未注册'}), 404

    employee = Employee.query.get(emp_id)
    if not employee:
        return jsonify({'message': '员工不存在'}), 404

    # 记录签到
    # sign_time = datetime.utcnow()
    import pytz
    tz = pytz.timezone("Asia/Shanghai")
    sign_time = datetime.now(tz)
    attendance = Attendance(
        employee_id=employee.id,
        sign_time=sign_time,
        latitude=latitude,
        longitude=longitude

    )
    db.session.add(attendance)
    db.session.commit()

    return jsonify({
        'employeeName': employee.name,
        'signTime': sign_time.strftime('%Y-%m-%d %H:%M:%S')
    }), 200


@api_bp.route('/attendance/records', methods=['GET'])
def get_attendance_records():
    """
    返回所有签到记录，包含员工姓名、签到时间和地址描述。
    """
    # 1. 拉取所有记录，按时间倒序
    records = Attendance.query.order_by(Attendance.sign_time.desc()).all()

    # 2. 获取百度地图逆地理编码的 AK（需在配置中设置）
    ak = current_app.config.get('BAIDU_MAP_AK', None)

    result = []
    for rec in records:
        lat = rec.latitude
        lng = rec.longitude
        address = None

        # 3. 调用百度地图逆地理编码（仅当 lat/lng 不为 None 时）
        if ak and lat is not None and lng is not None:
            try:
                resp = requests.get(
                    'http://api.map.baidu.com/reverse_geocoding/v3/',
                    params={
                        'ak': ak,
                        'output': 'json',
                        'coordtype': 'wgs84ll',
                        'location': f'{lat},{lng}'
                    },
                    timeout=3
                )
                data = resp.json()
                if data.get('status') == 0:
                    comp = data['result'].get('addressComponent', {})
                    street = data['result'].get('sematic_description')
                    if street:
                        address = street
                    else:
                        address = data['result'].get('formatted_address') or comp.get('district')
            except Exception:
                # 网络或解析异常，忽略，后面有 fallback
                address = None

        # 4. fallback：如果没有拿到地址，再根据坐标或直接标记未知
        if not address:
            if lat is not None and lng is not None:
                address = f"经度:{lng:.6f}, 纬度:{lat:.6f}"
            else:
                address = "地址未知"

        result.append({
            'employeeName': rec.employee.name,
            'signTime': rec.sign_time.strftime('%Y-%m-%d %H:%M:%S'),
            'address': address,
            "check_type":rec.check_type.value
        })

    return jsonify(result), 200

@api_bp.route('/attendance/records/user', methods=['GET'])
@login_required
def get_user_attendance_records():
    """
    获取当前登录用户的签到历史（分页），返回字段：
    - records: [{ employeeName, signTime, address }, ...]
    - total: 总记录数
    - page: 当前页码
    """
    # 1. 从请求中获取分页参数
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
    except (ValueError, TypeError):
        return jsonify({'message': '分页参数必须为整数'}), 400

    # 2. 获取当前用户对应的员工记录
    emp = getattr(current_user, 'employee', None)
    if not emp:
        return jsonify({'message': '未找到对应的员工信息'}), 404

    # 3. 构造查询并分页（按签到时间倒序）
    pagination = (
        Attendance.query
        .filter_by(employee_id=emp.id)
        .order_by(Attendance.sign_time.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    ak = current_app.config.get('BAIDU_MAP_AK', None)
    records = []

    for rec in pagination.items:
        # 4. 逆地理编码获取地址
        address = None
        if ak and rec.latitude is not None and rec.longitude is not None:
            try:
                resp = requests.get(
                    'http://api.map.baidu.com/reverse_geocoding/v3/',
                    params={
                        'ak': ak,
                        'output': 'json',
                        'coordtype': 'wgs84ll',
                        'location': f'{rec.latitude},{rec.longitude}'
                    },
                    timeout=3
                ).json()
                if resp.get('status') == 0:
                    street = resp['result'].get('sematic_description')
                    comp = resp['result'].get('addressComponent', {})
                    address = street or resp['result'].get('formatted_address') or comp.get('district')
            except Exception:
                address = None

        # 5. fallback：若无地址，则显示经纬度。如果经纬度本身为空，显示未知
        if not address:
            if rec.latitude is not None and rec.longitude is not None:
                address = f"经度:{rec.longitude:.6f}, 纬度:{rec.latitude:.6f}"
            else:
                address = "经度:未知, 纬度:未知"

        records.append({
            'employeeName': rec.employee.name,
            'signTime': rec.sign_time.strftime('%Y-%m-%d %H:%M:%S'),
            'address': address
        })

    # 6. 返回 JSON，多返回当前页（page）方便前端展示
    return jsonify({
        'records': records,
        'total': pagination.total,
        'page': pagination.page
    }), 200


@api_bp.route("/current_user/", methods=["GET"])
@login_required
def get_current_user():
    """
    返回当前登录用户信息
    """
    return jsonify({
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role.value
    })


@api_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """
    注销当前会话
    """
    logout_user()
    return jsonify({"message": "登出成功"}), 200


@api_bp.route("/users", methods=["GET"])
@login_required
def list_users():
    """
    列出所有用户
    """
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role.value
        } for u in users
    ]), 200


@api_bp.route("/users", methods=["POST"])
@login_required
def create_user():
    """
    新增用户
    """
    data = request.get_json() or {}
    print("data:",data)
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")
    role = role.lower()

    if not all([username, email, password, role]):
        return jsonify({"message": "缺少必要参数"}), 400

    if role not in {r.value for r in RoleEnum}:
        return jsonify({"message": "角色无效"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "用户名已存在"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "邮箱已存在"}), 400

    user = User(username=username, email=email, role=RoleEnum(role))
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value
    }), 201


@api_bp.route("/users/<int:user_id>", methods=["PUT"])
@login_required
def update_user(user_id):
    """
    更新用户信息
    """
    user = User.query.get(user_id)
    print("user:",user)
    if not user:
        return jsonify({"message": "用户不存在"}), 404

    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    # password = data.get("password")
    role = data.get("role")
    role = role.lower()

    print(username,email,role)
    _set = {r.value for r in RoleEnum}
    print(_set)
    if username:
        user.username = username
    if email:
        user.email = email
    if role:
        if role not in _set:
            return jsonify({"message": "角色无效"}), 400
        user.role = RoleEnum(role)
    # if password:
    #     user.set_password(password)

    db.session.commit()
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value
    }), 200


@api_bp.route("/users/<int:user_id>", methods=["DELETE"])
@login_required
def delete_user(user_id):
    """
    删除用户，同时级联删除对应的 Employee 记录
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "用户不存在"}), 404

    # 先删除与该用户关联的员工记录
    employee = Employee.query.filter_by(user_id=user_id).first()
    if employee:
        db.session.delete(employee)

    # 再删除用户
    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "删除成功"}), 200

@api_bp.route('/attendance/makeup', methods=['OPTIONS', 'POST'])
def attendance_makeup():
    # CORS 预检
    if request.method == 'OPTIONS':
        resp = make_response('', 204)
        resp.headers.update({
            'Access-Control-Allow-Origin': request.headers.get('Origin', '*'),
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        })
        return resp

    data = request.get_json(force=True) or {}
    user_id = data.get('userId')
    date_str = data.get('date')


    if not user_id or not date_str:
        return jsonify({'message': '参数不完整（需要 userId 和 date）'}), 400

    # 解析日期
    sign_time = None
    for fmt in (
        '%Y-%m-%d',                    # 仅日期
        '%Y-%m-%dT%H:%M:%S.%fZ',       # 带毫秒 + Z
        '%Y-%m-%dT%H:%M:%S.%f',        # 带毫秒
        '%Y-%m-%dT%H:%M:%S'            # 不带毫秒
    ):
        try:
            sign_time = datetime.strptime(date_str, fmt)
            break
        except ValueError:
            continue

    # 如果上面都没匹配，再尝试 strip Z 后用 fromisoformat
    if sign_time is None:
        try:
            ds = date_str.rstrip('Z')
            sign_time = datetime.fromisoformat(ds)
        except ValueError:
            return jsonify({'message': f'无法解析的日期格式: {date_str}'}), 400

    # 写入数据库
    try:
        makeup = Attendance(
            employee_id=user_id,
            sign_time=sign_time,
            latitude=None,
            longitude=None,
            check_type = CheckTypeEnum.ADMIN
        )
        db.session.add(makeup)
        db.session.commit()
        return jsonify({'message': '补签成功'}), 200

    except Exception as e:
        current_app.logger.error(f"补签失败：{e}")
        db.session.rollback()
        return jsonify({'message': '服务器内部错误，补签失败'}), 500
    
# @api_bp.route("/attendance/makeup", methods=["POST"])
# @login_required
# def makeup_attendance():
#     """
#     给指定用户在指定时间补签
#     """
#     data = request.get_json() or {}
#     user_id = data.get("userId")
#     date_str = data.get("date")

#     if not all([user_id, date_str]):
#         return jsonify({"message": "缺少参数"}), 400

#     try:
#         sign_time = datetime.fromisoformat(date_str)
#     except ValueError:
#         return jsonify({"message": "日期格式错误，应为 ISO 格式"}), 400

#     # 直接按 employee_id 补签
#     employee = Employee.query.get(user_id)
#     if not employee:
#         return jsonify({"message": "用户不存在"}), 404

#     attendance = Attendance(employee_id=user_id, sign_time=sign_time)
#     db.session.add(attendance)
#     db.session.commit()

#     return jsonify({"message": "补签成功"}), 200


@api_bp.route('/behavior/recognize/', methods=['POST'])
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



@api_bp.route('/behaviorRecognition', methods=['GET'])
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