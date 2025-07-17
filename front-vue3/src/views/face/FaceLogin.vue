<template>
    <div class="face-login-wrapper">
        <el-card class="face-login-card">
            <div class="header">
                <h2 class="title">人脸安全验证</h2>

                  <p v-if="username" class="welcome-message">
                      欢迎回来，<strong>{{ username }}</strong>！请正对摄像头完成验证。
                  </p>
                  <p v-else class="welcome-message">
                      正在加载用户信息...
                  </p>
            </div>

            <div class="video-container">
                <video ref="videoRef" autoplay playsinline class="video-feed"></video>
                <div v-if="cameraError" class="camera-overlay error">
                    <p>{{ cameraError }}</p>
                </div>
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
import { ElMessage } from 'element-plus';
import { Loading } from '@element-plus/icons-vue';
import http from '@/utils/http';

const route = useRoute();
const router = useRouter();

// 组件状态
const username = ref(route.params.username);
const videoRef = ref(null);
const isCameraReady = ref(false);
const isVerifying = ref(false);
const cameraError = ref('');
let stream = null;

onMounted(async () => {
    // 【核心修正】检查 username 是否成功获取
    if (!username.value) {
        console.error("未能从路由参数中获取到 username！");
        cameraError.value = '无法获取用户信息，请返回重试。';
        return;
    }

    // 启动摄像头
    try {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            videoRef.value.srcObject = stream;
            isCameraReady.value = true;
        } else {
            throw new Error('您的浏览器不支持访问摄像头。');
        }
    } catch (err) {
        console.error("启动摄像头失败:", err);
        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
            cameraError.value = '您拒绝了摄像头访问权限。';
        } else {
            cameraError.value = '无法启动摄像头，请检查设备或权限。';
        }
    }
});

// --- 组件卸载前关闭摄像头 ---
onBeforeUnmount(() => {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
});

const captureAndVerify = async () => {
    if (!videoRef.value || !isCameraReady.value) return;

    isVerifying.value = true;

    const canvas = document.createElement('canvas');
    canvas.width = videoRef.value.videoWidth;
    canvas.height = videoRef.value.videoHeight;
    canvas.getContext('2d').drawImage(videoRef.value, 0, 0, canvas.width, canvas.height);
    const imageBase64 = canvas.toDataURL('image/jpeg');

    try {
        // http.js 的拦截器会处理掉外层的 .data
        // 所以这里的 'response' 变量直接就是后端的业务数据 { success: true, ... }
        const response = await http.post('/face_verify/', {
            username: username.value,
            image: imageBase64
        });

        console.log("人脸验证成功，后端响应:", response);

        // 【关键修复】保存新的 Token
        if (response.token && response) {
            localStorage.setItem('token', response.token);

            console.log('Token 已保存到 localStorage:', localStorage.getItem('token'));

            ElMessage.success('验证成功，正在进入系统...');

            // 现在可以安全地跳转了
            router.push('/home'); // 或者你的主页路径

        } else {
            // 防御性编程：如果后端因为某种原因没返回 token
            ElMessage.error('登录凭证获取失败，无法进入系统。');
        }

    } catch (error) {
    if (error && error.isBusinessError) {
        // 这是后端明确告诉我们“人脸不匹配”或类似情况
        ElMessage.error(error.message || '人脸验证失败，请重试');
        // 在这里可以允许用户重试，比如重置摄像头状态等
    } else if (error && error.response?.status === 401) {
        ElMessage.error('登录状态已失效，请重新登录');
        // 跳转到登录页
        router.push('/login');
    } else {
        // 其他所有错误，包括超时
        ElMessage.error('验证请求失败，请检查网络或稍后再试');
    }
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