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

@auth_bp.route('/login', methods=['GET', 'POST'])  # <<-- 核心修改：添加 'OPTIONS'
def login():

    if request.method == 'GET':
        return jsonify(code=1, msg="请发送POST请求进行登录或未认证"), 401

        # 以下只处理 POST 请求
    try:
        data = request.get_json()
    except Exception as e:
        return jsonify(code=1, msg=f"请求体格式错误: {e}"), 400

    username = data.get('username')
    password = data.get('password')
    slider_verified = data.get('sliderVerified')

    if not slider_verified:
        return jsonify(code=1, msg='请先完成滑块验证！'), 400

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        login_user(user)
        token = "your_jwt_token_here"  # 替换为实际生成的token
        return jsonify(code=0, msg='登录成功', username=user.username, token=token)

    return jsonify(code=1, msg='用户名或密码错误'), 401

@auth_bp.route("get_csrftoken/")
def get_csrftoken():
    token = generate_csrf()
    resp = make_response(jsonify({'csrf_token': token}))
    resp.set_cookie('csrf_token', token, httponly=False, samesite='Lax')
    return resp

@auth_bp.route('/current_user', methods=['GET', 'OPTIONS']) # <<-- 添加 'OPTIONS'
@login_required
def get_current_user():
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify(username=current_user.username)

@auth_bp.route('/logout', methods=['POST', 'OPTIONS']) # <<-- 添加 'OPTIONS'
@login_required
def logout():
    if request.method == 'OPTIONS':
        return '', 200
    logout_user()
    return jsonify(code=0, msg='登出成功')


@auth_bp.route('/register/', methods=['POST'])
def register():
    """
    接收前端注册表单数据，完成用户和员工的创建。
    【已修改】移除图片验证码校验，依赖前端滑块验证。
    """
    data = request.get_json()
    if not data:
        return jsonify(message="无效的请求数据"), 400

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password')
    slider_verified = data.get('sliderVerified')  # 接收前端滑块验证状态

    # 后端可以做一次简单的校验
    if not slider_verified:
        return jsonify(message="请先完成滑块验证！"), 400

    if not all([username, email, password]):
        return jsonify(message="用户名、邮箱和密码均为必填项"), 400

    if User.query.filter_by(username=username).first():
        return jsonify(message="该用户名已被注册"), 409  # 409 Conflict 更符合语义
    if User.query.filter_by(email=email).first():
        return jsonify(message="该邮箱已被注册"), 409

    try:
        # 创建用户，但不包含人脸信息
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()  # flush() 获取 new_user.id，为创建 Employee 做准备

        current_app.logger.info(f"准备为用户 '{username}' 提交数据库...")
        db.session.commit()
        current_app.logger.info(f"用户 '{username}' 的数据库记录已成功提交！")

        # 同时创建关联的 Employee 记录
        new_employee = Employee(
            name=username,  # 默认员工名和用户名相同
            user_id=new_user.id
        )
        db.session.add(new_employee)
        db.session.commit()  # 一次性提交所有更改

        # 注册成功，返回用户信息，方便前端跳转
        response_data = {
            'code': 0,
            'message': '注册成功！',
            'user': {
                'id': new_user.id,
                'username': new_user.username
            }
        }

        current_app.logger.info(f"构造的响应数据为: {response_data}")

        json_response = jsonify(response_data)

        current_app.logger.info("JSON 响应已成功创建，准备返回。")

        return json_response, 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"注册流程在 try 块中发生严重错误: {e}", exc_info=True)
        return jsonify(message="服务器内部错误，注册失败"), 500