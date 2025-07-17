# fake_behaviors.py

import random
from datetime import datetime, timedelta

from app.models.employee import Behavior, BehaviorTypeEnum  # :contentReference[oaicite:0]{index=0}

def generate_fake_behaviors(emp=None):
    """
    随机生成指定数量的假行为记录并插入数据库。
    - num_records: 生成的记录总数
    """
    assert emp is not None
    behavior_type = random.choice(list(BehaviorTypeEnum))
    # 生成最近一周内的随机时间戳
    delta_days = random.randint(0, 6)
    delta_hours = random.randint(0, 23)
    delta_minutes = random.randint(0, 59)
    ts = datetime.utcnow() - timedelta(days=delta_days,
                                        hours=delta_hours,
                                        minutes=delta_minutes)
    # 构造并添加记录
    behavior = Behavior(
        employee_id=emp.id,
        behavior=behavior_type,
        timestamp=ts
    )
    return behavior
       
