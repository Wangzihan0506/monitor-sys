# backend/app/apis/abnormal_detection.py
from datetime import datetime
import os
import torch
import base64
import cv2
import numpy as np
import uuid
import yaml # 导入 yaml 库
from flask import Blueprint, request, jsonify, current_app
from ultralytics import YOLO
from flask import g
from app.decorators import token_required
from app.models.alert import Alert
from app.exts import db

# 检测模型路径
YOLO_REPO_PATH = r'C:\Users\Tsuki\Desktop\practice\project\yolo'

#姿态
POSE_WEIGHTS_PATH = r'C:\Users\Tsuki\Desktop\practice\project\yolo\runs\train\exp\weights\best.pt'
DATA_YAML_PATH = r'C:\Users\Tsuki\Desktop\practice\project\yolo\data\fall.yaml'

# #火灾
# FIRE_WEIGHTS_PATH = os.path.join(YOLO_REPO_PATH, 'best.pt')
# FIRE_DATA_YAML_PATH= r'C:\Users\Tsuki\Desktop\practice\project\yolov5-fire-main/data/fire_data.yaml'

abnormal_detection_bp = Blueprint("abnormal_detection", __name__)

#加在姿态检测模型
pose_model = None
pose_class_names = []
try:
    print("加载本地姿态识别模型...")
    # 检查文件是否存在
    if not os.path.exists(POSE_WEIGHTS_PATH) or not os.path.exists(DATA_YAML_PATH):
        raise FileNotFoundError("姿态检测模型的权重文件或 data.yaml 路径不正确！")
    # 加载模型
    pose_model = torch.hub.load(YOLO_REPO_PATH, 'custom', path=POSE_WEIGHTS_PATH, source='local')
    pose_model.conf = 0.35  # 设置置信度
    # 加载并解析 data.yaml 文件以获取类别名称
    with open(DATA_YAML_PATH, 'r', encoding='utf-8') as f:
        data_yaml = yaml.safe_load(f)
        pose_class_names = data_yaml['names']
    print(f"模型加载成功！识别类别: {pose_class_names}")
except Exception as e:
    print(f"错误：模型加载失败: {e}")

#加载【YOLOv8】模型 (用于火焰等通用物体检测) ---
fire_model = None
try:
    print("【YOLOv8】加载通用目标检测模型 (yolov8n.pt)...")
    # 这会自动下载官方的、能识别80种物体的标准模型
    fire_weights_path = r'C:\Users\Tsuki\Desktop\practice\project\backend\app\services\best.pt'
    fire_model = YOLO(fire_weights_path)
    fire_model.config=0.8
    print("【YOLOv8】通用模型加载成功！")
except Exception as e:
    print(f"【YOLOv8】错误：通用模型加载失败: {e}")

abnormal_detection_bp = Blueprint("abnormal_detection", __name__)

# API 端点
@abnormal_detection_bp.route('/detection', methods=['POST'])
@token_required
def abnormal_detection_endpoint():
    if pose_model is None:
        return jsonify(code=-1, msg="异常检测服务当前不可用，模型加载失败"), 503

    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify(code=1, msg='No image provided'), 400

        # --- 1. 解码并保存临时图片 ---
        image_data = data['image'].split(',', 1)[1]
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        save_dir = os.path.join(current_app.static_folder, 'alert_captures')
        os.makedirs(save_dir, exist_ok=True)
        timestamp_folder_name = datetime.now().strftime('%Y%m%d%H%M%S')
        frame_saved = False
        frame_path_for_db = None

        if img_bgr is None: return jsonify(code=1, msg='Failed to decode image'), 400
        image_height, image_width, _ = img_bgr.shape

        events_to_add = []

        if pose_model and pose_class_names:
            pose_results = pose_model(img_bgr)

            # --- 直接从结果中读取类别，不再需要复杂的姿态计算 ---
            predictions = pose_results.pred[0]
            final_results = []
            for det in predictions:
                box = det[:4].tolist()
                confidence = det[4].item()
                class_id = int(det[5].item())

                # 【核心】直接用 class_id 从列表-中查找姿态名称
                if 0 <= class_id < len(pose_class_names):
                    pose_name = pose_class_names[class_id]
                else:
                    pose_name = "unknown"

                final_results.append({
                    "box": box,
                    "pose": pose_name,
                    "confidence": confidence
                })

                if pose_name in ['fall', 'run']:
                    # 1. 保存截图
                    if not frame_saved:
                        filename = f"{timestamp_folder_name}_{uuid.uuid4().hex[:6]}.jpg"
                        full_path = os.path.join(save_dir, filename)
                        cv2.imwrite(full_path, img_bgr)
                        frame_path_for_db = os.path.join('alert_captures', filename).replace('\\', '/')
                        frame_saved = True

                    # 2. 创建一个 Alert 实例
                    new_alert = Alert(
                        message=f"检测到异常行为: {pose_name.upper()}",  # 告警信息
                        person_box=str(box),  # 使用 person_box 字段存储坐标
                        frame_path=frame_path_for_db
                        # 其他字段如 timestamp, is_handled 会使用默认值
                    )
                    events_to_add.append(new_alert)

        # === 推理 2：火焰检测 (使用 YOLOv8) ===
        if fire_model:
            print(f"火焰模型在检测了")
            # 使用新的 fire_model 进行推理
            fire_results = fire_model(img_bgr, conf=0.4, verbose=False)
            if fire_results and len(fire_results) > 0:
                print(f"火焰检测有结果")
                print(f"--- 火焰模型原始输出 (共 {len(fire_results[0].boxes)} 个检测框) ---")
                for box_data in fire_results[0].boxes:
                    current_app.logger.info(
                        f"  - 火焰检测框: class_id={int(box_data.cls)}, name={fire_model.names[int(box_data.cls)]}, "
                        f"conf={box_data.conf.item():.2f}, box={box_data.xyxy[0].tolist()}"
                    )
                print("----------------------------------------------------")
                for box_data in fire_results[0].boxes:
                    # 我们现在可以自信地假设，这个模型检测到的任何东西都是火焰
                    # 最好还是通过 class_id 来判断，以防万一

                    class_id = int(box_data.cls)
                    # 假设 fire_model.names 的结果是 {0: 'fire'}
                    if fire_model.names[class_id] =='Fire':
                        box = box_data.xyxy[0].tolist()
                        confidence = box_data.conf.item()
                        final_results.append({
                            "box": box, "pose": "fire", "confidence": confidence
                        })
                        current_app.logger.warning(f"【火焰告警】检测到明火! 置信度: {confidence:.2f}")
                        # 1. 保存截图 (如果需要)
                        if not frame_saved:
                            filename = f"{timestamp_folder_name}_{uuid.uuid4().hex[:6]}.jpg"
                            full_path = os.path.join(save_dir, filename)
                            cv2.imwrite(full_path, img_bgr)
                            frame_path_for_db = os.path.join('alert_captures', filename).replace('\\', '/')
                            frame_saved = True

                        # 2. 创建另一个 Alert 实例
                        new_alert = Alert(
                            message="【严重】检测到明火!",  # 告警信息
                            person_box=str(box),  # 我们复用 person_box 字段来存火焰的框
                            frame_path=frame_path_for_db
                        )
                        events_to_add.append(new_alert)

                        # 在日志中依然可以高亮告警
                        current_app.logger.warning(f"【火焰告警】检测到明火! 置信度: {box_data.conf.item():.2f}")

        if events_to_add:
            db.session.add_all(events_to_add)  # 使用 add_all 批量添加
            db.session.commit()
            print(f"成功将 {len(events_to_add)} 条告警记录写入数据库。")

        return jsonify({
            "code": 0, "msg": f"检测完成，识别到 {len(final_results)} 个对象。",
            "data": {"persons": final_results}  # 保持这个字段名，以免前端还要改
        })

    except Exception as e:
        current_app.logger.error(f"异常检测接口发生错误: {e}", exc_info=True)
        return jsonify(code=-1, msg='服务器内部错误'), 500