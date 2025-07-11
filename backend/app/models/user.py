# app/models/user.py

from datetime import datetime
from app.exts import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.Text, nullable=False)
    # --- 新增字段 ---
    # 人脸特征编码，使用 LargeBinary 存储二进制数据
    # nullable=True 是必须的，因为用户注册时还没有人脸数据
    face_encoding = db.Column(db.LargeBinary, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # —— 与 Employee 的一一对应关系 —— 
    employee = db.relationship(
        'Employee',
        back_populates='user',
        uselist=False
    )

    def __repr__(self):
        return f'<User {self.username}({self.role.value})>'

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
