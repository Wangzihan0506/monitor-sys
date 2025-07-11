from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
import config
import pymysql
from app.exts import db,login_manager,cors
from app.models.employee import Employee
from app.models.user import User

def create_app(config_class=config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化扩展
    db.init_app(app)
    migrate = Migrate(app, db)

    from app.models.user import User
    from app.models.employee import Employee, Attendance

    cors.init_app(
        app=app,
        resources={r"/api/*": {"origins": "*"}},
        supports_credentials=True
    )
    login_manager.init_app(app)
    login_manager.login_view = 'api.login'

    CORS(app, resources={r"/api/*": {"origins": "http://localhost:8080"}}, supports_credentials=True)

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))
    
    # 蓝图注册
    from app.apis.main import main_bp
    from app.apis.auth import auth_bp
    from app.apis.user import user_bp
    from app.apis.behavior import beh_bp
    from app.apis.attendance import attend_bp
    from app.apis.faceEnrollandLogin import face_bp
    from .apis.face_recognition import face_recognition_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp,url_prefix='/api')
    app.register_blueprint(face_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(attend_bp, url_prefix='/api')
    app.register_blueprint(beh_bp, url_prefix='/api')
    app.register_blueprint(face_recognition_bp, url_prefix='/api/face')

    # 创建数据库表 - 在设置了URI后才创建
    with app.app_context():
         pass
    
    pymysql.install_as_MySQLdb()
    
    return app 