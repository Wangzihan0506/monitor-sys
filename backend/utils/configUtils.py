import configparser
from typing import Dict
from typing import Dict, Any
import configparser
import re,random
from app.models.employee import BehaviorTypeEnum,Behavior
from datetime import datetime,timedelta
import pytz

def get_section_dict(
    file_path: str,
    section: str,
    encoding: str = 'utf-8'
) -> Dict[str, Any]:
    """
    从指定的 ini 文件中读取一个区块，将该区块的 key/value 封装为字典返回，
    并自动将字符串形式的布尔值、整数和浮点数转换为相应的 Python 类型。

    :param file_path: ini 文件路径
    :param section: 要读取的区块名称
    :param encoding: 文件编码，默认为 'utf-8'
    :return: 区块键值对字典，value 类型可能为 str, int, float, 或 bool
    :raises KeyError: 如果指定区块在文件中不存在
    """
    config = configparser.ConfigParser()
    config.optionxform = str  # 保持 key 的大小写
    config.read(file_path, encoding=encoding)

    if section not in config:
        raise KeyError(f"Section '{section}' not found in '{file_path}'.")

    raw = config[section]
    parsed: Dict[str, Any] = {}

    for key, value in raw.items():
        v = value.strip()
        low = v.lower()

        # 布尔类型
        if low in ('true', 'yes', 'on'):
            parsed_val: Any = True
        elif low in ('false', 'no', 'off'):
            parsed_val = False
        # 整数
        elif re.fullmatch(r'-?\d+', v):
            parsed_val = int(v)
        # 浮点数
        elif re.fullmatch(r'-?\d+\.\d+', v):
            parsed_val = float(v)
        # 其余保持字符串
        else:
            parsed_val = v

        parsed[key] = parsed_val

    return parsed


def recognize_employee_behavior(emp=None):
    assert emp is not None

    # 随机挑选一个行为类型
    behavior_type = random.choice(list(BehaviorTypeEnum))

    tz = pytz.timezone('Asia/Shanghai')
    ts = datetime.now(tz)

    # 构造并返回记录（注意：只是返回对象，未自动写库）
    behavior = Behavior(
        employee_id=emp.id,
        behavior=behavior_type,
        timestamp=ts
    )
    return behavior
       