# front-vue3

## Project setup
```
pnpm install
```

### Compiles and hot-reloads for development
```
pnpm run serve
```

### Compiles and minifies for production
```
pnpm run build
```

### Lints and fixes files
```
pnpm run lint
```

### Customize configuration
See [Configuration Reference](https://cli.vuejs.org/config/).

数据库更新后需要迁移更新
进入后端目录
cd backend 

# 只做一次：初始化迁移环境
flask db init

# 每次模型变化后执行（生成版本脚本）
flask db migrate -m "更新描述"

# 应用到数据库
flask db upgrade

如果运行不成功可以尝试把backend中的migrations文件夹删除了，重新初始化

下载电脑推流端应用OBS https://obsproject.com/download
在设置处连接流媒体服务器
<img width="1215" height="887" alt="image" src="https://github.com/user-attachments/assets/14c36f8f-4885-4392-bf53-fb23e3cdbfb5" />
不要使用相同的推流码，避免冲突（例如已经有detection，另起名字）
在IdentityDetector.vue和ZoneMonitor.vue中<script setup>处更新：const streamUrl = 'http://119.3.214.158:8080/live/你的推流码.flv';


