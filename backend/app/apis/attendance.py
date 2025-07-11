#考勤相关接口
import base64
import datetime

import numpy as np
from flask import (
    make_response, jsonify, request, current_app, Blueprint
)
from io import BytesIO
from PIL import Image
import requests

from app.apis.behavior import recognize_face
from app.models.employee import Attendance, CheckTypeEnum, Employee
from flask_login import login_required,current_user

from app.exts import db

attend_bp = Blueprint('attend_bp',__name__)

@attend_bp.route('attendance/checkin/', methods=['POST'], strict_slashes=False)
def checkin():
    data = request.get_json() or {}
    image_data = data.get('image')
    latitude = data.get('latitude',None)
    longitude = data.get('longitude',None)
    # check_type = data.get("check_type","self")

    if not image_data:
        return jsonify({'message': '缺少图像数据'}), 400

    # 解码 Base64 图像
    try:
        header, encoded = image_data.split(',', 1)
        img_bytes = base64.b64decode(encoded)
    except Exception:
        return jsonify({'message': '图像解码失败'}), 400

    try:
        image = Image.open(BytesIO(img_bytes)).convert('RGB')
    except Exception:
        return jsonify({'message': '无法读取图像'}), 400

    # 转为 numpy 数组
    image_np = np.array(image)

    # 人脸识别
    emp_id = recognize_face(image_np)
    if not emp_id:
        return jsonify({'message': '识别不到人脸或未注册'}), 404

    employee = Employee.query.get(emp_id)
    if not employee:
        return jsonify({'message': '员工不存在'}), 404

    # 记录签到
    # sign_time = datetime.utcnow()
    import pytz
    tz = pytz.timezone("Asia/Shanghai")
    sign_time = datetime.now(tz)
    attendance = Attendance(
        employee_id=employee.id,
        sign_time=sign_time,
        latitude=latitude,
        longitude=longitude

    )
    db.session.add(attendance)
    db.session.commit()

    return jsonify({
        'employeeName': employee.name,
        'signTime': sign_time.strftime('%Y-%m-%d %H:%M:%S')
    }), 200


@attend_bp.route('/attendance/records', methods=['GET'])
def get_attendance_records():
    """
    返回所有签到记录，包含员工姓名、签到时间和地址描述。
    """
    # 1. 拉取所有记录，按时间倒序
    records = Attendance.query.order_by(Attendance.sign_time.desc()).all()

    # 2. 获取百度地图逆地理编码的 AK（需在配置中设置）
    ak = current_app.config.get('BAIDU_MAP_AK', None)

    result = []
    for rec in records:
        lat = rec.latitude
        lng = rec.longitude
        address = None

        # 3. 调用百度地图逆地理编码（仅当 lat/lng 不为 None 时）
        if ak and lat is not None and lng is not None:
            try:
                resp = requests.get(
                    'http://api.map.baidu.com/reverse_geocoding/v3/',
                    params={
                        'ak': ak,
                        'output': 'json',
                        'coordtype': 'wgs84ll',
                        'location': f'{lat},{lng}'
                    },
                    timeout=3
                )
                data = resp.json()
                if data.get('status') == 0:
                    comp = data['result'].get('addressComponent', {})
                    street = data['result'].get('sematic_description')
                    if street:
                        address = street
                    else:
                        address = data['result'].get('formatted_address') or comp.get('district')
            except Exception:
                # 网络或解析异常，忽略，后面有 fallback
                address = None

        # 4. fallback：如果没有拿到地址，再根据坐标或直接标记未知
        if not address:
            if lat is not None and lng is not None:
                address = f"经度:{lng:.6f}, 纬度:{lat:.6f}"
            else:
                address = "地址未知"

        result.append({
            'employeeName': rec.employee.name,
            'signTime': rec.sign_time.strftime('%Y-%m-%d %H:%M:%S'),
            'address': address,
            "check_type":rec.check_type.value
        })

    return jsonify(result), 200

@attend_bp.route('/attendance/records/user', methods=['GET'])
@login_required
def get_user_attendance_records():
    """
    获取当前登录用户的签到历史（分页），返回字段：
    - records: [{ employeeName, signTime, address }, ...]
    - total: 总记录数
    - page: 当前页码
    """
    # 1. 从请求中获取分页参数
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
    except (ValueError, TypeError):
        return jsonify({'message': '分页参数必须为整数'}), 400

    # 2. 获取当前用户对应的员工记录
    emp = getattr(current_user, 'employee', None)
    if not emp:
        return jsonify({'message': '未找到对应的员工信息'}), 404

    # 3. 构造查询并分页（按签到时间倒序）
    pagination = (
        Attendance.query
        .filter_by(employee_id=emp.id)
        .order_by(Attendance.sign_time.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    ak = current_app.config.get('BAIDU_MAP_AK', None)
    records = []

    for rec in pagination.items:
        # 4. 逆地理编码获取地址
        address = None
        if ak and rec.latitude is not None and rec.longitude is not None:
            try:
                resp = requests.get(
                    'http://api.map.baidu.com/reverse_geocoding/v3/',
                    params={
                        'ak': ak,
                        'output': 'json',
                        'coordtype': 'wgs84ll',
                        'location': f'{rec.latitude},{rec.longitude}'
                    },
                    timeout=3
                ).json()
                if resp.get('status') == 0:
                    street = resp['result'].get('sematic_description')
                    comp = resp['result'].get('addressComponent', {})
                    address = street or resp['result'].get('formatted_address') or comp.get('district')
            except Exception:
                address = None

        # 5. fallback：若无地址，则显示经纬度。如果经纬度本身为空，显示未知
        if not address:
            if rec.latitude is not None and rec.longitude is not None:
                address = f"经度:{rec.longitude:.6f}, 纬度:{rec.latitude:.6f}"
            else:
                address = "经度:未知, 纬度:未知"

        records.append({
            'employeeName': rec.employee.name,
            'signTime': rec.sign_time.strftime('%Y-%m-%d %H:%M:%S'),
            'address': address
        })

    # 6. 返回 JSON，多返回当前页（page）方便前端展示
    return jsonify({
        'records': records,
        'total': pagination.total,
        'page': pagination.page
    }), 200




@attend_bp.route('/attendance/makeup', methods=['OPTIONS', 'POST'])
def attendance_makeup():
    # CORS 预检
    if request.method == 'OPTIONS':
        resp = make_response('', 204)
        resp.headers.update({
            'Access-Control-Allow-Origin': request.headers.get('Origin', '*'),
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        })
        return resp

    data = request.get_json(force=True) or {}
    user_id = data.get('userId')
    date_str = data.get('date')


    if not user_id or not date_str:
        return jsonify({'message': '参数不完整（需要 userId 和 date）'}), 400

    # 解析日期
    sign_time = None
    for fmt in (
        '%Y-%m-%d',                    # 仅日期
        '%Y-%m-%dT%H:%M:%S.%fZ',       # 带毫秒 + Z
        '%Y-%m-%dT%H:%M:%S.%f',        # 带毫秒
        '%Y-%m-%dT%H:%M:%S'            # 不带毫秒
    ):
        try:
            sign_time = datetime.strptime(date_str, fmt)
            break
        except ValueError:
            continue

    # 如果上面都没匹配，再尝试 strip Z 后用 fromisoformat
    if sign_time is None:
        try:
            ds = date_str.rstrip('Z')
            sign_time = datetime.fromisoformat(ds)
        except ValueError:
            return jsonify({'message': f'无法解析的日期格式: {date_str}'}), 400

    # 写入数据库
    try:
        makeup = Attendance(
            employee_id=user_id,
            sign_time=sign_time,
            latitude=None,
            longitude=None,
            check_type = CheckTypeEnum.ADMIN
        )
        db.session.add(makeup)
        db.session.commit()
        return jsonify({'message': '补签成功'}), 200

    except Exception as e:
        current_app.logger.error(f"补签失败：{e}")
        db.session.rollback()
        return jsonify({'message': '服务器内部错误，补签失败'}), 500