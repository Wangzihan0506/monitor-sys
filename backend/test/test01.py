import configparser
from typing import Dict
from config import BASE_DIR
import os
from utils.configUtils import get_section_dict

# —— 使用示例 ——
if __name__ == '__main__':
    ini_path = os.path.join(
        BASE_DIR,"config.ini"
    )
    try:
        mysql_cfg = get_section_dict(ini_path, 'redis')
        print("MySQL 配置：", mysql_cfg)
    except KeyError as e:
        print(e)
    print(mysql_cfg)
