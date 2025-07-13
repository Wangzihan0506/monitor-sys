<template>
  <div class="zone-monitor">
    <!-- 控制面板 -->
    <div class="controls-panel">
      <el-button type="primary" @click="enableDrawZone">绘制危险区域</el-button>
      <div class="slider-item">
        <span>停留告警(秒):</span>
        <el-slider v-model="intrusionSettings.lingerTime" :min="1" :max="30" show-input size="small"></el-slider>
      </div>
       <!-- 距离告警功能较复杂，暂不加入滑块，未来可扩展 -->
    </div>

    <!-- 视频和画布容器 -->
    <div class="video-wrapper">
      <video ref="videoRef" autoplay playsinline muted></video>
      <canvas ref="canvasRef"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, reactive,h } from 'vue';
import * as cocoSsd from '@tensorflow-models/coco-ssd';
import '@tensorflow/tfjs-core';
import '@tensorflow/tfjs-backend-webgl';
import { ElMessage, ElNotification } from 'element-plus';
import '@tensorflow/tfjs-backend-cpu';


// --- Refs and State ---
const videoRef = ref(null);
const canvasRef = ref(null);
let model = null;
let detectionInterval = null;

// --- 危险区域和入侵检测状态 ---
const dangerousZone = ref(null); // { x, y, width, height }
const trackedPersons = reactive(new Map()); // 跟踪进入区域的人的状态

// --- 可配置的告警设置 ---
const intrusionSettings = reactive({
  lingerTime: 5, // 停留超过5秒告警
  // proximityThreshold: 50, // 靠近边缘50像素告警 (高级功能，暂缓)
});

// --- 组件生命周期 ---
onMounted(async () => {

   if (videoRef.value) {
    videoRef.value.addEventListener('play', onPlay);
  }

  try {
    ElMessage.info('正在加载物体检测模型...');
    model = await cocoSsd.load();
    ElMessage.success('模型加载完成!');
    await startCamera();
  } catch (error) {
    console.error("初始化失败:", error);
    ElMessage.error('模型或摄像头初始化失败!');
  }
});

onUnmounted(() => {
  clearInterval(detectionInterval);
  stopCamera();
  if (videoRef.value) {
      videoRef.value.removeEventListener('play', onPlay);
  }
});

// --- 核心功能函数 ---
// --- 【请使用这个修复后的版本】 ---
async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    videoRef.value.srcObject = stream;
    // 这里不再需要 addEventListener 了
    await videoRef.value.play();
  } catch (err) {
    console.error("摄像头启动失败:", err);
    ElMessage.error('无法访问摄像头');
  }
}

function stopCamera() {
  if (videoRef.value && videoRef.value.srcObject) {
    videoRef.value.srcObject.getTracks().forEach(track => track.stop());
  }
}

function onPlay() {
  // 设置画布尺寸与视频显示尺寸一致
  canvasRef.value.width = videoRef.value.clientWidth;
  canvasRef.value.height = videoRef.value.clientHeight;
  // 启动检测循环
  detectionInterval = setInterval(detectFrame, 200); // 提高检测频率以获得更及时的反馈
}

async function detectFrame() {

  if (!model) {
    console.log("中断原因：模型 (model) 尚未加载");
    return;
  }
  if (!videoRef.value) {
    console.log("中断原因：视频引用 (videoRef) 为空");
    return;
  }
  if (videoRef.value.paused) {
    console.log("中断原因：视频已暂停 (paused)");
    return;
  }

  const video = videoRef.value;
  const canvas = canvasRef.value;
  const ctx = canvas.getContext('2d');

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  drawDangerousZone(ctx, canvas, video); // 我把之前让你加的日志放在这个函数里了

  // 后续的物体检测代码
  const predictions = await model.detect(video);
  const persons = predictions.filter(p => p.class === 'person' && p.score > 0.6);

  updateTrackedPersons(persons);
  drawDetections(persons, ctx, canvas);
}

// --- 区域绘制与交互 ---
function enableDrawZone() {

  trackedPersons.clear();
  console.log("【新区域绘制】已清空所有人员跟踪状态。");

  const canvas = canvasRef.value;
  let startPos = null;
  const tempZoneDiv = document.createElement('div');
  tempZoneDiv.className = 'temp-draw-zone';
  canvas.parentElement.appendChild(tempZoneDiv);

  const onMouseDown = (e) => {
    startPos = { x: e.offsetX, y: e.offsetY };
    tempZoneDiv.style.left = `${startPos.x}px`;
    tempZoneDiv.style.top = `${startPos.y}px`;
    tempZoneDiv.style.width = '0px';
    tempZoneDiv.style.height = '0px';
    canvas.addEventListener('mousemove', onMouseMove);
  };

  const onMouseMove = (e) => {
    const width = e.offsetX - startPos.x;
    const height = e.offsetY - startPos.y;
    tempZoneDiv.style.width = `${Math.abs(width)}px`;
    tempZoneDiv.style.height = `${Math.abs(height)}px`;
    tempZoneDiv.style.left = `${width < 0 ? e.offsetX : startPos.x}px`;
    tempZoneDiv.style.top = `${height < 0 ? e.offsetY : startPos.y}px`;
  };

  const onMouseUp = () => {
    // 将显示坐标转换为视频原始坐标进行存储
    const video = videoRef.value;
    const scaleX = video.videoWidth / canvas.clientWidth;
    const scaleY = video.videoHeight / canvas.clientHeight;

    dangerousZone.value = {
      x: parseInt(tempZoneDiv.style.left) * scaleX,
      y: parseInt(tempZoneDiv.style.top) * scaleY,
      width: parseInt(tempZoneDiv.style.width) * scaleX,
      height: parseInt(tempZoneDiv.style.height) * scaleY,
    };

    // 清理
    canvas.removeEventListener('mousedown', onMouseDown);
    canvas.removeEventListener('mousemove', onMouseMove);
    canvas.parentElement.removeChild(tempZoneDiv);
    ElMessage.success('危险区域设置成功!');
  };

  canvas.addEventListener('mousedown', onMouseDown);
  canvas.addEventListener('mouseup', onMouseUp, { once: true });
  ElMessage.info('请在视频区域拖拽鼠标以绘制危险区域。');
}

// --- 状态更新与告警逻辑 ---
function updateTrackedPersons(persons) {
  // --- 日志 1: 检查函数入口 ---
  console.log(`\n--- [${new Date().toLocaleTimeString()}] updateTrackedPersons: 检测到 ${persons.length} 个人 ---`);

  if (!dangerousZone.value) {
    // 如果没有设置区域，就不需要打印后续日志了
    return;
  }

  const currentTime = Date.now();
  const detectedPersonIds = new Set();

  for (const person of persons) {
    const [px, py, pw, ph] = person.bbox;
    const personBox = { x: px, y: py, width: pw, height: ph };
    // 使用一个更稳定的ID，因为坐标可能会有微小抖动
    const personId = `person-${Math.round(px / 50)}-${Math.round(py / 50)}`;
    detectedPersonIds.add(personId);

    // --- 日志 2: 检查相交判断 ---
    const intersects = isIntersecting(personBox, dangerousZone.value);
    console.log(`  - 正在检查 ID: ${personId}, 是否相交: ${intersects}`);

    if (intersects) {
      if (!trackedPersons.has(personId)) {
        // --- 日志 3: 新人进入 ---
        console.log(`    >> [新发现!] ID: ${personId} 进入区域，开始计时。`);
        sendAlarm('人员进入危险区域！');
        trackedPersons.set(personId, {
          startTime: currentTime,
          hasLingered: false,
          bbox: person.bbox,
        });
      } else {
        // --- 日志 4: 已在区域内的人 ---
        const personState = trackedPersons.get(personId);
        personState.bbox = person.bbox; // 更新位置
        const lingerDuration = (currentTime - personState.startTime) / 1000;

        console.log(`    >> [跟踪中] ID: ${personId} 已停留 ${lingerDuration.toFixed(1)} 秒。告警阈值: ${intrusionSettings.lingerTime}秒。`);

        if (lingerDuration > intrusionSettings.lingerTime && !personState.hasLingered) {
          // --- 日志 5: 触发停留告警 ---
          console.log(`      !!!! [触发停留告警!] ID: ${personId} 停留时间超限！`);
          sendAlarm(
            `人员在危险区域停留超过 ${intrusionSettings.lingerTime} 秒！`,
            `实际停留: ${lingerDuration.toFixed(1)} 秒`
          );
          personState.hasLingered = true; // 标记已告警
        }
      }
    }
  }

  // --- 日志 6: 移除离开的人 ---
  for (const id of trackedPersons.keys()) {
    if (!detectedPersonIds.has(id)) {
      console.log(`  - [人员离开] ID: ${id} 已离开危险区域，从跟踪列表移除。`);
      trackedPersons.delete(id);
    }
  }
}

function isIntersecting(boxA, boxB) {
  return !(
    boxA.x > boxB.x + boxB.width ||
    boxA.x + boxA.width < boxB.x ||
    boxA.y > boxB.y + boxB.height ||
    boxA.y + boxA.height < boxB.y
  );
}

// --- 绘制函数 ---
function drawDangerousZone(ctx, canvas, video) {
  console.log("正在尝试绘制危险区域...");
  if (!dangerousZone.value) return;
  // 将存储的原始坐标转换回显示坐标进行绘制
  const scaleX = canvas.clientWidth / video.videoWidth;
  const scaleY = canvas.clientHeight / video.videoHeight;

  const { x, y, width, height } = dangerousZone.value;
  const drawX = x * scaleX;
  const drawY = y * scaleY;
  const drawWidth = width * scaleX;
  const drawHeight = height * scaleY;

   if (isNaN(drawX) || isNaN(drawY) || isNaN(drawWidth) || isNaN(drawHeight) || drawWidth <= 0 || drawHeight <= 0) {
      console.error("危险区域绘制参数无效，取消绘制。");
      return;
  }


  ctx.strokeStyle = 'rgba(255, 0, 0, 0.7)';
  ctx.fillStyle = 'rgba(255, 0, 0, 0.2)';
  ctx.lineWidth = 3;
  ctx.strokeRect(drawX, drawY, drawWidth, drawHeight);
  ctx.fillRect(drawX, drawY, drawWidth, drawHeight);
}

function drawDetections(persons, ctx, canvas,video) {
  if (!video) return;
  const scaleX = canvas.clientWidth / video.videoWidth;
  const scaleY = canvas.clientHeight / video.videoHeight;

  persons.forEach(person => {
    const [x, y, width, height] = person.bbox;
    const personBox = { x, y, width, height };

    // 判断是否在区域内来决定颜色
    const color = dangerousZone.value && isIntersecting(personBox, dangerousZone.value) ? 'red' : 'limegreen';

    const drawX = x * scaleX;
    const drawY = y * scaleY;
    const drawWidth = width * scaleX;
    const drawHeight = height * scaleY;

    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.strokeRect(drawX, drawY, drawWidth, drawHeight);
  });
}

// --- 告警通知 ---
let lastAlarmTime = 0;
function sendAlarm(title, description = '') {
  const now = Date.now();
  // 告警节流，3秒内不重复发送同类型告警
  if (now - lastAlarmTime < 3000) return;
  lastAlarmTime = now;
   ElNotification({
    title: '危险区域告警',
    // 使用 h 函数创建更复杂的通知内容
    message: h('div', null, [
      h('p', { style: 'font-weight: bold; margin: 0;' }, title), // 主要信息加粗
      description ? h('p', { style: 'font-size: 12px; margin: 5px 0 0 0;' }, description) : null // 如果有描述，就显示它
    ]),
    type: 'error',
    duration: 4000,
  });
}

</script>

<style>
/* 添加一个用于绘制时临时显示的div的样式 */
.temp-draw-zone {
  position: absolute;
  border: 2px dashed #409EFF;
  background-color: rgba(64, 158, 255, 0.2);
  z-index: 10;
  pointer-events: none; /* 确保不影响下层canvas的鼠标事件 */
}
</style>

<style scoped>
.zone-monitor {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 600px; /* 或者你需要的固定高度 */
  background-color: #f0f2f5;
}

.controls-panel {
  display: flex;
  align-items: center;
  padding: 10px;
  background-color: #fff;
  border-bottom: 1px solid #dcdfe6;
}

.slider-item {
  display: flex;
  align-items: center;
  margin-left: 20px;
  width: 300px;
}

.slider-item span {
  font-size: 14px;
  margin-right: 10px;
  white-space: nowrap;
}

.video-wrapper {
  flex-grow: 1;
  position: relative;
  overflow: hidden;
}

video, canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover; /* 视频铺满容器 */
}
</style>
