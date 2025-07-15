from app.exts import db
from datetime import datetime

class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.String(255))  # 告警信息
    message = db.Column(db.String(255), nullable=False)  # 告警信息
    person_box = db.Column(db.String(255), nullable=False)  # 人员框坐标（json字符串）
    frame_path = db.Column(db.String(255))  # 截图保存路径
    video_clip = db.Column(db.String(255))  # 可选：视频片段路径
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # 告警时间

    is_handled = db.Column(db.Boolean, default=False)  #是否已处理
    handle_result = db.Column(db.String(255))  # 处理意见
    handled_time = db.Column(db.DateTime)  # 处理时间

    def __repr__(self):
        return f"<Alert id={self.id} zone_id={self.zone_id} msg={self.message}>"