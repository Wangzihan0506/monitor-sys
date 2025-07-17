# app/decorators.py

from functools import wraps
from flask import request, jsonify, current_app, g
import jwt
from .models.user import User


def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            try:
                token = auth_header.split(" ")[1]
                secret = current_app.config['SECRET_KEY']
                print(f"【Token 验证】准备用 SECRET_KEY: '{secret}' 来解码")
                payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
                user_id = payload.get('sub')

                # 在 g 对象上存储用户，g 在单次请求中是全局的
                g.current_user = User.query.get(user_id)

                if g.current_user is None:
                    return jsonify({'code': 1, 'msg': 'Token 无效，找不到用户'}), 401

            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
                print(f"【Token 验证】解码失败！错误: {e}")
                return jsonify({'code': 1, 'msg': 'Token 无效或已过期'}), 401

        if not token:
            return jsonify({'code': 1, 'msg': '缺少 Token 或认证头格式不正确'}), 401

        return f(*args, **kwargs)

    return decorated_function