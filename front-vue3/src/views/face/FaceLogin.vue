<template>
    <div class="face-login-wrapper">
        <el-card class="face-login-card">
            <div class="header">
                <h2 class="title">人脸安全验证</h2>
                <p v-if="username" class="sub-title">
                    欢迎回来，<span class="username">{{ username }}</span>！请正对摄像头完成验证。
                </p>
            </div>

            <div class="video-container">
                <video ref="videoRef" autoplay playsinline class="video-feed"></video>
                <div v-if="!isCameraReady" class="loading-overlay">
                    <el-icon class="is-loading" :size="30"><Loading /></el-icon>
                    <p>正在启动摄像头...</p>
                </div>
            </div>

            <div class="action-buttons">
                <!-- 我们可以做一个自动验证的逻辑，或者手动点击 -->
                <el-button
                    type="primary"
                    size="large"
                    @click="captureAndVerify"
                    :loading="isVerifying"
                    :disabled="!isCameraReady"
                >
                    {{ isVerifying ? '正在验证...' : '开始人脸验证' }}
                </el-button>
            </div>
             <div class="tips">
                <p>验证成功后将自动进入系统。</p>
            </div>
        </el-card>
    </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElNotification, ElMessage } from 'element-plus';
import { Loading } from '@element-plus/icons-vue';
import http from '@/utils/http';

const route = useRoute();
const router = useRouter();

// 组件状态
const username = ref('');
const videoRef = ref(null);
const isCameraReady = ref(false);
const isVerifying = ref(false);
let stream = null;

onMounted(async () => {
    username.value = route.query.username;
    if (!username.value) {
        ElMessage.error('无法获取用户信息，请重新登录。');
        router.push('/login');
        return;
    }
    await startCamera();
});

onBeforeUnmount(() => {
    stopCamera();
});

const startCamera = async () => {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        if (videoRef.value) {
            videoRef.value.srcObject = stream;
            isCameraReady.value = true;
        }
    } catch (error) {
        ElMessage.error('摄像头启动失败，请检查设备和浏览器权限。');
    }
};

const stopCamera = () => {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
};

const captureAndVerify = async () => {
    if (!videoRef.value || !isCameraReady.value) return;

    isVerifying.value = true;

    const canvas = document.createElement('canvas');
    canvas.width = videoRef.value.videoWidth;
    canvas.height = videoRef.value.videoHeight;
    canvas.getContext('2d').drawImage(videoRef.value, 0, 0, canvas.width, canvas.height);
    const imageBase64 = canvas.toDataURL('image/jpeg');

    try {
        const {data} = await http.post('/face_verify/', {
            username: username.value,
            image: imageBase64
        });

        ElNotification({
            title: '验证成功！',
            message: '欢迎进入系统！',
            type: 'success',
            duration: 1500
        });

        // 验证成功，跳转到主页
        // 这里可以根据后端返回的角色信息跳转到不同页面
        // 假设data.role可以是'admin'或'user'
        const redirectPath = data.role === 'admin' ? '/admin' : '/home';
        router.push(redirectPath);

    } catch (err) {
        ElMessage.error(err.response?.data?.message || '人脸不匹配或识别失败，请重试。');
    } finally {
        isVerifying.value = false;
    }
};
</script>

<style scoped>
/* 样式可以复用 FaceEnroll.vue 的，或者自定义 */
.face-login-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    background: #f0f2f5;
}
.face-login-card {
    width: 700px;
    padding: 24px;
    border-radius: 8px;
    text-align: center;
}
.header {
    margin-bottom: 20px;
}
.title {
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