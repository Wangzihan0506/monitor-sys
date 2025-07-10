# app/models/user.py

from datetime import datetime
from enum import Enum as PyEnum
from exts import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class RoleEnum(PyEnum):
    ADMIN = 'admin'
    USER  = 'user'

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.Text, nullable=False)

    role = db.Column(
        db.Enum(RoleEnum, name='role_enum'),
        nullable=False,
        default=RoleEnum.USER
    )

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
