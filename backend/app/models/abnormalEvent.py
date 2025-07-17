from app.exts import db
from datetime import datetime

class AbnormalEvent(db.Model):
    __tablename__ = 'abnormal_events'

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(64), nullable=False)  # 异常类型（如：摔倒、抽烟）
    box = db.Column(db.String(255), nullable=False)  # 检测框坐标（JSON 字符串）
    frame_path = db.Column(db.String(255), nullable=False)  # 截图路径
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # 识别时间

    is_handled = db.Column(db.Boolean, default=False)  # 是否处理
    handle_result = db.Column(db.String(255))  # 处理意见
    handled_time = db.Column(db.DateTime)  # 处理时间

    def __repr__(self):
        return f"<AbnormalEvent id={self.id} label={self.label} path={self.frame_path}>"