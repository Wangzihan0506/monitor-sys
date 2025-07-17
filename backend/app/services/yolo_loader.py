import torch
from flask import current_app


class YoloDetectorService:
    """
    一个封装了本地 YOLOv5 姿态估计模型的服务类。
    采用单例模式，延迟加载。
    """
    _instance = None
    model = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(YoloDetectorService, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def init_app(self, app):
        with app.app_context():
            if self.model is None:
                print("【AI服务】正在初始化本地 YOLOv5 Pose 模型...")
                try:
                    repo_path = current_app.config['YOLO_REPO_PATH']
                    weights_path = current_app.config['POSE_MODEL_WEIGHTS_PATH']

                    print(f"  > 源码路径: {repo_path}")
                    print(f"  > 权重路径: {weights_path}")

                    # 使用 torch.hub.load 加载本地模型
                    # source='local' 是关键，它告诉 torch 在 repo_path 里找模型定义
                    self.model = torch.hub.load(repo_path, 'custom', path=weights_path, source='local')

                    # 你可以设置一些模型的默认参数
                    self.model.conf = 0.5  # 置信度阈值
                    self.model.iou = 0.45  # IOU 阈值

                    print("【AI服务】本地 YOLOv5 Pose 模型加载成功！")
                except Exception as e:
                    print(f"【AI服务】错误：本地 YOLOv5 Pose 模型加载失败: {e}")
                    self.model = None

    def detect(self, image_rgb):
        """
        对单张图片进行姿态估计。
        :param image_rgb: RGB 格式的图像 (numpy array)
        :return: YOLOv5 的 results 对象
        """
        if self.model is None:
            raise RuntimeError("YoloDetectorService 未初始化或模型加载失败。")

        # 直接调用模型进行推理
        return self.model(image_rgb)


# 创建一个全局的单例实例
yolo_detector = YoloDetectorService()