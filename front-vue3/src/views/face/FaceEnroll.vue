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
                <!-- 实时视频流将显示在这里 -->
                <video ref="videoRef" autoplay playsinline class="video-feed"></video>
                <!-- 加载视频时的提示 -->
                <div v-if="!isCameraReady" class="loading-overlay">
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
                    :disabled="!isCameraReady"
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
import { ElNotification } from 'element-plus';
import { Loading } from '@element-plus/icons-vue';
import http from '@/utils/http';

const route = useRoute();
const router = useRouter();

// 组件状态
const username = ref('');
const videoRef = ref(null); // 引用 <video> 元素
const isCameraReady = ref(false);
const isEnrolling = ref(false);
let stream = null; // 用于存储摄像头流

// 组件挂载时执行
onMounted(async () => {
    // 1. 从路由参数中获取用户名
    username.value = route.query.username;
    if (!username.value) {
        ElNotification({
            title: '错误',
            message: '无法获取用户信息，请重新注册。',
            type: 'error',
        });
        router.push('/register');
        return;
    }

    // 2. 启动摄像头
    await startCamera();
});

// 组件卸载前，关闭摄像头以释放资源
onBeforeUnmount(() => {
    stopCamera();
});

/**
 * 启动摄像头并显示实时视频流
 */
const startCamera = async () => {
    try {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480 }, // 可以指定分辨率
                audio: false
            });
            if (videoRef.value) {
                videoRef.value.srcObject = stream;
                isCameraReady.value = true;
            }
        } else {
            throw new Error('浏览器不支持摄像头访问');
        }
    } catch (error) {
        console.error("摄像头启动失败:", error);
        ElNotification({
            title: '摄像头启动失败',
            message: error.message || '请检查浏览器权限设置。',
            type: 'error',
        });
        isCameraReady.value = false;
    }
};

/**
 * 停止摄像头
 */
const stopCamera = () => {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
    if (videoRef.value) {
        videoRef.value.srcObject = null;
    }
    isCameraReady.value = false;
};

/**
 * 捕获视频帧并发送到后端进行录入
 */
const captureAndEnroll = async () => {
    if (!videoRef.value || !isCameraReady.value) return;

    isEnrolling.value = true;

    // 1. 创建一个 <canvas> 元素来捕获图像
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.value.videoWidth;
    canvas.height = videoRef.value.videoHeight;
    const context = canvas.getContext('2d');
    context.drawImage(videoRef.value, 0, 0, canvas.width, canvas.height);

    // 2. 将 canvas 内容转换为 Base64 编码的图片
    const imageBase64 = canvas.toDataURL('image/jpeg');

    try {
        // 3. 将图片和用户名发送到后端
        await http.post('/face_enroll/', {
            username: username.value,
            image: imageBase64
        });

        ElNotification({
            title: '录入成功！',
            message: '您的人脸信息已保存，现在可以登录了。',
            type: 'success',
            duration: 2000
        });

        // 4. 成功后跳转到登录页面
        setTimeout(() => {
            router.push('/login');
        }, 2000);

    } catch (err) {
        ElNotification({
            title: '人脸录入失败',
            message: err.response?.data?.message || '请确保面部清晰无遮挡，然后重试。',
            type: 'error'
        });
    } finally {
        isEnrolling.value = false;
    }
};
</script>

<style scoped>
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