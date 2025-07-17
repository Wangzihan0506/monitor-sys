<template>
  <el-card>
    <div class="header">
      <h2>后厨行为异常检测</h2>
      <p>状态: <el-tag :type="statusTagType" size="small">{{ statusMessage }}</el-tag></p>
    </div>

    <!-- 视频和Canvas的容器 -->
    <div class="video-container">
      <video ref="videoRef" autoplay playsinline muted></video>
      <canvas ref="canvasRef" class="overlay-canvas"></canvas>
    </div>

    <!-- 控制按钮 -->
    <div class="controls">
      <el-button type="primary" @click="startDetection" :disabled="isDetecting || !isStreamReady">开始检测</el-button>
      <el-button @click="stopDetection" :disabled="!isDetecting">停止检测</el-button>
    </div>

    <!-- 原始数据展示区 (可选) -->
    <div class="result-display" v-if="detectionResult">
      <h3>最近一次检测结果 (原始数据):</h3>
      <pre>{{ JSON.stringify(detectionResult, null, 2) }}</pre>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, computed } from 'vue';
import http from '@/utils/http';
import { ElMessage } from 'element-plus';
import flvjs from 'flv.js';

// --- 1. 状态和引用 (Refs) ---
const videoRef = ref(null);
const canvasRef = ref(null); // Ref for the canvas element
let flvPlayer = null;
let detectionTimer = null;

const isDetecting = ref(false);
const isStreamReady = ref(false);
const detectionResult = ref(null);
const lastDetectionData = ref(null);
const statusMessage = ref('正在初始化...');

// 【请确认】你的流媒体地址
const streamUrl = 'http://119.3.214.158:8080/live/phone.flv';

const statusTagType = computed(() => {
  if (!isStreamReady.value) return 'info';
  if (isDetecting.value) return 'primary';
  return 'success';
});

// --- 2. 视频流处理 ---
function setupFlvPlayer() {
  if (!flvjs.isSupported()) {
    statusMessage.value = '浏览器不支持FLV';
    return;
  }
  const videoElement = videoRef.value;
  if (!videoElement) {
    console.error("无法获取到 video DOM 元素。");
    return;
  }
  destroyFlvPlayer();
  statusMessage.value = '正在连接视频流...';

  flvPlayer = flvjs.createPlayer({
    type: 'flv',
    isLive: true,
    url: streamUrl
  });
  flvPlayer.attachMediaElement(videoElement);
  flvPlayer.load();
  videoElement.play().catch(e => console.warn("自动播放被阻止:", e));

  flvPlayer.on(flvjs.Events.ERROR, (errType, errDetail) => {
    console.error('FLV.js 错误:', errType, errDetail);
    statusMessage.value = `视频流错误: ${errDetail}`;
    isStreamReady.value = false;
     destroyFlvPlayer();
  });

  videoElement.addEventListener('loadedmetadata', () => {
    isStreamReady.value = true;
    statusMessage.value = '视频流已就绪';
  }, { once: true });
}

function destroyFlvPlayer() {
  if (flvPlayer) {
    console.log("【FLV.js】正在销毁播放器...");
    flvPlayer.pause(); // 暂停播放
    flvPlayer.unload(); // 卸载媒体
    flvPlayer.detachMediaElement(); // 脱离媒体元素
    flvPlayer.destroy(); // 销毁实例
    flvPlayer = null; // 【关键】置为 null，清除引用
    isStreamReady.value = false;
    statusMessage.value = '视频流已断开';
    console.log("【FLV.js】播放器已销毁。");
  }
}

// --- 3. 检测逻辑 ---
function startDetection() {
  if (!isStreamReady.value) {
    ElMessage.warning('请等待视频流准备就绪。');
    return;
  }
  isDetecting.value = true;
  lastDetectionData.value = null;
  statusMessage.value = '正在进行姿态检测...';

  performDetection();
  detectionTimer = setInterval(performDetection, 3000); // 调整检测频率
}

function stopDetection() {
  if (detectionTimer) {
    clearInterval(detectionTimer);
    detectionTimer = null;
  }
  isDetecting.value = false;
  statusMessage.value = isStreamReady.value ? '视频流已就绪' : '视频流未连接';
  clearCanvas();
}

async function performDetection() {
  const videoElement = videoRef.value;
  if (!videoElement || videoElement.videoWidth === 0) return;

  const MAX_WIDTH = 640; // 减小尺寸
  const tempCanvas = document.createElement('canvas');
  const scale = MAX_WIDTH / videoElement.videoWidth;
  tempCanvas.width = MAX_WIDTH;
  tempCanvas.height = videoElement.videoHeight * scale;
  const context = tempCanvas.getContext('2d');
  context.drawImage(videoElement, 0, 0, tempCanvas.width, tempCanvas.height);

  const imageBase64 = tempCanvas.toDataURL('image/jpeg', 0.8); // 降低质量

  try {
    const response = await http.post('/detection', { image: imageBase64 },{ // 这是 axios 的第三个参数：config 对象
        headers: {
            // 手动、明确地告诉 axios，这次请求的内容是 JSON
            'Content-Type': 'application/json'
        }});

    console.log('%c检测成功，后端响应:', 'color: green;', response);


    const persons = response.data?.persons;

    if (persons && Array.isArray(persons)) {
      lastDetectionData.value = response.data; // 保存原始数据以供展示
      drawDetections(persons); // 把 persons 数组传给绘制函数
    } else {
      // 防御性编程：如果后端返回的 data 结构不符合预期
      console.warn("后端返回的数据格式不正确，缺少 persons 数组:", response);
      clearCanvas(); // 清空画布，避免显示旧的检测框
    }

  } catch (error) {
    console.error("检测请求在 catch 块中失败:", error);
    stopDetection();
  }
}

// --- 4. 绘制功能 ---
// --- 绘制功能 (核心修改区) ---
function drawDetections(persons) {
  const video = videoRef.value;
  const canvas = canvasRef.value;
  if (!video || !canvas) return;

  const ctx = canvas.getContext('2d');
  canvas.width = video.clientWidth;
  canvas.height = video.clientHeight;

  const originalImageWidth = 640;
  const originalImageHeight = video.videoHeight * (originalImageWidth / video.videoWidth);
  const scaleX = canvas.width / originalImageWidth;
  const scaleY = canvas.height / originalImageHeight;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // 检查 persons 是否为数组，然后遍历
  if (!Array.isArray(persons)) return;

  persons.forEach(person => {
    // 从 person 对象解构数据
    const [xmin, ymin, xmax, ymax] = person.box;
    const pose = person.pose;
    const confidence = person.confidence;

    // 计算在 canvas 上的实际坐标
    const x = xmin * scaleX;
    const y = ymin * scaleY;
    const width = (xmax - xmin) * scaleX;
    const height = (ymax - ymin) * scaleY;

    let color = 'rgba(200, 200, 200, 0.7)'; // 默认颜色：灰色，用于不关心的物体
    const label = `${pose} ${(confidence * 100).toFixed(0)}%`;
    let shouldDraw = true; // 是否要绘制这个框

    // 根据姿态（类别）设置不同颜色
    switch (pose) {
        case 'stand':
            color = 'limegreen';
            break;
        case 'sit':
            color = 'orange';
            break;
        case 'run':
            color = '#e63946'; // 醒目的红色
            break;
        case 'fall':
            color = '#d90429'; // 最危险的深红色
            break;
        case 'fire':
            color = '#FF4500'; // 使用火橙色
            break;
        default:
            shouldDraw = false;

    }

    // 如果不满足绘制条件，直接跳过
    if (!shouldDraw) {
        return;
    }

    // 绘制矩形框
    ctx.strokeStyle = color;
    ctx.lineWidth = 3; // 加粗一点更清晰
    ctx.strokeRect(x, y, width, height);

    // 绘制标签
    ctx.fillStyle = color;
    const fontSize = Math.max(16, canvas.width / 50); // 动态调整字体大小
    ctx.font = `bold ${fontSize}px Arial`;
    const textWidth = ctx.measureText(label).width;
    const textHeight = fontSize * 1.2;

    ctx.fillRect(x, y - textHeight, textWidth + 8, textHeight); // 背景
    ctx.fillStyle = 'white';
    ctx.fillText(label, x + 4, y - (textHeight / 2) + (fontSize/2) - 2); // 文字垂直居中
  });
}

function clearCanvas() {
  const canvas = canvasRef.value;
  if (canvas) {
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }
}

// --- 5. 生命周期钩子 ---
onMounted(() => {
  nextTick(() => {
    setupFlvPlayer();
  });
});

onBeforeUnmount(() => {
  stopDetection();
  destroyFlvPlayer();
});
</script>

<style scoped>
.header p {
  margin-top: 0.5rem;
}

/* 视频容器，使用 position: relative 作为子元素的定位基准 */
.video-container {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9; /* 强制16:9的宽高比，避免布局错乱 */
  background-color: #000;
  overflow: hidden;
  border-radius: 4px;
}

/* 视频和Canvas都绝对定位，铺满父容器 */
.video-container video,
.video-container .overlay-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain; /* 保持内容原始比例 */
}

/* Canvas 在顶层，且不响应鼠标事件 */
.overlay-canvas {
  z-index: 10;
  pointer-events: none;
}

.controls {
  margin-top: 1rem;
}

.result-display {
  margin-top: 1rem;
  padding: 1rem;
  border-top: 1px solid #eee;
  background-color: #f8f9fa;
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
}

.result-display pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: Consolas, 'Courier New', monospace;
  margin: 0;
}
</style>