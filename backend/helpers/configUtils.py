
import random
from app.models.employee import BehaviorTypeEnum,Behavior
from datetime import datetime,timedelta
import pytz

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
       