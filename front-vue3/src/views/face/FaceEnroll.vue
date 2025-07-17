<template>
    <div class="enroll-wrapper">
        <el-card class="enroll-card">
            <div class="enroll-header">
                <h2 class="enroll-title">人脸信息录入</h2>
                <p v-if="username" class="sub-title">
                    你好，<span class="username">{{ username }}</span>！请正对摄像头，确保光线充足。
                </p>
            </div>

            <div class="video-container">
                <video ref="videoRef" autoplay playsinline class="video-feed"></video>
                <div v-if="cameraError" class="loading-overlay error-overlay">
                    <el-icon :size="30"><WarningFilled /></el-icon>
                    <p>{{ cameraError }}</p>
                </div>
                <div v-else-if="!isCameraReady" class="loading-overlay">
                    <el-icon class="is-loading" :size="30"><Loading /></el-icon>
                    <p>正在启动摄像头...</p>
                </div>
            </div>

            <div class="action-buttons">
                <el-button
                    type="primary"
                    size="large"
                    @click="captureAndEnroll"
                    :loading="isEnrolling"
                    :disabled="!isCameraReady || isEnrolling"
                >
                    {{ isEnrolling ? '正在录入...' : '捕获并录入人脸' }}
                </el-button>
            </div>

            <div class="tips">
                <p>录入成功后将自动跳转到登录页面。</p>
            </div>
        </el-card>
    </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElNotification, ElMessage } from 'element-plus'; // 引入 ElMessage
import { Loading, WarningFilled } from '@element-plus/icons-vue'; // 引入图标
import http from '@/utils/http';

const route = useRoute();
const router = useRouter();

// 组件状态
const username = ref('');
const videoRef = ref(null);
const isCameraReady = ref(false);
const isEnrolling = ref(false);
const cameraError = ref(''); // 用于显示摄像头错误信息
let stream = null;

onMounted(async () => {
    username.value = route.query.username;
    if (!username.value) {
        ElMessage.error('无法获取用户信息，即将返回注册页面...');
        setTimeout(() => router.push({ name: 'register' }), 2000);
        return;
    }
    await startCamera();
});

onBeforeUnmount(() => {
    stopCamera();
});

const startCamera = async () => {
    try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('您的浏览器不支持摄像头访问功能。');
        }
        stream = await navigator.mediaDevices.getUserMedia({
            video: { width: 640, height: 480 },
            audio: false
        });
        if (videoRef.value) {
            videoRef.value.srcObject = stream;
            isCameraReady.value = true;
        }
    } catch (error) {
        console.error("摄像头启动失败:", error);
        cameraError.value = '摄像头启动失败，请检查设备和浏览器权限。';
        // 可以提供更具体的错误提示
        if (error.name === "NotAllowedError" || error.name === "PermissionDeniedError") {
            cameraError.value = "您拒绝了摄像头访问权限，请在浏览器设置中允许访问。";
        } else if (error.name === "NotReadableError") {
            cameraError.value = "无法读取摄像头数据，请确保摄像头未被其他程序占用。";
        }
    }
};

const stopCamera = () => {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
};

const captureAndEnroll = async () => {
    if (!isCameraReady.value) {
        ElMessage.error('摄像头未就绪，无法捕获图像。');
        return;
    }

    isEnrolling.value = true;

    const canvas = document.createElement('canvas');
    canvas.width = videoRef.value.videoWidth;
    canvas.height = videoRef.value.videoHeight;
    const context = canvas.getContext('2d');
    context.drawImage(videoRef.value, 0, 0, canvas.width, canvas.height);
    const imageBase64 = canvas.toDataURL('image/jpeg');

    try {

        const response = await http.post('/face_enroll/', {
            username: username.value,
            image: imageBase64
        });

        console.log('【人脸录入】后端返回的原始响应:', response);

        ElNotification({
              title: '录入成功！',
              message: '您的人脸信息已保存，即将跳转到登录页面。',
              type: 'success',
          });
          stopCamera();
          setTimeout(() => {
              // 确保你的登录路由 name 是 'Login'
              router.push({ name: 'login' });
          }, 2000);

    } catch (err) {
        // 处理网络错误或服务器500错误
        ElNotification({
            title: '请求失败',
            message: err.response?.data?.message || '服务器发生错误，请稍后重试。',
            type: 'error'
        });
    } finally {
        isEnrolling.value = false;
    }
};
</script>

<style scoped>
/* 保持你的样式不变，你的样式已经很好了 */
.enroll-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    background: #f0f2f5;
}

.enroll-card {
    width: 700px;
    padding: 24px;
    border-radius: 8px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.enroll-header {
    margin-bottom: 20px;
}

.enroll-title {
    font-size: 24px;
    font-weight: bold;
}

.sub-title {
    color: #606266;
    margin-top: 8px;
}

.username {
    font-weight: bold;
    color: #409eff;
}

.video-container {
    position: relative;
    width: 640px;
    height: 480px;
    margin: 0 auto;
    background-color: #000;
    border-radius: 6px;
    overflow: hidden;
}

.video-feed {
    width: 100%;
    height: 100%;
    object-fit: cover;
    /* 镜像翻转，让用户感觉像在照镜子 */
    transform: scaleX(-1);
}

.loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    background-color: rgba(0, 0, 0, 0.5);
    color: white;
    z-index: 10;
}

.error-overlay {
    background-color: rgba(245, 108, 108, 0.7);
}


.action-buttons {
    margin-top: 24px;
}

.tips {
    margin-top: 16px;
    color: #909399;
    font-size: 14px;
}
</style>