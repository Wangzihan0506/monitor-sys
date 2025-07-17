# 📺 餐厅安全监测系统  
基于 Flask + Vue3 的企业级监控解决方案，支持人脸识别、行为分析和异常事件报警 🚨   

## 📖目录
##### 💻 项目架构   🚀 快速开始
##### 🎯 核心功能   🔧 环境配置
##### 🎮 系统操作   📡 推流设置
##### 🐛 常见问题   🤝 贡献指南

## 💻 项目架构
```
.
├── backend/                     # 后端项目目录
│   ├── app/                     # 应用程序目录
│   │   ├── apis/                # API相关模块
│   │   │   ├── __init__.py            
│   │   │   ├── alerts.py
│   │   │   ├── api.py
│   │   │   ├── attendance.py
│   │   │   ├── auth.py
│   │   │   ├── behavior.py
│   │   │   ├── face_recognition.py
│   │   │   ├── faceEnrollandLogin.py
│   │   │   ├── main.py
│   │   │   ├── monitor.py
│   │   │   ├── user.py
│   │   │   └── zone.py
│   │   ├── forms/               # 表单相关模块
│   │   │   └── __init__.py
│   │   └── models/             # 数据模型模块
│   │       ├── __init__.py
│   │       ├── abnormalEvent.py
│   │       ├── alert.py
│   │       ├── employee.py
│   │       ├── user.py
│   │       └── exts.py
│   ├── cv2_data/                # OpenCV数据目录
│   ├── images/                  # 图片目录
│   ├── migrations/              # 数据库迁移目录
│   ├── node_modules/            # Node.js模块目录
│   ├── sql/                     # SQL脚本目录
│   ├── static/                  # 静态文件目录
│   ├── temp_images/             # 临时图片目录
│   ├── test/                    # 测试目录
│   ├── utils/                   # 工具函数目录
│   │   ├── add_employees.py
│   │   ├── app.py
│   │   ├── config.ini
│   │   ├── config.py
│   │   └── diag.py
│   └── config.ini               # 配置文件
├── front-vue3/                 # 前端Vue3项目目录
│   ├── node_modules/            # Node.js模块目录
│   ├── public/                  # 公共资源目录
│   ├── src/                     # 源代码目录
│   │   ├── api/                 # API接口目录
│   │   │   └── user/            # 用户相关API
│   │   │       └── index.js
│   │   ├── assets/             # 资源文件目录
│   │   ├── components/          # 组件目录
│   │   ├── router/              # 路由配置目录
│   │   ├── stores/             # 状态管理目录
│   │   ├── utils/              # 工具函数目录
│   │   ├── views/              # 视图组件目录
│   │   │   ├── admin/           # 管理页面组件
│   │   │   │   └── AdminIndex.vue
│   │   │   ├── face/           # 人脸识别页面组件
│   │   │   │   ├── FaceEnroll.vue
│   │   │   │   └── FaceLogin.vue
│   │   │   └── home/          # 首页组件
│   │   │       └── HomeIndex.vue
│   ├── .eslintrc.cjs            # ESLint配置文件
│   ├── .gitignore               # Git忽略文件配置
│   ├── .npmrc                  # NPM配置文件
│   ├── babel.config.js          # Babel配置文件
│   ├── jsconfig.json            # JavaScript配置文件
│   ├── package.json             # 项目依赖配置文件
│   ├── package-lock.json        # 项目依赖锁定文件
│   ├── README.md                # 项目说明文件
│   └── yolov8n.pt               # YOLOv8模型文件
└── login/                      # 登录相关组件目录
    ├── LoginIndex.vue           # 登录页面组件
    ├── register/                # 注册相关组件目录
    │   └── RegisterIndex.vue    # 注册页面组件
    └── welcome/                 # 欢迎页面组件目录
        ├── App.vue              # 应用根组件
        ├── main.ts              # 主入口文件
        └── settings.js          # 设置文件
```
## 🚀 快速开始
#### 前端部署 （front-vue3）  
```
#安装依赖
pnpm install

#开发环境
pnpm run serve

#生产环境
pnpm run build
```
#### 后端部署
```
# 创建虚拟环境
conda create -n flask-py310 python=3.10
conda activate flask-py310

# 安装依赖
conda install -c conda-forge cmake dlib
pip install -r backend/requirements.txt

# 数据库迁移
cd backend
flask db init          # 首次初始化
flask db migrate -m "更新描述"  # 模型变更后
flask db upgrade       # 应用到数据库

# 启动服务
python app.py
```

#### lints 和修复文件
```
pnpm run lint
```

#### 自定义配置
See [Configuration Reference](https://cli.vuejs.org/config/).

数据库更新后需要迁移更新
进入后端目录
cd backend 

###### 只做一次：初始化迁移环境
flask db init

###### 每次模型变化后执行（生成版本脚本）
flask db migrate -m "更新描述"

###### 应用到数据库
flask db upgrade


## 🎯 核心功能
#### 👤 人脸识别
通过 /api/face_enroll/ API 录入人脸数据
```
import requests
import base64

# 准备数据
with open("face.jpg", "rb") as f:
    img_data = base64.b64encode(f.read()).decode()

data = {
    "username": "张三",
    "image": img_data
}

# 发送请求
response = requests.post(
    "http://localhost:5000/api/face_enroll/",
    json=data
)

print(response.json())
```
#### 📊 行为分析
1.员工在岗状态实时监控
2.异常行为自动识别报警
3.历史数据统计与报表生成

#### 🚪 区域监控
自定义监控区域，配置敏感行为规则：
```
// ZoneMonitor.vue
const monitorRules = [
    { zoneId: "A1", action: "loitering", threshold: 30 }, // 徘徊超过30秒
    { zoneId: "B2", action: "intrusion", alert: true }    // 非法闯入
]
```
## 🔧 环境配置
#### 🔌 数据库设置
编辑 backend/config.ini：
```
[mysql]
user = root
password = your_password
host = localhost
port = 3307
database = detection
```
#### 🛠️ 依赖安装
| 组件 | 	命令 |
| --- | --- |
| CMake | conda install -c conda-forge cmake |
| Dlib	 | conda install -c conda-forge dlib | 
| Face Recognition | pip install face_recognition | 

## 🎮 系统操作
#### 📝 添加员工
```
# 批量添加
python add_employees.py --dir images/employees

# 单条添加
python add_employees.py --name "李四" path/to/lisi.jpg
```

#### 👨💻 用户管理
```
# 创建新用户
import requests

data = {
    "username": "admin",
    "email": "admin@example.com",
    "password": "SecurePass123!",
    "role": "ADMIN"
}

response = requests.post(
    "http://localhost:5000/api/users",
    json=data
)
```
## 📡 推流设置
🔽 下载 OBS 推流软件：官网链接
⚙️ 配置流媒体服务器：
服务器地址：rtmp://119.3.214.158:1935/live
推流码：自定义（如 camera01）
🖥️ 更新前端代码：
```
// IdentityDetector.vue 和 ZoneMonitor.vue
const streamUrl = 'http://119.3.214.158:8080/live/你的推流码.flv';
```
## 🐛 常见问题
#### ❗ 数据库迁移失败
```
# 解决方案
rm -rf backend/migrations  # 删除旧迁移文件
flask db init             # 重新初始化
flask db migrate -m "initial"
flask db upgrade
```
#### ❗ 人脸识别失败
检查图片质量（清晰、正面、光照充足）
确认已正确安装 dlib 和 face_recognition
执行诊断脚本：python backend/diag.py
#### ❗ 推拉流失败
如果运行不成功可以尝试把backend中的migrations文件夹删除了，重新初始化

下载电脑推流端应用OBS https://obsproject.com/download
在设置处连接流媒体服务器
<img width="1215" height="887" alt="image" src="https://github.com/user-attachments/assets/14c36f8f-4885-4392-bf53-fb23e3cdbfb5" />
不要使用相同的推流码，避免冲突（例如已经有detection，另起名字）
在IdentityDetector.vue和ZoneMonitor.vue中<script setup>处更新：const streamUrl = 'http://119.3.214.158:8080/live/你的推流码.flv';


