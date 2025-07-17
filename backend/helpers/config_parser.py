import configparser
import re
from typing import Dict, Any

def get_section_dict(
    file_path: str,
    section: str,
    encoding: str = 'utf-8'
) -> Dict[str, Any]:
    """
    从指定的 ini 文件中读取一个区块，将该区块的 key/value 封装为字典返回，
    并自动将字符串形式的布尔值、整数和浮点数转换为相应的 Python 类型。
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

        if low in ('true', 'yes', 'on'):
            parsed_val: Any = True
        elif low in ('false', 'no', 'off'):
            parsed_val = False
        elif re.fullmatch(r'-?\d+', v):
            parsed_val = int(v)
        elif re.fullmatch(r'-?\d+\.\d+', v):
            parsed_val = float(v)
        else:
            parsed_val = v

        parsed[key] = parsed_val

    return parsed