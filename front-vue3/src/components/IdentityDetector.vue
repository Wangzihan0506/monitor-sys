<template>
  <div class="recognizer-container">
    <div class="status-bar">
      <p>{{ statusMessage }}</p>
    </div>
    <div class="video-wrapper">
      <!-- 视频元素，用来显示摄像头画面 -->
      <video ref="videoRef" @play="onPlay" autoplay playsinline muted></video>
      <!-- Canvas元素，用来在视频上绘制框和名字 -->
      <canvas ref="canvasRef"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import * as faceDetection from '@tensorflow-models/face-detection';
import '@tensorflow/tfjs-core';
import '@tensorflow/tfjs-backend-webgl'; // 引入WebGL后端以获得最佳性能
import axios from 'axios';

// --- Refs and State ---
const videoRef = ref(null);
const canvasRef = ref(null);
const statusMessage = ref('正在初始化...');
let detector = null; // 人脸检测器实例
let recognitionInterval = null;
let isRecognitionRunning = false;

// --- 生命周期钩子 ---
onMounted(async () => {
  statusMessage.value = '正在加载人脸识别模型...';
  try {
    // 设置并加载新的人脸检测模型
    const model = faceDetection.SupportedModels.MediaPipeFaceDetector;
    detector = await faceDetection.createDetector(model, {
      runtime: 'tfjs',
      modelType: 'full',
    });
    statusMessage.value = '正在启动摄像头...';
    await startCamera();
  } catch (error) {
    console.error("加载模型或启动摄像头失败:", error);
    statusMessage.value = '初始化失败，请检查浏览器控制台。';
  }
});

onUnmounted(() => {
  clearInterval(recognitionInterval);
  if (videoRef.value && videoRef.value.srcObject) {
    videoRef.value.srcObject.getTracks().forEach(track => track.stop());
  }
});

// --- 功能函数 ---
async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: {} });
    videoRef.value.srcObject = stream;
  } catch (error) {
    console.error("摄像头启动失败:", error);
    statusMessage.value = '摄像头启动失败。';
  }
}

function onPlay() {
  console.log("onPlay 事件已触发！");
  if (!videoRef.value) return;
  statusMessage.value = '摄像头已启动，正在实时识别...';
  // 确保canvas尺寸与视频显示尺寸一致
  canvasRef.value.width = videoRef.value.clientWidth;
  canvasRef.value.height = videoRef.value.clientHeight;
  recognitionInterval = setInterval(runRecognition, 2000);
}

// 【重构】使用新的库进行识别和绘制
async function runRecognition() {
  if (isRecognitionRunning || !detector || !videoRef.value || videoRef.value.paused || videoRef.value.ended) return;

  isRecognitionRunning = true;
  try {
    const video = videoRef.value;
    const canvas = canvasRef.value;
    const context = canvas.getContext('2d');
    context.clearRect(0, 0, canvas.width, canvas.height);

    // --- 【关键的最终解决方案】 ---
    // 步骤1：从视频中创建一个可靠的静态快照 (ImageBitmap)
    const videoFrameBitmap = await createImageBitmap(video);

    // 步骤2：在快照上检测人脸
    const faces = await detector.estimateFaces(videoFrameBitmap, { flipHorizontal: false });

    if (faces.length === 0) {
      isRecognitionRunning = false;
      return;
    }

    // 步骤3：从快照中裁剪人脸图片
    const faceBlobs = await Promise.all(
      faces.map(async (face) => {
        const { xMin, yMin, width, height } = face.box;

        // 现在所有尺寸都基于 ImageBitmap，非常稳定
        const imageWidth = videoFrameBitmap.width;
        const imageHeight = videoFrameBitmap.height;

        const safeX = Math.max(0, xMin);
        const safeY = Math.max(0, yMin);
        const safeWidth = Math.min(imageWidth - safeX, width);
        const safeHeight = Math.min(imageHeight - safeY, height);

        if (safeWidth <= 0 || safeHeight <= 0) return null;

        const faceCanvas = document.createElement('canvas');
        faceCanvas.width = safeWidth;
        faceCanvas.height = safeHeight;
        const faceCtx = faceCanvas.getContext('2d');

        // 从 ImageBitmap 快照（而不是动态的video元素）中绘制，这更可靠
        faceCtx.drawImage(videoFrameBitmap, safeX, safeY, safeWidth, safeHeight, 0, 0, safeWidth, safeHeight);

        return new Promise(resolve => faceCanvas.toBlob(resolve, 'image/jpeg'));
      })
    );

    const validBlobs = faceBlobs.filter(blob => blob);
    if (validBlobs.length === 0) {
        console.log("检测到人脸，但无法成功裁剪，结束本轮。");
        isRecognitionRunning = false;
        return;
    }

    // 步骤4：打包发送（不变）
    const formData = new FormData();
    validBlobs.forEach((blob, i) => {
      formData.append('faces', blob, `face_${i}.jpg`);
    });

    console.log("准备将裁剪的人脸发送到后端...");
    const response = await axios.post('/api/face/recognize_batch', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    const results = response.data.results;
    console.log("收到后端识别结果:", results);

    // 步骤5：绘制结果（不变，但坐标更稳定）
    const scaleX = canvas.width / videoFrameBitmap.width;
    const scaleY = canvas.height / videoFrameBitmap.height;

    results.forEach((result, i) => {
      if (faces[i]) {
        const { xMin, yMin, width, height } = faces[i].box;
        const drawX = xMin * scaleX;
        const drawY = yMin * scaleY;
        const drawWidth = width * scaleX;
        const drawHeight = height * scaleY;

        context.strokeStyle = result.name === '陌生人' ? 'red' : 'limegreen';
        context.lineWidth = 2;
        context.strokeRect(drawX, drawY, drawWidth, drawHeight);

        const label = `${result.name} (${result.distance.toFixed(2)})`;
        context.fillStyle = context.strokeStyle;
        context.font = '16px Arial';
        context.fillText(label, drawX, drawY > 10 ? drawY - 5 : drawY + height + 15);
      }
    });

  } catch (error) {
    console.error("runRecognition 函数中发生严重错误:", error);
  } finally {
    isRecognitionRunning = false;
  }
}


</script>

<style scoped>
/* 你的 CSS 样式保持不变 */
.recognizer-container {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.status-bar {
  margin-bottom: 10px;
  font-size: 1.2em;
  font-weight: bold;
}
.video-wrapper {
  position: relative; /* 这是关键，为了让canvas能覆盖在video上 */
  width: 720px;
  height: 560px;
}
video, canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}
</style>