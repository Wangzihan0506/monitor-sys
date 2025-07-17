#用户管理接口
from flask import Blueprint, jsonify, request,g,current_app
from flask_login import login_required, current_user
from app.exts import db
from app.models.user import User         # 直接从 app.models.user 导入 User
from app.models.employee import Employee # 直接从 app.models.employee 导入 Employee
from app.decorators import token_required

user_bp = Blueprint('user', __name__)

def user_to_dict(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None
    }


@user_bp.route("/users", methods=["GET"])
@token_required
def list_users():
    """
    列出所有用户 (【已添加分页】)
    """
    current_app.logger.info("--- [API] 开始获取用户列表 ---")

    # 【调试点1】确认当前用户 (现在应该有值了)
    current_app.logger.info(f"[DEBUG] 当前用户已认证: {g.current_user.username}e")

    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('size', 10, type=int)

        users_query = User.query.order_by(User.created_at.desc())

        total_users = users_query.count()
        paginated_users = users_query.offset((page - 1) * per_page).limit(per_page).all()

        serialized_users = [user_to_dict(u) for u in paginated_users]

        return jsonify({
            "code": 0,  # 统一 code 格式
            "msg": "用户列表获取成功",  # 统一 msg 格式
            "data": {
                "items": serialized_users,
                "page": page,
                "per_page": per_page,
                "total": total_users,
                "pages": (total_users + per_page - 1) // per_page if per_page > 0 else 0
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取用户列表时发生错误: {e}", exc_info=True)
        return jsonify(code=-1, msg='服务器内部错误'), 500

@user_bp.route("/users", methods=["POST"])
@token_required
def create_user():
    """
    新增用户
    """
    data = request.get_json() or {}
    print("data:",data)
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not all([username, email, password]):
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
    }), 201


@user_bp.route("/users/<int:user_id>", methods=["PUT"])
@token_required
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

    }), 200


@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
@token_required
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

@user_bp.route("/current_user/", methods=["GET"])
@token_required  # 这个装饰器确保了只有登录用户才能访问
def get_current_user_info():
    """
    获取当前已登录用户的信息 (【已修复】使用 g.current_user)
    """
    # 【关键修复】使用 g.current_user
    if not g.current_user:
        current_app.logger.warning("获取当前用户信息失败：g.current_user 为空。")
        return jsonify(code=1, msg="用户未登录或认证失败"), 401

    return jsonify({
        "code": 0, # 统一 code 格式
        "msg": "当前用户信息获取成功", # 统一 msg 格式
        "data": user_to_dict(g.current_user) # 使用辅助函数序列化当前用户
    }), 200