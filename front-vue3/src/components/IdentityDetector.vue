<template>
  <div class="recognizer-container">
    <div class="status-bar">
      <p>{{ statusMessage }}</p>
    </div>

    <div class="detection-display-wrapper">
      <video ref="videoElement" autoplay playsinline muted></video>
      <canvas ref="detectionCanvasRef"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, h ,nextTick } from 'vue'; // 确保导入 h 用于 ElNotification
import * as faceDetection from '@tensorflow-models/face-detection';
import '@tensorflow/tfjs-core';
import '@tensorflow/tfjs-backend-webgl';
import axios from 'axios';
import { ElMessage, ElNotification } from 'element-plus';
import flvjs from 'flv.js'; // <<-- 重新引入 flv.js


const props = defineProps({
  detectionInterval: {
    type: Number,
    default: 2000,
  },
  displayDetectionCanvas: {
    type: Boolean,
    default: true,
  }
});

// --- Refs and State ---
const statusMessage = ref('人脸识别模块初始化中...');
const videoElement = ref(null); // 【核心修改】绑定到本地 <video> 标签
const detectionCanvasRef = ref(null);
const streamUrl = 'http://119.3.214.158:8080/live/detection.flv'; // 【核心修改】视频流地址移到这里
let flvPlayer = null; // 【核心修改】flvPlayer 实例移到这里
let detector = null;
let recognitionTimer = null;
let isRecognitionRunning = false;
const backendBaseUrl = 'http://127.0.0.1:5000/api';
const lastAbnormalAlarmSentTime = ref(0);
const ALARM_THROTTLE_SECONDS = 5;

// --- 生命周期钩子 ---
onMounted(async () => {
  statusMessage.value = '正在加载人脸检测模型...';
  try {
    const model = faceDetection.SupportedModels.MediaPipeFaceDetector;
    detector = await faceDetection.createDetector(model, {
      runtime: 'tfjs',
      modelType: 'full',
    });
    statusMessage.value = '模型加载完成，等待视频流输入...';

    // 【核心修改】直接在这里启动流和识别定时器
    startStream();
    startRecognition();

  } catch (error) {
    console.error("Identity Detector 初始化失败:", error);
    statusMessage.value = '初始化失败，请检查浏览器控制台。';
    ElMessage.error('身份检测模型加载失败！');
  }
});

onUnmounted(() => {
  console.log("IdentityDetector: 组件卸载，停止识别定时器和本地视频显示。");
  stopRecognition();
  destroyFlvPlayer(); // 销毁 flvPlayer
  if (videoElement.value) { // 清理本地 video element
      videoElement.value.srcObject = null;
  }
});

// 【核心修改】startStream 函数 (与 ZoneMonitor 类似，独立管理)
function startStream() {
  const videoDomElement = videoElement.value; // 使用本地 ref
  if (!videoDomElement) {
    console.warn("IdentityDetector: Video DOM element is not available yet.");
    // 如果 videoDomElement 还是 null，使用 nextTick 再次尝试 (更健壮)
    nextTick(() => { // <<-- nextTick 必须在这里
        if (!videoElement.value) { // 再次检查是否真的没拿到
            console.error("IdentityDetector: Video DOM element still not available after nextTick. Cannot start stream.");
            ElMessage.error('视频播放器初始化失败，请重试或检查配置。');
            return;
        }
        startStream(); // 递归调用，尝试在下一个渲染周期获取
    });
    return;
  }

  if (flvjs.isSupported()) {
    console.log("IdentityDetector: 使用 flv.js 加载视频流...");

    if (flvPlayer) { // 销毁旧播放器实例，确保总是创建新的
      flvPlayer.pause();
      flvPlayer.unload();
      flvPlayer.detachMediaElement();
      flvPlayer.destroy();
      flvPlayer = null;
    }

    flvPlayer = flvjs.createPlayer({
      type: 'flv',
      isLive: true,
      url: streamUrl
    });

    flvPlayer.attachMediaElement(videoDomElement);

    flvPlayer.load();
    videoDomElement.play().catch(e => console.error("IdentityDetector: 视频自动播放失败:", e));

    flvPlayer.on('error', (errType, errDetail, errInfo) => {
      console.error('IdentityDetector: FLV.js 播放器错误:', errType, errDetail, errInfo);
      ElMessage.error(`IdentityDetector: 视频流错误: ${errDetail} - ${errInfo.msg || '未知错误'}`);
      destroyFlvPlayer();
      setTimeout(startStream, 3000);
    });

  } else {
    ElMessage.error('IdentityDetector: 您的浏览器不支持播放FLV视频流。');
  }
}

// 【核心修改】destroyFlvPlayer 函数 (与 ZoneMonitor 类似，独立管理)
function destroyFlvPlayer() {
  if (flvPlayer) {
    console.log("IdentityDetector: 销毁 flv.js 播放器...");
    flvPlayer.pause();
    flvPlayer.unload();
    flvPlayer.detachMediaElement();
    flvPlayer.destroy();
    flvPlayer = null;
  }
  if (videoElement.value && videoElement.value.srcObject) {
      videoElement.value.srcObject.getTracks().forEach(track => track.stop());
      videoElement.value.srcObject = null;
  }
}

// --- 功能函数 ---
function startRecognition() {
  if (recognitionTimer) {
    clearInterval(recognitionTimer);
  }
  statusMessage.value = '人脸识别器已启动，正在实时检测...';
  recognitionTimer = setInterval(runRecognition, props.detectionInterval); // detectionInterval prop 依然保留
}

function stopRecognition() {
  if (recognitionTimer) {
    clearInterval(recognitionTimer);
    recognitionTimer = null;
    isRecognitionRunning = false;
    statusMessage.value = '人脸识别器已停止。';
  }
}

// 【核心修改】runRecognition 函数，使用本地 videoElement
async function runRecognition() {
  const video = videoElement.value; // <<-- 修正这里，使用本地 ref
  if (isRecognitionRunning || !detector || !video || video.paused || video.ended || video.videoWidth === 0) {
    return;
  }

  isRecognitionRunning = true;
  let context = null;
  let videoFrameBitmap = null;

  try {
    videoFrameBitmap = await createImageBitmap(video); // 从本地 videoElement 获取帧

    const faces = await detector.estimateFaces(videoFrameBitmap, { flipHorizontal: false });

    if (faces.length === 0) {
      statusMessage.value = '未检测到人脸。';
      if (detectionCanvasRef.value) {
          const ctx = detectionCanvasRef.value.getContext('2d');
          ctx.clearRect(0, 0, detectionCanvasRef.value.width, detectionCanvasRef.value.height);
      }
      return;
    }

    statusMessage.value = `检测到 ${faces.length} 个人脸，进行识别...`;

    // 为每个检测到的人脸创建 Blob 并加入 FormData
    const formData = new FormData();
    let facesAddedToForm = 0;
    const faceBoxes = [];

    for (const face of faces) {
      const { xMin, yMin, width, height } = face.box;

      const safeX = Math.max(0, xMin);
      const safeY = Math.max(0, yMin);
      const safeWidth = Math.min(videoFrameBitmap.width - safeX, width);
      const safeHeight = Math.min(videoFrameBitmap.height - safeY, height);

      if (safeWidth <= 0 || safeHeight <= 0) {
        console.warn("无法裁剪有效人脸区域，跳过。");
        continue;
      }

      const faceCanvas = document.createElement('canvas');
      faceCanvas.width = safeWidth;
      faceCanvas.height = safeHeight;
      const faceCtx = faceCanvas.getContext('2d');

      faceCtx.drawImage(videoFrameBitmap, safeX, safeY, safeWidth, safeHeight, 0, 0, safeWidth, safeHeight);

      const blob = await new Promise(resolve => faceCanvas.toBlob(resolve, 'image/jpeg', 0.8));
      if (blob) {
        formData.append('faces', blob, `face_${facesAddedToForm}.jpg`);
        faceBoxes.push([xMin, yMin, width, height]);
        facesAddedToForm++;
      }
    }

    if (facesAddedToForm === 0) {
      statusMessage.value = '未检测到可识别的人脸。';
      if (detectionCanvasRef.value) {
          const ctx = detectionCanvasRef.value.getContext('2d');
          ctx.clearRect(0, 0, detectionCanvasRef.value.width, detectionCanvasRef.value.height);
      }
      return;
    }

    console.log(`准备将 ${facesAddedToForm} 个人脸发送到后端进行识别...`);
    const response = await axios.post(`${backendBaseUrl}/face_recognition/recognize_batch`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    const results = response.data.results;
    console.log("收到后端识别结果:", results);

    drawFaceDetections(faces, results, faceBoxes, videoFrameBitmap);

    // 绘制检测框和标签 (如果 displayDetectionCanvas 为 true)
    if (props.displayDetectionCanvas && detectionCanvasRef.value) { // displayDetectionCanvas prop 依然保留
      const canvas = detectionCanvasRef.value;
      context = canvas.getContext('2d');
      canvas.width = videoFrameBitmap.width;
      canvas.height = videoFrameBitmap.height;
      context.clearRect(0, 0, canvas.width, canvas.height);

      results.forEach((result, i) => {
        if (faceBoxes[i]) {
          const [x, y, width, height] = faceBoxes[i];
          context.strokeStyle = result.name === '陌生人' ? 'red' : 'limegreen';
          context.lineWidth = 2;
          context.strokeRect(x, y, width, height);

          const label = `${result.name} (${result.distance.toFixed(2)})`;
          context.fillStyle = context.strokeStyle;
          context.font = '24px Arial';
          context.fillText(label, x, y > 24 ? y - 10 : y + height + 20);
        }
      });
    }

    // 处理识别结果，发送陌生人告警
    results.forEach((result, i) => {
      if (result.name === '陌生人') {
        const personBox = faceBoxes[i];
        console.warn(`[身份告警] 检测到陌生人! ID: ${result.name}, 距离: ${result.distance.toFixed(4)}`);
        sendAbnormalAlarm('陌生人', `检测到陌生人！距离: ${result.distance.toFixed(2)}`, personBox);
      }
    });

  } catch (error) {
    console.error("人脸识别运行时发生错误:", error);
    statusMessage.value = '识别失败，请检查网络或日志。';
    if (error.response) {
      console.error("后端响应错误:", error.response.data);
    }
    ElMessage.error('人脸识别处理失败，请查看控制台。');
  } finally {
    isRecognitionRunning = false;
    if (videoFrameBitmap) {
      videoFrameBitmap.close();
    }
  }
}

function drawFaceDetections(faces, recognitionResults, originalFaceBoxes, videoBitmap) {

    console.log("IdentityDetector: drawFaceDetections called. Canvas ref:", detectionCanvasRef.value); // <<-- 新增日志
    if (!props.displayDetectionCanvas || !detectionCanvasRef.value) {
        console.warn("IdentityDetector: Canvas or displayDetectionCanvas prop not ready for drawing."); // <<-- 新增日志
        return;
    }

    if (!props.displayDetectionCanvas || !detectionCanvasRef.value) return; // 检查 prop 和 canvas 存在

    const canvas = detectionCanvasRef.value;
    const ctx = canvas.getContext('2d');

    ctx.clearRect(0, 0, canvas.width, canvas.height); // 清除上一帧内容

    // 【临时测试代码】绘制一个红色的矩形覆盖整个 Canvas
    ctx.fillStyle = 'rgba(255, 0, 0, 0.5)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    // 【临时测试代码】绘制一个绿色的圆心
    ctx.fillStyle = 'green';
    ctx.beginPath();
    ctx.arc(canvas.width / 2, canvas.height / 2, 50, 0, Math.PI * 2);
    ctx.fill();

    // 确保 Canvas 尺寸与视频帧（ImageBitmap）尺寸一致
    canvas.width = videoBitmap.width;
    canvas.height = videoBitmap.height;

    ctx.clearRect(0, 0, canvas.width, canvas.height); // 清除上一帧内容

    recognitionResults.forEach((result, i) => {
        const faceBox = originalFaceBoxes[i]; // 这是 MediaPipe 检测到的原始人脸框坐标
        if (!faceBox) return;

        const [x, y, width, height] = faceBox;

        let color = result.name === '陌生人' ? 'red' : 'limegreen';
        let label = result.name === '陌生人' ? `陌生人 (${result.distance.toFixed(2)})` : `${result.name} (${result.distance.toFixed(2)})`;
        if (result.distance > 0.8) { // 再次用阈值判断，如果距离太大，也认为是陌生人
            color = 'red';
            label = `陌生人 (${result.distance.toFixed(2)})`;
        }


        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.strokeRect(x, y, width, height); // 绘制框

        // 绘制背景
        ctx.fillStyle = color;
        const textPadding = 4;
        const fontSize = 24;
        ctx.font = `${fontSize}px Arial`;
        const textWidth = ctx.measureText(label).width;

        ctx.fillRect(x, y > fontSize ? y - fontSize : y + height, textWidth + textPadding * 2, fontSize + textPadding);

        // 绘制文字
        ctx.fillStyle = 'white';
        ctx.fillText(label, x + textPadding, y > fontSize ? y - textPadding : y + height + fontSize);
    });
}

// --- 告警通知 (仅发送 Abnormal 类型告警) ---
async function sendAbnormalAlarm(label, message, box) {
  const now = Date.now();
  if (now - lastAbnormalAlarmSentTime.value < ALARM_THROTTLE_SECONDS * 1000) {
    console.warn(`告警节流：异常行为告警发送频率过高。`);
    return;
  }
  lastAbnormalAlarmSentTime.value = now;

  ElNotification({
    title: '异常行为告警',
    message: h('div', null, [
      h('p', { style: 'font-weight: bold; margin: 0;' }, message),
      box ? h('p', { style: 'font-size: 12px; margin: 5px 0 0 0;' }, `目标框: ${JSON.stringify(box)}`) : null
    ]),
    type: 'warning',
    duration: 4000,
  });

  // 【核心修改】从本地 videoElement 捕获当前帧
  const frameBase64 = captureFrameAsBase64FromVideoElement(videoElement.value); // 使用本地 ref
  if (!frameBase64) {
    console.error("未能捕获告警截图，跳过后端写入。");
    return;
  }

  const apiUrl = `${backendBaseUrl}/alert_abnormal`;
  const postData = {
    label: label,
    box: JSON.stringify(box),
    frame_image: frameBase64,
    message: message
  };

  try {
    const response = await axios.post(apiUrl, postData);
    if (response.data.code === 0) {
      console.log(`异常告警已发送至后端：`, response.data.msg);
    } else {
      console.error(`异常告警发送后端失败：`, response.data.msg);
      ElMessage.error(`异常告警后端写入失败: ${response.data.msg}`);
    }
  } catch (error) {
    console.error(`发送异常告警到后端时发生错误：`, error);
    ElMessage.error(`发送异常告警到后端时发生网络错误。`);
  }
}

// 【核心修改】captureFrameAsBase64FromVideoElement 函数 (使用本地 ref)
function captureFrameAsBase64FromVideoElement(videoDomElement) { // 保持参数名，但内部使用传入的参数
   const video = videoDomElement;
   if (!video || video.videoWidth === 0 || video.videoHeight === 0) {
    console.error("IdentityDetector: 无法捕获帧：视频不可用或尺寸无效。");
    return null;
  }
  const tempCanvas = document.createElement('canvas');
  tempCanvas.width = video.videoWidth;
  tempCanvas.height = video.videoHeight;
  const tempCtx = tempCanvas.getContext('2d');
  tempCtx.drawImage(video, 0, 0, video.videoWidth, video.videoHeight);
  return tempCanvas.toDataURL('image/jpeg', 0.8).split(',')[1];
}

</script>

<style scoped>
/* 样式保持不变，这些样式之前已经修改过，并且没有 syntax error */
.recognizer-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
  background-color: #f9f9f9;
  border: 1px solid #eee;
  margin-top: 10px;
  height: 100%; /* 【新增】确保组件本身能撑开高度 */
  box-sizing: border-box; /* 【新增】防止 padding 导致高度溢出 */
}
.status-bar {
  margin-bottom: 10px;
  font-size: 1.2em;
  font-weight: bold;
  color: #333;
}
.detection-display-wrapper {
  position: relative;
  width: 100%; /* 假设这个容器会和视频显示尺寸一致或按比例缩放 */
  aspect-ratio: 16 / 9; /* 示例，保持和视频一样的宽高比 */
  background-color: #000; /* 视频未加载时的背景色 */
  overflow: hidden; /* 【确保这里没有多余的斜杠 / 】 */
  flex-shrink: 0; /* 【新增】防止 flex 容器挤压 */
  margin-top: 10px; /* 【新增】与 status-bar 分隔 */
}
.detection-display-wrapper video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain; /* 视频保持比例填充容器 */
  z-index: 1; /* 确保视频在 canvas 之下 */
}
.detection-display-wrapper canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none; /* 允许鼠标事件穿透 */
  z-index: 2; /* 确保 canvas 在视频之上，可以绘制 */
  border: 1px solid #ddd; /* 给 Canvas 加个边框以便观察 */
}
</style>