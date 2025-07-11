
import os

#===============================================================================
# 基础路由配置
#===============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#===============================================================================
# 随机密钥
#===============================================================================
SECRET_KEY = "dfasdfsdflasdjfl"


#===============================================================================
# msyql 数据库配置
#===============================================================================
from utils.config_parser import get_section_dict

cfg_msyql = get_section_dict(
    file_path=os.path.join(
        BASE_DIR,"config.ini"
    ),
    section="mysql"
)

DB_URI = 'mysql+pymysql://%s:%s@%s:%s/%s?charset=utf8mb4' % (
    cfg_msyql.get("user","root"),
    cfg_msyql.get("password","linyanzi2005"),
    cfg_msyql.get("host","localhost"),
    cfg_msyql.get("port","3307"),
    cfg_msyql.get("database","detection"),
    )

SQLALCHEMY_DATABASE_URI = DB_URI


#===============================================================================
# redis 数据库配置
#===============================================================================
import redis
cfg_redis = get_section_dict(
    file_path=os.path.join(
        BASE_DIR,"config.ini"
    ),
    section="redis"
)

redis_con = redis.Redis(
    host=cfg_redis.get("host","localhost"), 
    port=cfg_redis.get("port",6379), 
    db=cfg_redis.get("db",1), 
    decode_responses=cfg_redis.get("decode_responses",False)
)

cfg_flask = get_section_dict(
    file_path=os.path.join(
        BASE_DIR,"config.ini"
    ),
    section="flask"
)

#===============================================================================
# 百度地图 api key
#===============================================================================
BAIDU_MAP_AK = "bQ8D7LpqqNsHDWNIgzuL5wKXFrb3grbc"