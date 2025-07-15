import numpy as np
from deepface import DeepFace
from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from flask_migrate import Migrate
import config
import pymysql
from app.exts import db,login_manager
from app.models.employee import Employee
from app.models.user import User
import logging
import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_app(config_class=config):
    # 获取当前文件 (app/__init__.py) 的绝对路径
    current_file_path = os.path.abspath(__file__)
    # 获取当前文件所在的目录 (backend/app)
    current_dir = os.path.dirname(current_file_path)
    # 获取项目根目录 (backend)
    project_root_dir = os.path.join(current_dir, '..')
    # 静态文件目录的绝对路径 (backend/static)
    static_folder_path = os.path.join(project_root_dir, 'static')
    app = Flask(__name__,
                static_folder=static_folder_path,  # <<-- 明确指定静态文件物理路径
                static_url_path='/static')  # <<-- 明确指定 Web 访问路径为 /static
    app.config.from_object(config_class)

    # 初始化扩展
    db.init_app(app)
    migrate = Migrate(app, db)

    from app.models.user import User
    from app.models.employee import Employee, Attendance

    login_manager = LoginManager()  # 临时变量避免冲突
    login_manager.init_app(app)
    login_manager.login_view = 'auth_bp.login'

    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True,
         allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-CSRFToken"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    @login_manager.user_loader
    def load_user(user_id):
        """
        这个函数会在每个受保护的请求中被 Flask-Login 调用。
        它的作用是根据 session 中存储的 user_id，从数据库中加载对应的用户对象。
        """
        try:
            # Flask-Login 传入的 user_id 是字符串，需要转成整数
            return User.query.get(int(user_id))
        except (ValueError, TypeError):
            # 如果 user_id 无效，返回 None
            return None

    # 蓝图注册
    from app.apis.main import main_bp
    from app.apis.auth import auth_bp
    from app.apis.user import user_bp
    from app.apis.behavior import beh_bp
    from app.apis.attendance import attend_bp
    from app.apis.faceEnrollandLogin import face_bp
    from .apis.face_recognition import face_recognition_bp
    from app.apis.alerts import alert_bp
    from app.apis.monitor import monitor_bp


    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp,url_prefix='/api/auth')
    app.register_blueprint(face_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(attend_bp, url_prefix='/api')
    app.register_blueprint(beh_bp, url_prefix='/api')
    app.register_blueprint(face_recognition_bp, url_prefix='/api/face_recognition')
    app.register_blueprint(alert_bp, url_prefix='/api')
    app.register_blueprint(monitor_bp)

    def warmup_models():
        print("【服务器启动】开始预热人脸识别模型...")
        try:
            # 创建一个虚拟的黑色图片 (64x64像素)
            dummy_image = np.zeros((64, 64, 3), dtype=np.uint8)

            # 使用项目中实际用到的模型和检测器进行一次虚拟调用
            DeepFace.represent(
                img_path=dummy_image,
                model_name='Facenet512',
                detector_backend='retinaface'
            )
            print("✅ 模型预热成功！")
        except Exception as e:
            print(f"❌ 模型预热失败: {e}")

    # 在应用上下文准备好后或直接在启动前调用
    warmup_models()

    # 创建数据库表 - 在设置了URI后才创建
    with app.app_context():
         pass
    
    pymysql.install_as_MySQLdb()
    
    return app 