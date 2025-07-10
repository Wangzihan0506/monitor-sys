<template>
  <div class="zone-monitor">
    <div id="controls">
      <el-button type="primary" @click="enableDrawZone">绘制监控区域</el-button>
    </div>
    <video ref="video" autoplay muted></video>
    <canvas ref="canvas"></canvas>
    <div ref="zone" id="zone"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, h } from 'vue'
import * as cocoSsd from '@tensorflow-models/coco-ssd'
import '@tensorflow/tfjs'
import { ElMessage } from 'element-plus'
import { alarmNotify } from '@/utils/alarmNotify'

const video = ref(null)
const canvas = ref(null)
const zone = ref(null)
let ctx = null
let model = null
let zoneRect = null
let isDetecting = false
let hasAlarmed = false // 防止重复弹窗

onMounted(async () => {
  await nextTick()
  video.value.addEventListener('loadedmetadata', () => {
    // 这里设置的是 canvas 的“属性”宽高，保证绘制不变形
    canvas.value.width = video.value.videoWidth
    canvas.value.height = video.value.videoHeight
  })
  ctx = canvas.value.getContext('2d')

  const cameraReady = await setupCamera()
  if (!cameraReady) return

  model = await cocoSsd.load()
  console.log('model loaded', model)

  // 直接判断 video 是否 ready，直接启动 detectFrame
  if (video.value.readyState >= 2) { // HAVE_CURRENT_DATA
    if (!isDetecting) {
      isDetecting = true
      detectFrame()
    }
  } else {
    video.value.addEventListener('loadeddata', () => {
      console.log('video loadeddata')
      if (!isDetecting) {
        isDetecting = true
        detectFrame()
      }
    })
  }
})

async function setupCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true })
    video.value.srcObject = stream
    return new Promise(resolve => {
      video.value.onloadedmetadata = () => {
        resolve(true)
      }
    })
  } catch (err) {
    ElMessage.error('无法访问摄像头')
    return false
  }
}

function drawRect([x, y, width, height], label, color = 'green') {
  if (!ctx) return
  ctx.strokeStyle = color
  ctx.lineWidth = 2
  ctx.strokeRect(x, y, width, height)
  ctx.fillStyle = color
  ctx.font = '16px Arial'
  ctx.fillText(label, x, y > 10 ? y - 5 : 10)
}

function boxesIntersect(boxA, boxB) {
  return !(
    boxA.x > boxB.x + boxB.width ||
    boxA.x + boxA.width < boxB.x ||
    boxA.y > boxB.y + boxB.height ||
    boxA.y + boxA.height < boxB.y
  )
}

function isIntersectingZone(box) {
  if (!zoneRect) return false
  const [x, y, w, h] = box
  const personBox = { x, y, width: w, height: h }
  return boxesIntersect(personBox, zoneRect)
}

async function detectFrame() {
  console.log('detectFrame running')
  if (!video.value || video.value.readyState !== 4) {
    requestAnimationFrame(detectFrame)
    return
  }
  if (!model) {
    console.log('模型未加载')
    requestAnimationFrame(detectFrame)
    return
  }
  if (!video.value.srcObject) {
    console.log('摄像头未就绪')
    requestAnimationFrame(detectFrame)
    return
  }
  const predictions = await model.detect(video.value)
  console.log('predictions:', predictions)
  ctx.clearRect(0, 0, canvas.value.width, canvas.value.height)

  predictions.forEach(pred => {
    if (pred.class === 'person') {
      const color = isIntersectingZone(pred.bbox) ? 'red' : 'green'
      drawRect(pred.bbox, pred.class + ' ' + Math.round(pred.score * 100) + '%', color)
      // 进入违规区域时弹窗
      if (isIntersectingZone(pred.bbox) && !hasAlarmed) {
        hasAlarmed = true
        alarmNotify({
          title: '告警',
          message: h('div', '进入违规区域'),
          type: 'error',
          duration: 4000
        })
        setTimeout(() => { hasAlarmed = false }, 5000)
      }
    }
  })

  requestAnimationFrame(detectFrame)
}

function enableDrawZone() {
  let startX, startY
  function onMouseDown(e) {
    startX = e.offsetX
    startY = e.offsetY
    zone.value.style.left = startX + 'px'
    zone.value.style.top = startY + 'px'
    zone.value.style.width = '0px'
    zone.value.style.height = '0px'

    function onMouseMove(e) {
      const width = e.offsetX - startX
      const height = e.offsetY - startY
      zone.value.style.width = Math.abs(width) + 'px'
      zone.value.style.height = Math.abs(height) + 'px'
      zone.value.style.left = (width < 0 ? e.offsetX : startX) + 'px'
      zone.value.style.top = (height < 0 ? e.offsetY : startY) + 'px'
    }

    function onMouseUp() {
      zoneRect = {
        x: parseInt(zone.value.style.left),
        y: parseInt(zone.value.style.top),
        width: parseInt(zone.value.style.width),
        height: parseInt(zone.value.style.height)
      }
      canvas.value.removeEventListener('mousemove', onMouseMove)
      canvas.value.removeEventListener('mouseup', onMouseUp)
    }

    canvas.value.addEventListener('mousemove', onMouseMove)
    canvas.value.addEventListener('mouseup', onMouseUp)
  }
  canvas.value.addEventListener('mousedown', onMouseDown)
}
</script>

<style scoped>
.zone-monitor {
  position: relative;
  width: 100%;
  height: 100%;
}

video,
canvas,
#zone {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

video {
  z-index: 1;
  object-fit: cover;
}

canvas {
  z-index: 2;
}

#zone {
  z-index: 3;
  border: 2px dashed red;
  pointer-events: none;
}

#controls {
  position: absolute;
  top: 10px;
  left: 10px;
  background: white;
  padding: 10px;
  z-index: 999;
}

/* 让 ZoneMonitor 的根元素填满卡片 */
.zone-full {
  width: 100%;
  height: 600px; /* 或改为 100% 如果你希望动态自适应卡片区域 */
  position: relative;
}

</style>
