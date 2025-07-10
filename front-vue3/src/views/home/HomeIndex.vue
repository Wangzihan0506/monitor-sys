<template>
    <div class="face-checkin">
        <el-row class="container" :gutter="20">
            <!-- 地图区域 -->
            <el-col :span="16">
                <el-card class="map-card" shadow="never">
                    <div id="map-container" class="map-container"></div>
                </el-card>
            </el-col>

            <!-- 控制与记录区域 -->
            <el-col :span="8">
                <el-card class="control-card" shadow="never">
                    <!-- 视频预览，仅在摄像头开启后显示 -->
                    <div class="video-wrapper" v-show="streaming">
                        <video ref="videoRef" class="video-feed" autoplay playsinline></video>
                        <canvas ref="canvasRef" style="display: none;"></canvas>
                    </div>

                    <!-- 签到按钮：首次点击开启摄像头，后续点击拍照并签到 -->
                    <el-button type="primary" :loading="loading" @click="handleSign">
                        {{ streaming ? '拍照并签到' : '开启摄像头并签到' }}
                    </el-button>

                    <!-- 显示签到结果与地址 -->
                    <div v-if="signResult">
                        <el-alert title="签到成功" type="success" :description="signResult" show-icon />
                    </div>

                    <el-divider />

                    <!-- 查看签到记录功能 -->
                    <el-button type="info" @click="fetchRecords">
                        查看签到记录
                    </el-button>
                </el-card>

                <!-- 历史记录表格 + 分页 -->
                <el-card class="records-card" v-if="records.length">
                    <el-table :data="records" stripe style="width: 100%; margin-top: 16px;">
                        <el-table-column prop="employeeName" label="姓名" />
                        <el-table-column prop="signTime" label="时间" />
                        <el-table-column prop="address" label="地址" />
                    </el-table>

                    <el-pagination background layout="total, sizes, prev, pager, next, jumper"
                        :page-sizes="[10, 20, 50, 100]" :current-page="page" :page-size="perPage" :total="total"
                        @current-change="handlePageChange" @size-change="handleSizeChange"
                        style="margin: 16px 0; text-align: right;" />
                </el-card>
            </el-col>
        </el-row>
    </div>
</template>

<script setup>
/* global BMapGL */
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/utils/http'

// 元素引用
const videoRef = ref(null)
const canvasRef = ref(null)

// 状态管理
const loading = ref(false)
const streaming = ref(false)
const signResult = ref('')
const records = ref([])

// 分页相关
const page = ref(1)
const perPage = ref(5)
const total = ref(0)

// 地图与地理编码
let mapInstance = null
let geocoder = null

// 保存摄像头轨道，方便关闭
const streamTracks = []

/** 初始化地图与定位 */
function initMap() {
    mapInstance = new BMapGL.Map('map-container')
    const defaultPoint = new BMapGL.Point(116.404, 39.915)
    mapInstance.centerAndZoom(defaultPoint, 15)
    mapInstance.enableScrollWheelZoom()
    geocoder = new BMapGL.Geocoder()

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            ({ coords }) => {
                const pt = new BMapGL.Point(coords.longitude, coords.latitude)
                mapInstance.panTo(pt)
                mapInstance.addOverlay(new BMapGL.Marker(pt))
            },
            err => console.warn('无法获取地理位置：', err)
        )
    }
}

/** 开启摄像头流 */
async function startVideo() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true })
        if (videoRef.value) {
            videoRef.value.srcObject = stream
            stream.getTracks().forEach(track => streamTracks.push(track))
            streaming.value = true
        }
    } catch (e) {
        ElMessage.error('无法访问摄像头，请检查权限')
        throw e
    }
}

/** 抓拍并签到 */
async function captureAndCheckIn() {
    const video = videoRef.value
    const canvas = canvasRef.value
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    const imageBase64 = canvas.toDataURL('image/jpeg')

    const center = mapInstance.getCenter()
    const payload = {
        image: imageBase64,
        latitude: center.lat,
        longitude: center.lng,
    }

    const response = await http.post(
        'attendance/checkin',
        payload,
        { withCredentials: true }
    )

    // 通过地理编码获取地名，并组装显示
    geocoder.getLocation(
        new BMapGL.Point(center.lng, center.lat),
        result => {
            const comp = result?.addressComponents || {}
            const street = comp.street || ""
            const streetNo = comp.streetNumber || ""
            const district = comp.district || ""
            let placeName = street ? `${street}${streetNo}` : district
            //const comp = result?.addressComponents
            // let placeName = comp?.street
            // ? `${comp.street}${comp.streetNumber}`
            // : `${comp.district}`
            if (!placeName) {
                placeName = `经度:${center.lng.toFixed(6)}, 纬度:${center.lat.toFixed(6)}`
            }
            signResult.value = `
          ${response.data.employeeName} 于 ${response.data.signTime}
          在 ${placeName} 签到
        `.trim()
        }
    )
}

/** 按钮点击处理：首次打开摄像头，再次点击抓拍签到 */
async function handleSign() {
    if (!streaming.value) {
        try {
            await startVideo()
        } catch {
            return
        }
    } else {
        loading.value = true
        try {
            await captureAndCheckIn()
            ElMessage.success('签到成功')
        } catch (e) {
            const msg = e.response?.data?.message || e.message || '签到失败'
            ElMessage.error(msg)
        } finally {
            // 关闭摄像头
            streamTracks.forEach(track => track.stop())
            streaming.value = false
            loading.value = false
        }
    }
}

/** 获取签到历史记录（支持分页） */
async function fetchRecords(p = page.value) {
    // 1. 确保 pageNo 始终为整数，且大于等于 1
    let pageNo = parseInt(p, 10);
    if (isNaN(pageNo) || pageNo < 1) {
        pageNo = 1;
    }
    page.value = pageNo;

    try {
        const res = await http.get(
            '/attendance/records/user',
            {
                params: {
                    page: page.value,
                    per_page: perPage.value,
                },
                withCredentials: true,
            }
        );
        // 2. 检查后端返回值结构是否正确
        if (!Array.isArray(res.data.records)) {
            console.error('后端返回的 records 不是数组：', res.data.records);
            ElMessage.error('签到记录格式异常');
            return;
        }
        // 3. 将 records、total、page 分别赋值到对应的响应式变量
        records.value = res.data.records;
        total.value = res.data.total;
        
    } catch (err) {
        console.error('fetchRecords 失败：', err);
        ElMessage.error('获取签到记录失败');
    }
}




/** 分页页码变化回调 */
function handlePageChange(newPage) {
    fetchRecords(newPage)
}

/** 每页数量变化回调 */
function handleSizeChange(newSize) {
    perPage.value = newSize
    fetchRecords(page.value)
}

onMounted(() => {
    initMap()
    // 可选：自动加载第一页记录
    // fetchRecords()
})

onBeforeUnmount(() => {
    streamTracks.forEach(track => track.stop())
})
</script>

<style scoped>
.face-checkin {
    padding: 24px;
    background: #f0f2f5;
}

.container {
    min-height: 80vh;
}

.map-card,
.control-card,
.records-card {
    background: #ffffff;
    border-radius: 8px;
}

.map-container {
    width: 100%;
    height: 60vh;
    border-radius: 8px;
}

.video-feed {
    width: 100%;
    height: auto;
    border: 2px solid #409eff;
    border-radius: 4px;
    margin-bottom: 12px;
}

.el-button {
    width: 100%;
    margin-top: 12px;
}

.el-alert {
    margin: 16px 0;
}
</style>
