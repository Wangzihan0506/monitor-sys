from flask import Blueprint, jsonify, request
from sqlalchemy import union_all, literal_column

from app.models.alert import Alert
from app.models.abnormalEvent import AbnormalEvent
from app.exts import db
from datetime import datetime

alert_bp = Blueprint("alert", __name__)

# 查询所有告警（常规 + 异常行为）
@alert_bp.route('/alerts', methods=['GET'])
def list_alerts():
    """
    分页、全局排序地获取所有类型的告警
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('size', 10, type=int)
        is_handled_str = request.args.get('is_handled')
    except (TypeError, ValueError):
        return jsonify(success=False, message="参数无效"), 400

    # 【核心修正】为每一个需要用到的列都加上 .label()
    # 查询1：常规告警 (Alert)
    q1 = db.session.query(
        Alert.id.label("id"),
        literal_column("'normal'").label("type"),
        Alert.message.label("message"),
        Alert.timestamp.label("timestamp"),  # <-- 加上 .label()
        Alert.frame_path.label("frame_path"),
        Alert.person_box.label("box"),
        Alert.is_handled.label("is_handled"),
        Alert.handle_result.label("handle_result")
    )

    # 查询2：异常行为告警 (AbnormalEvent)
    q2 = db.session.query(
        AbnormalEvent.id.label("id"),
        literal_column("'abnormal'").label("type"),
        AbnormalEvent.label.label("message"),
        AbnormalEvent.timestamp.label("timestamp"),  # <-- 加上 .label()
        AbnormalEvent.frame_path.label("frame_path"),
        AbnormalEvent.box.label("box"),
        AbnormalEvent.is_handled.label("is_handled"),
        AbnormalEvent.handle_result.label("handle_result")
    )

    # 应用过滤条件
    if is_handled_str is not None:
        handled_bool = is_handled_str.lower() == 'true'
        q1 = q1.filter(Alert.is_handled == handled_bool)
        q2 = q2.filter(AbnormalEvent.is_handled == handled_bool)

    # 合并查询
    combined_query = union_all(q1, q2).subquery()

    # 现在 .order_by(combined_query.c.timestamp.desc()) 就可以正常工作了！
    final_query = db.session.query(combined_query).order_by(combined_query.c.timestamp.desc())

    total_count = final_query.count()
    paginated_alerts = final_query.offset((page - 1) * per_page).limit(per_page).all()

    # 序列化结果
    serialized_alerts = [
        {
            'id': a.id,
            'type': a.type,
            'message': a.message,
            'timestamp': a.timestamp.strftime('%Y-%m-%d %H:%M:%S') if a.timestamp else None,
            'frame_path': a.frame_path,
            'box': a.box,
            'is_handled': a.is_handled,
            'handle_result': a.handle_result
        } for a in paginated_alerts
    ]

    # 返回正确的 JSON 结构
    return jsonify({
        "success": True,
        "message": "告警列表获取成功",
        "data": {
            "items": serialized_alerts,
            "page": page,
            "per_page": per_page,
            "total": total_count,
            "pages": (total_count + per_page - 1) // per_page if per_page > 0 else 0
        }
    })


# 获取某条告警（常规 or 异常）
@alert_bp.route('/api/alerts/<string:alert_type>/<int:alert_id>', methods=['GET'])
def get_alert(alert_type, alert_id):
    if alert_type == 'normal':
        alert = Alert.query.get_or_404(alert_id)
    elif alert_type == 'abnormal':
        alert = AbnormalEvent.query.get_or_404(alert_id)
    else:
        return jsonify({'code': 1, 'msg': '未知类型'}), 400

    return jsonify({
        'code': 0,
        'alert': {
            'id': alert.id,
            'type': alert_type,
            'message': alert.message if alert_type == 'normal' else f"异常行为：{alert.label}",
            'person_box': alert.person_box if alert_type == 'normal' else alert.box,
            'frame_path': alert.frame_path,
            'timestamp': alert.timestamp,
            'is_handled': alert.is_handled,
            'handle_result': alert.handle_result,
            'handled_time': alert.handled_time
        }
    })


# 处理告警（通用接口）
@alert_bp.route('/api/alerts/<string:alert_type>/<int:alert_id>/handle', methods=['POST'])
def handle_alert(alert_type, alert_id):
    data = request.get_json()
    result = data.get('handle_result', '')

    if alert_type == 'normal':
        alert = Alert.query.get_or_404(alert_id)
    elif alert_type == 'abnormal':
        alert = AbnormalEvent.query.get_or_404(alert_id)
    else:
        return jsonify({'code': 1, 'msg': '未知类型'}), 400

    alert.is_handled = True
    alert.handle_result = result
    alert.handled_time = datetime.utcnow()
    db.session.commit()

    return jsonify({'code': 0, 'msg': '处理完成'})


# 清空告警（可选接口）
@alert_bp.route('/api/alerts/clear', methods=['POST'])
def clear_alerts():
    Alert.query.delete()
    AbnormalEvent.query.delete()
    db.session.commit()
    return jsonify({'code': 0, 'msg': '已清空所有告警数据'})