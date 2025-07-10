from flask import Flask
from flask_migrate import Migrate
import config
import pymysql
from exts import db,login_manager,cors
import redis
from app.models.employee import Employee,Attendance
from app.models.user import User


def create_app(config_class=config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    
    
    # 初始化扩展
    db.init_app(app)
    migrate = Migrate(app, db)

    cors.init_app(
        app=app,
        resources={r"/api/*": {"origins": "*"}},
        supports_credentials=True
    )
    login_manager.init_app(app)
    login_manager.login_view = 'api.login'

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))
    
    # 蓝图注册
    from app.routes.main import main_bp
    from app.routes.api import api_bp


    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp,url_prefix='/api')
    


    
    # 创建数据库表 - 在设置了URI后才创建
    with app.app_context():

        db.create_all()
    
    pymysql.install_as_MySQLdb()
    
    return app 