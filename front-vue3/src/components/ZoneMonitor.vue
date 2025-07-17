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
      <video ref="videoElement" autoplay playsinline muted></video>
      <canvas ref="canvasRef"></canvas>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, reactive,h } from 'vue';
import * as cocoSsd from '@tensorflow-models/coco-ssd';
import '@tensorflow/tfjs-core';
import '@tensorflow/tfjs-backend-webgl';
import { ElMessage, ElNotification} from 'element-plus';
import '@tensorflow/tfjs-backend-cpu';
import flvjs from 'flv.js';
import axios from 'axios';

// --- Refs and State ---
const videoElement = ref(null);
const canvasRef = ref(null);
const streamUrl = 'http://119.3.214.158:8080/live/detection.flv';
const backendBaseUrl = 'http://127.0.0.1:5000/api';
let model = null;
let detectionInterval = null;
let flvPlayer = null; // 【核心修改】flvPlayer 实例移到这里

// --- 危险区域和入侵检测状态 ---
const dangerousZone = ref(null); // { x, y, width, height }
const trackedPersons = reactive(new Map()); // 跟踪进入区域的人的状态

// --- 可配置的告警设置 ---
const intrusionSettings = reactive({
  lingerTime: 5, // 默认是停留超过5秒告警
});

const localAlarms = reactive([]);

// --- 组件生命周期 ---
onMounted(async () => {
  if (videoElement.value) { // 绑定到本地 <video> 标签的 ref
    videoElement.value.addEventListener('loadedmetadata', onMetadataLoaded);
    videoElement.value.addEventListener('play', onPlay);
  }

  try {
    ElMessage.info('ZoneMonitor: 正在加载物体检测模型...');
    model = await cocoSsd.load();
    ElMessage.success('ZoneMonitor: 模型加载完成!');
    startStream(); // 【核心修改】直接在这里启动流
  } catch (error) {
    console.error("ZoneMonitor 初始化失败:", error);
    ElMessage.error('ZoneMonitor: 模型加载失败!');
  }
});

onUnmounted(() => {
  console.log("ZoneMonitor: 组件卸载，清除检测定时器和本地视频显示。");
  clearInterval(detectionInterval);
  detectionInterval = null;
  destroyFlvPlayer(); // 【核心修改】销毁 flvPlayer
  if (videoElement.value) {
    videoElement.value.removeEventListener('loadedmetadata', onMetadataLoaded);
    videoElement.value.removeEventListener('play', onPlay);
  }
});

function onMetadataLoaded() {
  const video = videoElement.value;
  const canvas = canvasRef.value;
  if (!video || !canvas) return;

  console.log(`视频元数据加载完成! 原始尺寸: ${video.videoWidth}x${video.videoHeight}`);

  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;

  if (video.videoWidth > 0 && video.videoHeight > 0 && !detectionInterval) {
    console.log("视频尺寸有效，正式启动检测循环...");
    detectionInterval = setInterval(detectFrame, 200);
  }
}

function onPlay() {
  const video = videoElement.value;
  if (!video) return;
  console.log("视频事件: play");

  // 尝试启动循环（如果它因为某种原因还没启动的话）
  if (video.videoWidth > 0 && video.videoHeight > 0 && !detectionInterval) {
    console.log("onPlay 事件触发，补充启动检测循环...");
    detectionInterval = setInterval(detectFrame, 200);
  }
}

function startStream() {
  const videoDomElement = videoElement.value; // 使用本地 ref
  if (!videoDomElement) {
    console.warn("ZoneMonitor: Video DOM element is not available yet.");
    return;
  }

  if (flvjs.isSupported()) {
    console.log("ZoneMonitor: 使用 flv.js 加载视频流...");

    // 销毁旧播放器实例，确保总是创建新的，避免状态混乱
    if (flvPlayer) {
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
    videoDomElement.play().catch(e => console.error("ZoneMonitor: 视频自动播放失败:", e));

    flvPlayer.on('error', (errType, errDetail, errInfo) => {
      console.error('ZoneMonitor: FLV.js 播放器错误:', errType, errDetail, errInfo);
      ElMessage.error(`ZoneMonitor: 视频流错误: ${errDetail} - ${errInfo.msg || '未知错误'}`);
      destroyFlvPlayer();
      setTimeout(startStream, 3000);
    });

  } else {
    ElMessage.error('ZoneMonitor: 您的浏览器不支持播放FLV视频流。');
  }
}

// 【核心修改】destroyFlvPlayer 函数 (与最初的版本类似)
function destroyFlvPlayer() {
  if (flvPlayer) {
    console.log("ZoneMonitor: 销毁 flv.js 播放器...");
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

async function detectFrame() {
  const video = videoElement.value; // <<-- 使用本地的 video 元素进行检测
  if (!model || !video || video.paused || video.videoWidth === 0) {
    return;
  }

  const canvas = canvasRef.value;
  const ctx = canvas.getContext('2d');

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  drawDangerousZone(ctx);

  const predictions = await model.detect(video);
  const persons = predictions.filter(p => p.class === 'person' && p.score > 0.6);

  updateTrackedPersons(persons);
  drawDetections(persons, ctx);
}

function captureFrameAsBase64() {
  const video = videoElement.value; // <<-- 使用本地的 video 元素进行截图
  if (!video || video.videoWidth === 0 || video.videoHeight === 0) {
    console.error("ZoneMonitor: 无法捕获帧：视频不可用或尺寸无效。");
    return null;
  }
  const tempCanvas = document.createElement('canvas');
  tempCanvas.width = video.videoWidth;
  tempCanvas.height = video.videoHeight;
  const tempCtx = tempCanvas.getContext('2d');
  tempCtx.drawImage(video, 0, 0, video.videoWidth, video.videoHeight);
  return tempCanvas.toDataURL('image/jpeg', 0.8).split(',')[1];
}

// --- 区域绘制与交互 ---
function enableDrawZone() {
  trackedPersons.clear();
  console.log("【新区域绘制】已清空所有人员跟踪状态。");

  const canvas = canvasRef.value;
  const video = videoElement.value;
  if (!video || video.videoWidth === 0 || video.videoHeight === 0) {
    ElMessage.error("视频尚未加载或尺寸无效，无法绘制区域。");
    return;
  }

  const videoAspectRatio = video.videoWidth / video.videoHeight;
  const containerWidth = canvas.clientWidth; // Canvas 和 video_wrapper 宽度一致
  const containerHeight = canvas.clientHeight; // Canvas 和 video_wrapper 高度一致
  const containerAspectRatio = containerWidth / containerHeight;

  let displayedVideoWidth;
  let displayedVideoHeight;
  let offsetX = 0; // 视频内容在容器中的X轴偏移量 (黑边)
  let offsetY = 0; // 视频内容在容器中的Y轴偏移量 (黑边)

  if (containerAspectRatio > videoAspectRatio) {
    // 容器更宽，视频会填满高度，左右留黑边
    displayedVideoHeight = containerHeight;
    displayedVideoWidth = displayedVideoHeight * videoAspectRatio;
    offsetX = (containerWidth - displayedVideoWidth) / 2;
  } else {
    displayedVideoWidth = containerWidth;
    displayedVideoHeight = displayedVideoWidth / videoAspectRatio;
    offsetY = (containerHeight - displayedVideoHeight) / 2;
  }

  const scaleX = video.videoWidth / displayedVideoWidth;
  const scaleY = video.videoHeight / displayedVideoHeight;

  let startPos = null;
  const tempZoneDiv = document.createElement('div');
  tempZoneDiv.className = 'temp-draw-zone';

  canvas.parentElement.appendChild(tempZoneDiv);

  const onMouseDown = (e) => {
    startPos = { x: e.offsetX, y: e.offsetY }; // 鼠标事件的 offsetX/Y 是相对于 canvas 元素的
    tempZoneDiv.style.left = `${startPos.x}px`;
    tempZoneDiv.style.top = `${startPos.y}px`;
    tempZoneDiv.style.width = '0px';
    tempZoneDiv.style.height = '0px';
    canvas.addEventListener('mousemove', onMouseMove);
  };

  const onMouseMove = (e) => {
    const currentX = Math.max(0, Math.min(containerWidth, e.offsetX)); // 限制在容器内
    const currentY = Math.max(0, Math.min(containerHeight, e.offsetY)); // 限制在容器内

    const rawWidth = currentX - startPos.x;
    const rawHeight = currentY - startPos.y;

    // 调整位置和宽度/高度，确保始终为正值
    tempZoneDiv.style.left = `${Math.min(startPos.x, currentX)}px`;
    tempZoneDiv.style.top = `${Math.min(startPos.y, currentY)}px`;
    tempZoneDiv.style.width = `${Math.abs(rawWidth)}px`;
    tempZoneDiv.style.height = `${Math.abs(rawHeight)}px`;
  };

  const onMouseUp = () => {
    const finalLeft = parseInt(tempZoneDiv.style.left);
    const finalTop = parseInt(tempZoneDiv.style.top);
    const finalWidth = parseInt(tempZoneDiv.style.width);
    const finalHeight = parseInt(tempZoneDiv.style.height);

    // 将显示坐标 (考虑黑边偏移) 转换成视频原始分辨率的坐标进行存储
    dangerousZone.value = {
      x: (finalLeft - offsetX) * scaleX,
      y: (finalTop - offsetY) * scaleY,
      width: finalWidth * scaleX,
      height: finalHeight * scaleY,
    };

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

  if (!dangerousZone.value) {
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

        if (lingerDuration > intrusionSettings.lingerTime && !personState.hasLingered) {
          // --- 日志 5: 触发停留告警 ---
          console.log(`      !!!! [触发停留告警!] ID: ${personId} 停留时间超限！`);
          addLocalAlarm('error', `人员在危险区域停留超过 ${intrusionSettings.lingerTime} 秒！(ID: ${personId}, 实际: ${lingerDuration.toFixed(1)} 秒)`);
          sendAlarm(
            'normal',
            `人员在危险区域停留超过 ${intrusionSettings.lingerTime} 秒！`,
            person.bbox,
            'zone_linger',
            'zone_id_placeholder'
          );
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
function drawDangerousZone(ctx) {
   if (!dangerousZone.value) return;
  // 将存储的原始坐标转换回显示坐标进行绘制

   const { x, y, width, height } = dangerousZone.value;

   if (isNaN(x) || isNaN(y) || isNaN(width) || isNaN(height) || width <= 0 || height <= 0) {

      return;
   }


   ctx.strokeStyle = 'rgba(255, 0, 0, 0.7)';
   ctx.fillStyle = 'rgba(255, 0, 0, 0.2)';
   ctx.lineWidth = 3;
   ctx.strokeRect(x, y, width, height); // 直接使用存储的原始坐标
   ctx.fillRect(x, y, width, height);   // 直接使用存储的原始坐标
}

function drawDetections(persons, ctx) {

  persons.forEach(person => {
    const [x, y, width, height] = person.bbox;
    const personBox = { x, y, width, height };
    const color = dangerousZone.value && isIntersecting(personBox, dangerousZone.value) ? 'red' : 'limegreen';

    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    // 直接用模型返回的坐标绘制
    ctx.strokeRect(x, y, width, height);
  });
}

// --- 告警通知 ---
let lastNormalAlarmSentTime = 0;
//let lastAbnormalAlarmSentTime = 0;
const ALARM_THROTTLE_SECONDS = 3;

//eventType = '',
async function sendAlarm(type, message, personBox,  zoneId = '') {
  const now = Date.now();
  let canSend = false;

  if (type === 'normal') { // 常规区域告警（进入/停留）
    if (now - lastNormalAlarmSentTime > ALARM_THROTTLE_SECONDS * 1000) {
      canSend = true;
      lastNormalAlarmSentTime = now;
    }
  }

  if (!canSend) {
    console.warn(`告警节流：${type}告警发送频率过高。`);
    return;
  }

  // 前端通知
  ElNotification({
    title: '危险区域告警', // 标题固定为危险区域告警
    message: h('div', null, [
      h('p', { style: 'font-weight: bold; margin: 0;' }, message),
      personBox ? h('p', { style: 'font-size: 12px; margin: 5px 0 0 0;' }, `目标框: ${JSON.stringify(personBox)}`) : null
    ]),
    type: 'error',
    duration: 4000,
  });

  // 截取当前帧作为告警图片
  const frameBase64 = captureFrameAsBase64();
  if (!frameBase64) {
    console.error("未能捕获告警截图，跳过后端写入。");
    return;
  }

  // 构建告警数据
  let apiUrl = '';
  let postData = {};

  if (type === 'normal') { // 危险区域告警
    apiUrl = `${backendBaseUrl}/alert_normal`;
    postData = {
      zone_id: zoneId, // 可以是固定的，或者从界面获取的区域ID
      message: message,
      person_box: JSON.stringify(personBox),
      frame_image: frameBase64,
    };
  }

  try {
    const response = await axios.post(apiUrl, postData);
    if (response.data.code === 0) {
      console.log(`常规告警已发送至后端：`, response.data.msg);
    } else {
      console.error(`常规告警发送后端失败：`, response.data.msg);
      ElMessage.error(`常规告警后端写入失败: ${response.data.msg}`);
    }
  } catch (error) {
    console.error(`发送常规告警到后端时发生错误：`, error);
    ElMessage.error(`发送常规告警到后端时发生网络错误。`);
  }
}

function addLocalAlarm(type, message) {
    const now = new Date();
    localAlarms.unshift({ // unshift 可以在数组开头添加，实现新消息在顶部
        type: type, // 'normal' 或 'error' (用于样式)
        message: message,
        time: now.toLocaleTimeString(), // 格式化时间
        fullTime: now.toISOString() // 完整时间戳，用于排序或唯一标识
    });
    // 限制列表长度，例如只保留最新的50条告警
    if (localAlarms.length > 50) {
        localAlarms.pop(); // 移除最旧的
    }
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
  object-fit: contain; /* 视频铺满容器 */
}
</style>