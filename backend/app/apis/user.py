#用户管理接口
from flask import Blueprint, jsonify, request
from flask_login import login_required
from app.exts import db
from .. import Employee, User


user_bp = Blueprint('user', __name__)

@user_bp.route("/users", methods=["GET"])
@login_required
def list_users():
    """
    列出所有用户
    """
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([
        {
            "id": u.id,
            "username": u.username,
            "email": u.email
        } for u in users
    ]), 200


@user_bp.route("/users", methods=["POST"])
@login_required
def create_user():
    """
    新增用户
    """
    data = request.get_json() or {}
    print("data:",data)
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")
    role = role.lower()

    if not all([username, email, password, role]):
        return jsonify({"message": "缺少必要参数"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "用户名已存在"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "邮箱已存在"}), 400

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value
    }), 201


@user_bp.route("/users/<int:user_id>", methods=["PUT"])
@login_required
def update_user(user_id):
    """
    更新用户信息
    """
    user = User.query.get(user_id)
    print("user:",user)
    if not user:
        return jsonify({"message": "用户不存在"}), 404

    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")

    print(username,email)

    db.session.commit()
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value
    }), 200


@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
@login_required
def delete_user(user_id):
    """
    删除用户，同时级联删除对应的 Employee 记录
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "用户不存在"}), 404

    # 先删除与该用户关联的员工记录
    employee = Employee.query.filter_by(user_id=user_id).first()
    if employee:
        db.session.delete(employee)

    # 再删除用户
    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "删除成功"}), 200