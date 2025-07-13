# TODO: 这里原本用于生成假行为记录，后续请接入真实后端行为识别逻辑。
# 真实行为识别数据结构示例：
# behavior_record = {
#     'id': int,                # 行为记录唯一ID
#     'employee_id': int,      # 员工ID
#     'employee_name': str,    # 员工姓名
#     'behavior': str,         # 行为类型，如 'EATING'/'DRINKING'/'SLEEP'/'PHONE'/'NOTWORKING'/'NORMAL'
#     'timestamp': datetime,   # 行为发生时间
#     'image': str,            # 可选，行为发生时的图片base64或url
#     'video': str,            # 可选，行为发生时的视频url
#     'confidence': float      # 可选，识别置信度
# }