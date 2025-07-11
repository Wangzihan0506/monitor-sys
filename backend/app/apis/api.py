from flask import (
    Blueprint,make_response,jsonify,request,current_app
)

import random



api_bp = Blueprint(
    "api", __name__, url_prefix="/api/"
    )


# @api_bp.route('/attendance/dection/', methods=['POST'])
# @login_required
# def attendance_detection():
#     """
#     接收前端定时上传的 base64 编码截图，解码为图像后进行相应的处理（如行为检测、存储等），
#     最后返回 JSON 格式的检测结果或状态。
#     """
#     try:
#         data = request.get_json()
#         if not data or 'image' not in data:
#             return jsonify({'error': 'No image provided'}), 400

#         image_data = data['image']
#         # 前端发送的 image 格式类似 "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABA..."
#         # 先去掉 "data:image/jpeg;base64," 这部分
#         if ',' in image_data:
#             header, encoded = image_data.split(',', 1)
#         else:
#             encoded = image_data

#         # 将 Base64 字符串解码为二进制
#         try:
#             img_bytes = base64.b64decode(encoded)
#         except Exception as e:
#             return jsonify({'error': 'Invalid base64 data', 'detail': str(e)}), 400

#         # 转换为 NumPy 数组，再通过 OpenCV 解码为图像
#         nparr = np.frombuffer(img_bytes, dtype=np.uint8)
#         img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
#         if img is None:
#             return jsonify({'error': 'Failed to decode image'}), 400

#         # save_dir = os.path.join(os.getcwd(), 'local_images')

#         save_dir = os.path.join(current_app.root_path, 'local_images')

#         os.makedirs(save_dir, exist_ok=True)
#         now = datetime.now()
#         timestamp = now.strftime("%Y%m%d%H%M%S")
#         img_filename = os.path.join(save_dir, f"{timestamp}.jpg")
    
#         success = cv2.imwrite(img_filename, img)
#         print(f"[DEBUG] cv2.imwrite 返回：{success}, 保存路径：{img_filename}")


#         # 2. TODO: 在这里调用你的行为检测模型，假设模型返回一个 dict 结果
#         #    比如： result = run_behavior_model(img)
#         #    下面我们先模拟一个假检测结果
#         result = {
#             'behavior': 'normal',       # 示例：检测到的行为
#             'confidence': 0.92,         # 示例：模型置信度
#             'timestamp': int(np.floor(cv2.getTickCount() / cv2.getTickFrequency()))
#         }

#         # 3. 将检测结果返回给前端
#         return jsonify({
#             'status': 'success',
#             'data': result
#         }), 200

#     except Exception as e:
#         # 捕获任意异常并返回 500
#         return jsonify({'error': 'Internal Server Error', 'detail': str(e)}), 500




    
# @api_bp.route("/attendance/makeup", methods=["POST"])
# @login_required
# def makeup_attendance():
#     """
#     给指定用户在指定时间补签
#     """
#     data = request.get_json() or {}
#     user_id = data.get("userId")
#     date_str = data.get("date")

#     if not all([user_id, date_str]):
#         return jsonify({"message": "缺少参数"}), 400

#     try:
#         sign_time = datetime.fromisoformat(date_str)
#     except ValueError:
#         return jsonify({"message": "日期格式错误，应为 ISO 格式"}), 400

#     # 直接按 employee_id 补签
#     employee = Employee.query.get(user_id)
#     if not employee:
#         return jsonify({"message": "用户不存在"}), 404

#     attendance = Attendance(employee_id=user_id, sign_time=sign_time)
#     db.session.add(attendance)
#     db.session.commit()

#     return jsonify({"message": "补签成功"}), 200

