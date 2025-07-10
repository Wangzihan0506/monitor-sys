<template>
  <div class="zone-monitor">
    <div id="controls">
      <el-button type="primary" @click="enableDrawZone">绘制监控区域</el-button>
    </div>
    <video ref="video" width="640" height="480" autoplay muted></video>
    <canvas ref="canvas" width="640" height="480"></canvas>
    <div ref="zone" id="zone"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as cocoSsd from '@tensorflow-models/coco-ssd'
import '@tensorflow/tfjs'
import { ElMessage } from 'element-plus'

const video = ref(null)
const canvas = ref(null)
const zone = ref(null)
let ctx = null
let model = null
let zoneRect = null
let isDetecting = false

onMounted(async () => {
  await nextTick() // 确保 DOM 已挂载
  ctx = canvas.value.getContext('2d')

  const cameraReady = await setupCamera()
  if (!cameraReady) return

  model = await cocoSsd.load()

  // 等待 video 加载完成后再开始识别
  video.value.addEventListener('loadeddata', () => {
    if (!isDetecting) {
      isDetecting = true
      detectFrame()
    }
  })
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
  if (!video.value || video.value.readyState !== 4) {
    requestAnimationFrame(detectFrame)
    return
  }

  const predictions = await model.detect(video.value)
  ctx.clearRect(0, 0, canvas.value.width, canvas.value.height)

  predictions.forEach(pred => {
    if (pred.class === 'person') {
      const color = isIntersectingZone(pred.bbox) ? 'red' : 'green'
      drawRect(pred.bbox, pred.class + ' ' + Math.round(pred.score * 100) + '%', color)
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
  display: flex;
  flex-direction: column;
}

video,
canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

#zone {
  position: absolute;
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
