import os
import pymysql
from flask import Flask, request, make_response, current_app
from flask_cors import CORS
from flask_migrate import Migrate
from config import config
import jwt

# 1. 从 exts 导入所有扩展实例
from .exts import db, login_manager, redis_client

# 2. 从 services 导入 AI 服务单例
from .services.yolo_loader import yolo_detector

# 设置环境变量，解决某些OpenCV冲突
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


def create_app(config_name='default'):
    app = Flask(__name__)

    # 3. 正确加载配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)


    # 4. 初始化从 exts 导入的实例
    db.init_app(app)
    Migrate(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # 蓝图名.函数名
    redis_client.init_app(app)

    CORS(app, resources={r"/api/*": {"origins": "http://localhost:8080"}},
         supports_credentials=True, intercept_exceptions=False)


    @app.before_request
    def handle_preflight():
        # 检查进来的请求方法是否为 OPTIONS (预检请求)
        if request.method == "OPTIONS":
            # 创建一个空的响应对象
            res = make_response()

            return res

    # 5. 【修正】只保留一个健壮的 user_loader
    @login_manager.user_loader
    def load_user(user_id):
        try:

            from .models.user import User
            return User.query.get(int(user_id))
        except (ValueError, TypeError):
            return None

    @login_manager.request_loader
    def load_user_from_request(request):
        current_app.logger.info("--- [request_loader] 开始工作 ---")

        auth_header = request.headers.get('Authorization')
        if not auth_header:
            current_app.logger.warning("[request_loader] 失败: 请求头中缺少 'Authorization'")
            return None

        current_app.logger.info(f"[request_loader] 成功获取到 Authorization 头: {auth_header}")

        try:
            token_type, token = auth_header.split()
            if token_type.lower() != 'bearer':
                current_app.logger.warning(f"[request_loader] 失败: Token 类型不是 'bearer'，而是 '{token_type}'")
                return None
        except ValueError:
            current_app.logger.warning("[request_loader] 失败: Authorization 头格式不正确，无法分割")
            return None

        current_app.logger.info(f"[request_loader] 成功分离出 Token: {token[:15]}...")  # 只打印前15位

        try:
            # 使用与生成 token 时完全相同的密钥和算法
            secret = current_app.config['SECRET_KEY']
            current_app.logger.info(f"[request_loader] 准备用密钥 '{secret}' 解码 Token...")

            payload = jwt.decode(token, secret, algorithms=["HS256"])
            user_id = payload.get('sub')

            current_app.logger.info(f"[request_loader] Token 解码成功! Payload: {payload}, User ID: {user_id}")

            if user_id:
                from .models.user import User
                user = User.query.get(user_id)

                if user:
                    current_app.logger.info(f"[request_loader] 【成功】根据 ID={user_id} 找到了用户: {user}")
                    return user  # <--- 这是唯一成功的路径
                else:
                    current_app.logger.warning(
                        f"[request_loader] 【失败】解码成功，但在数据库中找不到 ID={user_id} 的用户")
                    return None
            else:
                current_app.logger.warning("[request_loader] 【失败】解码成功，但 Payload 中没有 'sub' (user_id) 字段")
                return None

        except jwt.ExpiredSignatureError:
            current_app.logger.error("[request_loader] 【致命失败】Token 已过期!")
            return None
        except jwt.InvalidTokenError as e:
            current_app.logger.error(f"[request_loader] 【致命失败】Token 无效 (签名或格式错误): {e}")
            return None
        except Exception as e:
            current_app.logger.error(f"[request_loader] 【致命失败】发生未知异常: {e}", exc_info=True)
            return None

    # 6. 注册所有蓝图
    from .apis.main import main_bp
    from .apis.auth import auth_bp
    from .apis.user import user_bp
    # from .apis.behavior import beh_bp
    from .apis.attendance import attend_bp
    from .apis.faceEnrollandLogin import face_bp
    from .apis.face_recognition import face_recognition_bp
    from .apis.alerts import alert_bp
    from .apis.monitor import monitor_bp
    from .apis.abnormal_detection import abnormal_detection_bp
    from .apis.liveness import liveness_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(face_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(attend_bp, url_prefix='/api')
    # app.register_blueprint(beh_bp, url_prefix='/api')
    app.register_blueprint(face_recognition_bp, url_prefix='/api/face_recognition')
    app.register_blueprint(alert_bp, url_prefix='/api')
    app.register_blueprint(monitor_bp, url_prefix='/api')
    app.register_blueprint(abnormal_detection_bp,
                           url_prefix='/api')  # url_prefix='/api' + route='/detection' -> /api/detection
    app.register_blueprint(liveness_bp, url_prefix='/api')

    pymysql.install_as_MySQLdb()


    return app