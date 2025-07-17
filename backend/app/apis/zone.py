# from flask import Blueprint, request, jsonify
# import json
#
# zone_bp = Blueprint("zone", __name__)
#
# # 存储危险区域数据（可改为存数据库）
# danger_zones = {}
#
# @zone_bp.route('/api/set_danger_zone', methods=['POST'])
# def set_danger_zone():
#     data = request.json
#     zone_id = data.get('zone_id')
#     polygon = data.get('polygon')  # 例如：[(x1,y1), (x2,y2), ...]
#     safe_distance = data.get('safe_distance', 50)  # 默认50像素或cm
#     max_stay = data.get('max_stay', 3)  # 停留时间，单位秒
#     danger_zones[zone_id] = {
#         'polygon': polygon,
#         'safe_distance': safe_distance,
#         'max_stay': max_stay
#     }
#     return jsonify({"msg": "设置成功", "code": 0})