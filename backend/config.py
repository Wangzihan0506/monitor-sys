import os
import sys

import redis
from helpers.config_parser import get_section_dict

# 基础目录配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_INI_PATH = os.path.join(BASE_DIR, "config.ini")
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# --- 从 config.ini 读取配置 ---
cfg_mysql = get_section_dict(file_path=CONFIG_INI_PATH, section="mysql")
cfg_redis = get_section_dict(file_path=CONFIG_INI_PATH, section="redis")
cfg_flask = get_section_dict(file_path=CONFIG_INI_PATH, section="flask")


class Config:
    """
    基础配置类，包含所有环境通用的配置。
    """
    # 1. Flask 和扩展的通用配置
    # 从 .ini 文件读取，如果失败则使用默认值
    SECRET_KEY = "dfasdfsdflasdjfl"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 2. 外部服务 API Key
    BAIDU_MAP_AK = "bQ8D7LpqqNsHDWNIgzuL5wKXFrb3grbc"

    # 3. AI 模型相关配置
    FACE_MODEL_NAME = "Facenet512"
    YOLO_MODEL_NAME = "yolov5s"
    FACE_DETECTOR_BACKEND = "retinaface"
    DISTANCE_METRIC = "cosine"
    FACE_VERIFY_THRESHOLD = 0.40
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    @staticmethod
    def init_app(app):
        # 这个静态方法可以在创建 app 后执行一些初始化操作，是可选的
        pass


class DevelopmentConfig(Config):
    """
    开发环境配置
    """
    DEBUG = True

    # 数据库连接字符串
    DB_URI = 'mysql+pymysql://%s:%s@%s:%s/%s?charset=utf8mb4' % (
        cfg_mysql.get("user", "root"),
        cfg_mysql.get("password", "linyanzi2005"),
        cfg_mysql.get("host", "localhost"),
        cfg_mysql.get("port", "3307"),
        cfg_mysql.get("database", "detection"),
    )
    SQLALCHEMY_DATABASE_URI = DB_URI

    # Redis 连接实例
    REDIS_HOST = cfg_redis.get("host", "localhost")
    REDIS_PORT = int(cfg_redis.get("port", 6379))
    REDIS_DB = int(cfg_redis.get("db", 1))
    REDIS_URL = "redis://:%s@%s:%s/%s" % (
        cfg_redis.get("password", ""),  # Redis 密码（如果有的话）
        cfg_redis.get("host", "localhost"),
        cfg_redis.get("port", 6379),
        cfg_redis.get("db", 1)
    )


class ProductionConfig(DevelopmentConfig):  # 生产环境可以继承自开发环境，然后覆盖特定配置
    """
    生产环境配置
    """
    DEBUG = False


# --- 创建字典，方便在 app 工厂函数中根据环境变量选择配置 ---
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig  # 默认使用开发环境配置
}




