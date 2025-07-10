# fake_behaviors.py

import random
from datetime import datetime, timedelta

from app import create_app         # 如果你的项目使用工厂函数，请确保这里导入正确
from exts import db
from app.models.employee import Employee, Behavior, BehaviorTypeEnum  # :contentReference[oaicite:0]{index=0}

def generate_fake_behaviors(num_records: int = 100):
    """
    随机生成指定数量的假行为记录并插入数据库。
    - num_records: 生成的记录总数
    """
    # 获取所有员工
    employees = Employee.query.all()
    if not employees:
        print("未找到任何员工，请先插入员工数据。")
        return

    for _ in range(num_records):
        emp = random.choice(employees)
        # 随机选择一种行为类型
        behavior_type = random.choice(list(BehaviorTypeEnum))
        # 生成最近一周内的随机时间戳
        delta_days = random.randint(0, 6)
        delta_hours = random.randint(0, 23)
        delta_minutes = random.randint(0, 59)
        ts = datetime.utcnow() - timedelta(days=delta_days,
                                           hours=delta_hours,
                                           minutes=delta_minutes)
        # 构造并添加记录
        record = Behavior(
            employee_id=emp.id,
            behavior=behavior_type,
            timestamp=ts
        )
        db.session.add(record)

    db.session.commit()
    print(f"已插入 {num_records} 条假行为记录。")

if __name__ == "__main__":
    # 创建 Flask 应用并推入上下文
    app = create_app()
    with app.app_context():
        # 生成并插入 200 条假数据，可自行修改数量
        generate_fake_behaviors(num_records=200)
