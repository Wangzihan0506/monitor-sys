# 文件: app/apis/auth.py

#用户认证相关接口

import random
import sqlalchemy
from flask import request
from flask import Blueprint, jsonify, make_response, current_app
from flask_wtf.csrf import generate_csrf
from PIL import Image, ImageDraw, ImageFont
from config import redis_con, cfg_flask
from flask_login import login_user, login_required, logout_user, current_user
import io, uuid
from app.models.user import User
from app.models.employee import Employee
from app.exts import db
import pickle
import traceback

# 蓝图定义保持不变
auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login/', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    verify_code = (data.get('verify_code') or '').upper()

    # 验证码部分保持不变
    uuid_code = request.cookies.get('uuid')
    key = f"{cfg_flask.get('APP_NAME', 'flask_app')}_{uuid_code}"
    stored = redis_con.get(key)
    # 建议在生产环境中启用验证码校验
    # if not stored or pickle.loads(stored).upper() != verify_code:
    #     return jsonify(success=False, message='验证码错误'), 400

    # 验证用户名/密码部分保持不变
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify(success=False, message='用户名或密码错误'), 401

    return jsonify(success=True, message='密码验证成功'), 200


# get_verify_code, check_verify_code, get_csrftoken 函数保持不变
# ... (省略未修改的函数代码) ...

@auth_bp.route('/get_verify_code/', methods=['GET', 'OPTIONS'])
def get_verify_code():
    # ... (代码不变)
    print("====== 后端 /api/get_verify_code/ 接口被成功命中！======")
    if request.method == 'OPTIONS':
        resp = make_response('', 204)
        resp.headers.update({
            'Access-Control-Allow-Origin': request.headers.get('Origin', '*'),
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Allow-Methods': 'GET,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        })
        return resp
    uuid_code = request.cookies.get('uuid')
    chars = '0123456789ABCDEFGHJKLMNPQRSTUVWXYZ'
    text = ''.join(random.sample(chars, 4))
    img = Image.new('RGB', (100, 50), (255, 255, 240))
    font = ImageFont.truetype('fonts/simhei.ttf', 40)
    draw = ImageDraw.Draw(img)
    draw.text((10, 5), text, font=font, fill='red')
    buf = io.BytesIO()
    img.save(buf, 'PNG')
    buf.seek(0)
    image_data = buf.read()
    if not uuid_code:
        uuid_code = str(uuid.uuid4())
    key = f'{cfg_flask.get("APP_NAME", "flask_app")}_{uuid_code}'
    redis_con.set(key, pickle.dumps(text), ex=300)
    resp = make_response(image_data)
    resp.headers['Content-Type'] = 'image/png'
    resp.set_cookie('uuid', uuid_code, max_age=300, httponly=True)
    resp.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
    resp.headers['Access-Control-Allow-Credentials'] = 'true'
    return resp

@auth_bp.route("get_csrftoken/")
def get_csrftoken():
    token = generate_csrf()
    resp = make_response(jsonify({'csrf_token': token}))
    resp.set_cookie('csrf_token', token, httponly=False, samesite='Lax')
    return resp

@auth_bp.route("/current_user/", methods=["GET"])
@login_required
def get_current_user():
    """
    返回当前登录用户信息
    """
    # --- 修改点 2 ---
    # 获取当前用户信息时，移除 'role' 字段
    return jsonify({
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email
        # "role": current_user.role.value  <-- 已删除
    })


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """
    注销当前会话
    """
    logout_user()
    return jsonify({"message": "登出成功"}), 200


@auth_bp.route('/register/', methods=['POST'])
def register():
    """
    接收前端注册表单数据，完成用户和员工的创建。
    """
    data = request.get_json()
    if not data:
        return jsonify(message="无效的请求数据"), 400

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password')
    verify_code = data.get('verify_code', '').upper()

    if not all([username, email, password, verify_code]):
        return jsonify(message="用户名、邮箱、密码和验证码均为必填项"), 400

    uuid_code = request.cookies.get('uuid')
    if not uuid_code:
        return jsonify(message="验证码已过期，请刷新"), 400

    key = f"{cfg_flask.get('APP_NAME', 'flask_app')}_{uuid_code}"
    stored_code_bytes = redis_con.get(key)
    if not stored_code_bytes:
        return jsonify(message="验证码无效或已过期"), 400

    stored_code = pickle.loads(stored_code_bytes).upper()
    if stored_code != verify_code:
        return jsonify(message="验证码错误"), 400

    redis_con.delete(key)

    if User.query.filter_by(username=username).first():
        return jsonify(message="该用户名已被注册"), 409
    if User.query.filter_by(email=email).first():
        return jsonify(message="该邮箱已被注册"), 409

    try:
        # --- 修改点 3 ---
        # 创建 User 实例时，不再需要处理 role，因为它已从模型中删除
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()

        new_employee = Employee(
            name=username,
            user_id=new_user.id
        )
        db.session.add(new_employee)
        db.session.commit()

        # --- 修改点 4 ---
        # 注册成功返回的数据中，移除 'role' 字段
        return jsonify({
            'message': '注册成功！',
            'user': {
                'id': new_user.id,
                'username': new_user.username
                # 'role': new_user.role.value <-- 已删除
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        error_type = type(e).__name__
        error_message = str(e)
        error_traceback = traceback.format_exc()

        current_app.logger.error(f"注册失败 - 错误类型: {error_type}")
        current_app.logger.error(f"错误信息: {error_message}")
        current_app.logger.error(f"堆栈跟踪:\n{error_traceback}")

        if isinstance(e, sqlalchemy.exc.IntegrityError):
            if "username" in error_message.lower():
                return jsonify(message="用户名已被使用"), 400
            elif "email" in error_message.lower():
                return jsonify(message="邮箱已被使用"), 400
            else:
                return jsonify(message="数据完整性错误，请检查输入"), 400
        elif isinstance(e, sqlalchemy.exc.SQLAlchemyError):
            return jsonify(message="数据库操作失败，请稍后重试"), 500
        else:
            return jsonify(message="服务器内部错误，注册失败，请稍后重试"), 500