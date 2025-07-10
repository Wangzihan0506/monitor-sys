# app/models/employee.py

from datetime import datetime
from exts import db
from app.models.user import User

from enum import Enum as PyEnum

class CheckTypeEnum(PyEnum):
    SELF  = 'self'   # 自行签到
    ADMIN = 'admin'  # 管理员补签


class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(128), nullable=False)
    # 存储人脸特征向量（pickle 序列化或二进制流）
    face_encoding = db.Column(db.LargeBinary, nullable=False)

    # —— 新增 user_id 外键，与 users 表关联 —— 
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 与签到记录的一对多关系
    attendances = db.relationship(
        'Attendance',
        back_populates='employee',
        cascade='all, delete-orphan'
    )

    behaviors = db.relationship(
        'Behavior',
        back_populates='employee',
        cascade='all, delete-orphan'
    )

    # 与 User 的一对一关系
    user = db.relationship(
        'User',
        back_populates='employee',
        uselist=False
    )

    def __repr__(self):
        return f"<Employee id={self.id} name={self.name} user_id={self.user_id}>"

class Attendance(db.Model):
    __tablename__ = 'attendances'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    sign_time   = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    latitude    = db.Column(db.Float, nullable=True)
    longitude   = db.Column(db.Float, nullable=True)
    # —— 新增：签到方式 —— 
    check_type  = db.Column(
        db.Enum(CheckTypeEnum, name='check_type_enum'),
        nullable=False,
        default=CheckTypeEnum.SELF
    )

    # 关联到 Employee
    employee = db.relationship('Employee', back_populates='attendances')

    def __repr__(self):
        return (f"<Attendance id={self.id} employee_id={self.employee_id} "
                f"sign_time={self.sign_time} check_type={self.check_type.value}>")



class BehaviorTypeEnum(PyEnum):
    """
    吃饭，打电话，睡觉，喝水，不在工作岗位
    """
    NORMAL     = '正常'      # 正常
    EATING = "吃饭"          # 吃饭
    DRINKING = "喝水"      # 喝水
    SLEEP = "睡觉"         # 睡觉
    PHONE = "打电话"          # 打电话
    NOTWORKING = "不在工作岗位" # 不在工作岗位

    # WALKING    = 'walking'     # 行走
    # RUNNING    = 'running'     # 跑步
    # SUSPICIOUS = 'suspicious'  # 可疑


# —— 行为记录表 —— 
class Behavior(db.Model):
    __tablename__ = 'behaviors'

    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id  = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    behavior     = db.Column(
        db.Enum(
            BehaviorTypeEnum, 
            # *[e.value for e in BehaviorTypeEnum],
            name='behavior_type_enum'
            ),
        nullable=False
    )
    timestamp    = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # 关联回员工
    employee = db.relationship('Employee', back_populates='behaviors')

    def __repr__(self):
        return (f"<Behavior id={self.id} employee_id={self.employee_id} "
                f"behavior={self.behavior.value} timestamp={self.timestamp}>")