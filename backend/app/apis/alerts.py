from flask import Blueprint, jsonify, request
from app.models.alert import Alert
from app.models.abnormal_event import AbnormalEvent
from app.exts import db
from datetime import datetime

alert_bp = Blueprint("alert", __name__)

# 查询所有告警（常规 + 异常行为）
@alert_bp.route('/api/alerts', methods=['GET'])
def list_alerts():
    is_handled = request.args.get('is_handled')
    query1 = Alert.query
    query2 = AbnormalEvent.query

    if is_handled is not None:
        handled = is_handled.lower() == 'true'
        query1 = query1.filter_by(is_handled=handled)
        query2 = query2.filter_by(is_handled=handled)

    alert_list = [
        {
            'id': a.id,
            'type': 'normal',
            'zone_id': a.zone_id,
            'message': a.message,
            'person_box': a.person_box,
            'frame_path': a.frame_path,
            'timestamp': a.timestamp,
            'is_handled': a.is_handled,
            'handle_result': a.handle_result,
            'handled_time': a.handled_time
        }
        for a in query1.order_by(Alert.timestamp.desc()).all()
    ] + [
        {
            'id': a.id,
            'type': 'abnormal',
            'zone_id': 'abnormal',
            'message': f"异常行为：{a.label}",
            'person_box': a.box,
            'frame_path': a.frame_path,
            'timestamp': a.timestamp,
            'is_handled': a.is_handled,
            'handle_result': a.handle_result,
            'handled_time': a.handled_time
        }
        for a in query2.order_by(AbnormalEvent.timestamp.desc()).all()
    ]

    return jsonify({'code': 0, 'alerts': alert_list})


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
