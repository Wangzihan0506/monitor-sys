<template>
    <el-container style="height: 100vh;">

        <el-header class="header">
            <div class="header-left">
                <el-breadcrumb separator="/">
                    <el-breadcrumb-item>后台管理</el-breadcrumb-item>
                    <el-breadcrumb-item>{{ menuMap[activeMenu] }}</el-breadcrumb-item>
                </el-breadcrumb>
            </div>

            <div class="header-right">
                <el-dropdown trigger="click">
                    <!-- 下拉触发部分 -->
                    <span class="el-dropdown-link">
                        <el-avatar icon="el-icon-user-solid" size="small"></el-avatar>
                        {{ currentUser.username }}
                        <i class="el-icon-arrow-down el-icon--small"></i>
                    </span>

                    <!-- 菜单项必须放在 #dropdown 命名插槽里 -->
                    <template #dropdown>
                        <el-dropdown-item @click="logout">退出登录</el-dropdown-item>
                    </template>
                </el-dropdown>
            </div>
        </el-header>


        <el-container>
            <!-- 左侧菜单 -->
            <el-aside width="220px" class="sidebar">
                <el-menu :key="activeMenu" :default-active="activeMenu" @select="activeMenu = $event"
                    class="el-menu-vertical-demo">
                    <el-menu-item index="users">
                        <i class="el-icon-user"></i>
                        <span>用户管理</span>
                    </el-menu-item>
                    <el-menu-item index="records">
                        <i class="el-icon-date"></i>
                        <span>签到记录</span>
                    </el-menu-item>
                    <el-menu-item index="correction">
                        <i class="el-icon-edit-outline"></i>
                        <span>身份检测</span>
                    </el-menu-item>
                    <el-menu-item index="monitor">
                        <i class="el-icon-video-camera"></i>
                        <span>异常监测</span>
                    </el-menu-item>
                    <el-menu-item index="zoneDetection">
                        <i class="el-icon-s-promotion"></i>
                        <span>目标检测</span>
                    </el-menu-item>
                    <el-menu-item index="behaviorRecognition">
                        <i class="el-icon-video-play"></i>
                        <template #title>告警中心</template>
                    </el-menu-item>
                    <!-- 新增签到菜单选项 -->
                    <el-menu-item index="checkin">
                        <i class="el-icon-check"></i>
                        <span>签到</span>
                    </el-menu-item>
                </el-menu>
            </el-aside>

            <!-- 主内容区 -->
            <el-main class="main-content">
                <!-- 用户管理 -->
                <div v-if="activeMenu === 'users'">
                    <el-card shadow="hover">
                        <div class="toolbar">
                            <el-button type="primary" @click="createUserDialog = true">新增用户</el-button>
                        </div>
                        <el-table :data="users" stripe style="width: 100%">
                            <el-table-column prop="username" label="用户名" />
                            <el-table-column prop="email" label="邮箱" />
                            <el-table-column prop="role" label="角色">
                                <template #default="{ row }">{{ row.role }}</template>
                            </el-table-column>
                            <el-table-column label="操作" width="180">
                                <template #default="{ row }">
                                    <el-button size="mini" @click="openEditUser(row)">编辑</el-button>
                                    <el-button size="mini" type="danger" @click="deleteUser(row.id)">删除</el-button>
                                </template>
                            </el-table-column>
                        </el-table>
                        <div class="pagination-container">
                            <el-pagination background layout="total, prev, pager, next, jumper"
                                :current-page="userPage.page" :page-size="userPage.size" :total="userPage.total"
                                @current-change="handleUserPageChange" />
                        </div>
                    </el-card>

                    <el-dialog :title="editingUser ? '编辑用户' : '新增用户'" v-model="createUserDialog" width="400px">
                        <el-form :model="newUserForm" :rules="userFormRules" ref="userForm">
                            <el-form-item label="用户名" prop="username">
                                <el-input v-model="newUserForm.username" />
                            </el-form-item>
                            <el-form-item label="邮箱" prop="email">
                                <el-input v-model="newUserForm.email" />
                            </el-form-item>
                            <el-form-item label="密码" prop="password" v-if="!editingUser">
                                <el-input type="password" v-model="newUserForm.password" />
                            </el-form-item>
                            <el-form-item label="角色" prop="role">
                                <el-select v-model="newUserForm.role" placeholder="请选择">
                                    <el-option label="管理员" value="ADMIN"></el-option>
                                    <el-option label="普通用户" value="USER"></el-option>
                                </el-select>
                            </el-form-item>
                        </el-form>
                        <template #footer>
                            <el-button @click="createUserDialog = false">取消</el-button>
                            <el-button type="primary" @click="submitUserForm">确 定</el-button>
                        </template>
                    </el-dialog>
                </div>

                <!-- 签到记录 -->
                <div v-if="activeMenu === 'records'">
                    <el-card shadow="hover">
                        <el-table :data="records" stripe style="width: 100%">
                            <el-table-column prop="employeeName" label="用户名" />
                            <el-table-column prop="signTime" label="签到时间" />
                            <el-table-column prop="address" label="地点" />
                            <el-table-column prop="check_type" label="签到类型" />
                        </el-table>
                        <div class="pagination-container">
                            <el-pagination background layout="total, prev, pager, next, jumper"
                                :current-page="recordPage.page" :page-size="recordPage.size" :total="recordPage.total"
                                @current-change="handleRecordPageChange" />
                        </div>
                    </el-card>
                </div>

                 <div v-if="activeMenu === 'correction'" class="monitor-panel">
                        <el-card shadow="hover" style="height: 100%;">
                            <!-- 引入新的身份检测组件 -->
                            <IdentityDetector />
                        </el-card>
                 </div>

                <!-- 实时监测 -->
                <div v-if="activeMenu === 'monitor'" class="monitor-panel">
                    <el-card shadow="hover">
                        <video ref="videoRef" autoplay muted playsinline class="video-preview"></video>
                    </el-card>
                </div>

                <!-- 目标检测页面 -->
                <div v-if="activeMenu === 'zoneDetection'" class="monitor-panel">
                    <el-card shadow="hover" style="height: 100%;">
                        <ZoneMonitor class="zone-full" />
                    </el-card>
                </div>

                <!-- 告警中心管理 -->
                <!-- 告警内容 -->

                <div v-if="activeMenu === 'behaviorRecognition'">
                    <el-card shadow="hover">
                        <!-- 筛选：日期区间 -->
                        <div class="toolbar">
                            <el-date-picker v-model="filter.dateRange" type="daterange" range-separator="至"
                                start-placeholder="开始日期" end-placeholder="结束日期" />
                        </div>

                        <!-- 识别结果表格 -->
                        <el-table :data="recognitions" stripe style="width: 100%">
                            <el-table-column prop="employeeName" label="用户名" />
                            <el-table-column prop="behavior" label="行为" />
                            <el-table-column prop="time" label="识别时间" />
                            <el-table-column label="操作" width="180">
                              <template #default="{ row }">
                                  <el-button size="mini" @click="openBehaviorDetail(row)">详情</el-button>
                                  <el-button size="mini" type="danger" @click="deleteBehavior(row.id)">删除</el-button>
                              </template>
                            </el-table-column>
                        </el-table>

                        <!-- 分页 -->
                        <div class="pagination-container">
                            <el-pagination background layout="total, prev, pager, next, jumper"
                                :current-page="behaviorPage.page" :page-size="behaviorPage.size"
                                :total="behaviorPage.total" @current-change="handleBehaviorPageChange" />
                        </div>
                    </el-card>
                     <!-- 添加行为识别详情对话框 -->
                    <el-dialog title="行为识别详情" v-model="behaviorDetailDialog" width="600px">
                             <div class="behavior-detail">
                                  <div class="detail-item">
                                            <span class="label">用户名：</span>
                                            <span class="value">{{ currentBehavior.employeeName }}</span>
                                  </div>
                                  <div class="detail-item">
                                            <span class="label">行为：</span>
                                            <span class="value">{{ currentBehavior.behavior }}</span>
                                  </div>
                                  <div class="detail-item">
                                            <span class="label">识别时间：</span>
                                            <span class="value">{{ currentBehavior.time }}</span>
                                  </div>
                                  <div class="detail-item">
                                            <span class="label">详情：</span>
                                            <span class="value">{{ currentBehavior.details }}</span>
                                  </div>
                                  <div class="detail-image">
                                             <span class="label">截图：</span>
                                             <img :src="currentBehavior.imageUrl" alt="行为截图" class="behavior-image" />
                                  </div>
                             </div>
                             <template #footer>
                                        <el-button @click="behaviorDetailDialog = false">关闭</el-button>
                             </template>
                    </el-dialog>
                </div>
            </el-main>
        </el-container>
    </el-container>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import http from '@/utils/http'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { useRouter } from 'vue-router'
const router = useRouter()
import ZoneMonitor from '@/components/ZoneMonitor.vue'
import IdentityDetector from '@/components/IdentityDetector.vue'

/** 当前用户信息 **/
const currentUser = reactive({ username: '' })

/** 菜单状态 **/
const activeMenu = ref('users')
// const activeMenu = ref(router.path)


const menuMap = {
    users: '用户管理',
    records: '签到记录',
    correction: '身份检测',
    monitor: '实时监测',
    zoneDetection: '目标检测',
    behaviorRecognition: '告警中心',
    checkin: '签到'
}

/** 分页状态 **/
const userPage = reactive({ page: 1, size: 10, total: 0 })
const recordPage = reactive({ page: 1, size: 10, total: 0 })
const behaviorPage = reactive({ page: 1, size: 10, total: 0 })

/** 数据列表 **/
const users = ref([])
const records = ref([])
const recognitions = ref([])

// /** 补签表单 **/
// const makeupForm = reactive({ userId: '', date: null })

/** 行为识别过滤 **/
const filter = reactive({ dateRange: [] })

/** 新增/编辑用户 **/
const userForm = ref(null)
const createUserDialog = ref(false)
const editingUser = ref(false)
const newUserForm = reactive({
    id: null,
    username: '',
    email: '',
    password: '',
    role: 'USER'
})
const userFormRules = {
    username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
    email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }],
    password: [
        { required: !editingUser.value, message: '请输入密码', trigger: 'blur' }
    ],
    role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}
//告警响应
const behaviorDetailDialog = ref(false)
const currentBehavior = reactive({
    id: null,
    employeeName: '',
    behavior: '',
    time: '',
    details: '',
    imageUrl: ''
})

/** 摄像头 **/
const videoRef = ref(null)
let mediaStream = null

/** 获取当前用户 **/
async function fetchCurrentUser() {
    try {
        const { data } = await http.get('/current_user/')
        currentUser.username = data.username
    } catch {
        ElMessage.error('获取当前用户失败')
    }
}

/** 获取用户列表（分页） **/
async function fetchUsers() {
    try {
        const resp = await http.get('/users', {
            params: { page: userPage.page, size: userPage.size }
        })
        users.value = resp.data.items || resp.data
        userPage.total = resp.data.total || resp.data.totalCount || 0
    } catch {
        ElMessage.error('获取用户列表失败')
    }
}

/** 获取签到记录（分页） **/

async function fetchRecords() {
    try {
        const resp = await http.get('/attendance/records', {
            params: { page: recordPage.page, size: recordPage.size }
        })
        console.log("resp:", resp);

        records.value = resp.data.items || resp.data.records || resp.data
        recordPage.total = resp.data.total || resp.data.totalCount || 0
    } catch {
        ElMessage.error('获取签到记录失败')
    }
}


/** 获取行为识别结果（分页） **/
async function fetchRecognitions() {
    try {
        const params = { page: behaviorPage.page, size: behaviorPage.size }
        if (filter.dateRange.length === 2) {
            params.startDate = dayjs(filter.dateRange[0]).format('YYYY-MM-DD')
            params.endDate = dayjs(filter.dateRange[1]).format('YYYY-MM-DD')
        }
        const resp = await http.get('/behaviorRecognition', { params })
        console.log("行为识别结果：", resp);
        console.log(resp.data);

        recognitions.value = resp.data.items || resp.data.records || resp.data
        behaviorPage.total = resp.data.total || resp.data.totalCount || 0
    } catch {
        ElMessage.error('获取行为识别结果失败')
    }
}

/** 分页切换处理 **/
function handleUserPageChange(page) {
    userPage.page = page
    fetchUsers()
}
function handleRecordPageChange(page) {
    recordPage.page = page
    fetchRecords()
}

function handleBehaviorPageChange(page) {
    behaviorPage.page = page
    fetchRecognitions()
}

// 打开行为识别详情对话框
function openBehaviorDetail(row) {
    currentBehavior.id = row.id
    currentBehavior.employeeName = row.employeeName
    currentBehavior.behavior = row.behavior
    currentBehavior.time = row.time
    currentBehavior.details = row.details
    currentBehavior.imageUrl = row.imageUrl || '/default-behavior-image.jpg' // 如果没有图片URL，使用默认图片
    behaviorDetailDialog.value = true
}

/** 打开编辑用户 **/
function openEditUser(row) {
    editingUser.value = true
    Object.assign(newUserForm, {
        id: row.id,
        username: row.username,
        email: row.email,
        role: row.role,
        password: ''
    })
    createUserDialog.value = true
}

/** 删除用户 **/
async function deleteUser(id) {
    try {
        await http.delete(`/users/${id}`)
        ElMessage.success('删除成功')
        fetchUsers()
    } catch {
        ElMessage.error('删除失败')
    }
}

// 删除行为识别记录
async function deleteBehavior(id) {
    try {
        await http.delete(`/behaviorRecognition/${id}`)
        ElMessage.success('删除成功')
        fetchRecognitions() // 重新获取数据
    } catch {
        ElMessage.error('删除失败')
    }
}

/** 提交新增/编辑 **/
async function submitUserForm() {
    // 使用 Promise 风格校验，更简洁
    try {
        await userForm.value.validate()
    } catch (err) {
        // 校验不通过就直接退出
        return
    }

    try {
        if (editingUser.value) {
            await http.put(`/users/${newUserForm.id}`, newUserForm)
            ElMessage.success('更新成功')
        } else {
            await http.post('/users', newUserForm)
            ElMessage.success('新增成功')
        }
        // 重置对话框和表单
        createUserDialog.value = false
        editingUser.value = false
        Object.assign(newUserForm, {
            id: null,
            username: '',
            email: '',
            password: '',
            role: 'USER'
        })
        fetchUsers()
    } catch {
        ElMessage.error('保存失败')
    }
}


/** 登出 **/
function logout() {
    http.post('/logout')
        .finally(() => {
            // 清掉本地存储的登录态（如果有）
            localStorage.removeItem('token')
            // 用 router 导航到登录页
            router.replace({ path: '/' })
        })
}
/** 初始化摄像头并定时上传截图 **/
async function initCamera() {
    try {
        mediaStream = await navigator.mediaDevices.getUserMedia({ video: true })
        videoRef.value.srcObject = mediaStream
        const canvas = document.createElement('canvas')
        const ctx = canvas.getContext('2d')
        setInterval(() => {
            if (!videoRef.value || videoRef.value.readyState !== 4) return
            canvas.width = videoRef.value.videoWidth
            canvas.height = videoRef.value.videoHeight
            ctx.drawImage(videoRef.value, 0, 0)
            const image = canvas.toDataURL('image/jpeg')
            http
                .post('/attendance/dection/', { image })
                .then(res => {
                    console.log('检测结果', res.data)
                })
                .catch(() => { })
        }, 5000)
    } catch {
        ElMessage.error('无法访问摄像头')
    }
}

/** 监控菜单切换 **/
watch(activeMenu, val => {
    if (val === 'users') fetchUsers()
    if (val === 'records') fetchRecords()
    if (val === 'monitor') initCamera()
    if (val === 'behaviorRecognition') fetchRecognitions()
    //新增签到菜单切换逻辑
    if (val === 'checkin') {
        // 这里可以添加点击签到菜单后的逻辑，例如跳转到签到页面
        router.push('/index') // 假设签到页面路由为 /index
    }
})

onMounted(async () => {
    await fetchCurrentUser()
    await fetchUsers()
    await fetchRecords()
})
</script>

<style scoped>
.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(90deg, #409eff 0%, #66b1ff 100%);
    color: #fff;
    padding: 0 20px;
}

.header-left .el-breadcrumb {
    background: transparent;
    color: #fff;
}

.header-right {
    display: flex;
    align-items: center;
}

.sidebar {
    background-color: #2d3a4b;
}

.el-menu-vertical-demo {
    border-right: none;
    background-color: #2d3a4b;
    color: #bfcbd9;
}

.el-menu-vertical-demo .el-menu-item {
    color: #bfcbd9;
}

.el-menu-vertical-demo .el-menu-item.is-active {
    background-color: #409eff !important;
    color: #fff !important;
}

/**.main-content {
   padding: 20px;
    background: #f5f7fa;
} */
.main-content {
    padding: 20px;
    background: #f5f7fa;
    display: flex;
    flex-direction: column;
    height: 100%;
}

.monitor-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    height: 100%;
}

.toolbar {
    margin-bottom: 10px;
}

.pagination-container {
    text-align: right;
    margin-top: 15px;
}

.video-preview {
    width: 100%;
    border-radius: 8px;
    background: #000;
}

.correction-card {
    max-width: 400px;
}
/* 添加样式 */
.behavior-detail {
    padding: 20px;
}

.detail-item {
    margin-bottom: 15px;
    display: flex;
    align-items: center;
}

.detail-item .label {
    font-weight: bold;
    width: 100px;
    flex-shrink: 0;
}

.detail-image {
    margin-top: 20px;
}

.detail-image .label {
    display: block;
    font-weight: bold;
    margin-bottom: 10px;
}

.behavior-image {
    width: 100%;
    max-height: 400px;
    object-fit: contain;
    border: 1px solid #ddd;
    border-radius: 4px;
}
</style>
