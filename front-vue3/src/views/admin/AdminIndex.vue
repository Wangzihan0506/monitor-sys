<template>
    <el-container style="height: 100vh;">

        <el-header class="header">
            <div class="header-left">
                <el-breadcrumb separator="/">
                    <el-breadcrumb-item>餐厅安全监测系统</el-breadcrumb-item>
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
                            <el-pagination
                                background
                                layout="total, prev, pager, next, jumper"
                                :current-page="recordPage.page"
                                :page-size="recordPage.size"
                                :total="recordPage.total"
                                @current-change="handleRecordPageChange" />
                        </div>
                    </el-card>
                </div>

                <!-- 身份检测 -->
                 <div v-if="activeMenu === 'correction'" class="monitor-panel">
                        <el-card shadow="hover" style="height: 100%;">
                           <IdentityDetector />
                        </el-card>
                 </div>

                <!-- 异常监测 -->
                <!-- 异常监测 -->
                <div v-if="activeMenu === 'monitor'" class="monitor-panel">

                    <AbnormalDetection v-if="activeMenu === 'monitor'" />
                </div>

                <!-- 目标检测页面 -->
                <div v-if="activeMenu === 'zoneDetection'" class="monitor-panel">
                    <el-card shadow="hover" style="height: 100%;">
                        <!-- 只有当 sharedVideoRefElement 确实存在且视频加载完成才渲染 -->
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
                             <el-button
                                   type="success"
                                   style="margin-left: 12px"
                                  :disabled="filter.dateRange.length !== 2"
                                  @click="generateDailyReport">
                                  日志生成
                             </el-button>
                        </div>

                        <!-- 识别结果表格 -->
                        <el-table :data="alerts" stripe style="width: 100%">
                            <el-table-column prop="display_type" label="告警类型" width="120" />
                            <el-table-column prop="message" label="告警内容" />
                            <el-table-column prop="timestamp" label="告警时间" width="180" />
                            <el-table-column prop="is_handled" label="状态" width="100">
                              <template #default="{ row }">
                                <el-tag :type="row.is_handled ? 'success' : 'warning'">
                                    {{ row.is_handled ? '已处理' : '未处理' }}
                                </el-tag>
                              </template>
                            </el-table-column>
                            <el-table-column label="操作" width="200">
                              <template #default="{ row }">
                                  <el-button size="mini" @click="openAlertDetail(row)">详情</el-button>
                                  <el-button size="mini" type="success" v-if="!row.is_handled" @click="handleAlert(row)">处理</el-button>
                                  <el-button size="mini" type="danger" @click="deleteAlert(row)">删除</el-button>
                              </template>
                           </el-table-column>
                        </el-table>

                        <!-- 分页 -->
                        <div class="pagination-container">
                            <el-pagination background layout="total, prev, pager, next, jumper"
                                :current-page="alertPage.page" :page-size="alertPage.size"
                                :total="alertPage.total" @current-change="handleAlertPageChange" />
                        </div>
                    </el-card>
                      <!-- 【核心修改】告警详情对话框 -->
                    <el-dialog title="告警详情" v-model="behaviorDetailDialog" width="600px">
                        <div class="alert-detail">
                            <div class="detail-item">
                                <span class="label">告警类型：</span>
                                <span class="value">{{ currentAlert.display_type }}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">告警内容：</span>
                                <span class="value">{{ currentAlert.message }}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">告警时间：</span>
                                <span class="value">{{ currentAlert.timestamp }}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">目标框：</span>
                                <span class="value">{{ currentAlert.person_box }}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">状态：</span>
                                <span class="value">
                                    <el-tag :type="currentAlert.is_handled ? 'success' : 'warning'">
                                        {{ currentAlert.is_handled ? '已处理' : '未处理' }}
                                    </el-tag>
                                </span>
                            </div>
                            <div class="detail-item" v-if="currentAlert.is_handled">
                                <span class="label">处理意见：</span>
                                <span class="value">{{ currentAlert.handle_result }}</span>
                            </div>
                            <div class="detail-item" v-if="currentAlert.is_handled">
                                <span class="label">处理时间：</span>
                                <span class="value">{{ currentAlert.handled_time }}</span>
                            </div>
                            <div class="detail-image" v-if="currentAlert.frame_path">
                                <span class="label">截图：</span>
                                <!-- 假设后端静态文件服务在 /static 路径下，且 img_path 是相对路径 -->
                                 <img :src="getAlertImageUrl(currentAlert)" alt="告警截图" class="behavior-image" />
                            </div>
                             <!-- 处理告警的输入框和按钮 -->
                            <div v-if="!currentAlert.is_handled" style="margin-top: 20px;">
                                <el-input v-model="handleResultInput" placeholder="请输入处理意见" type="textarea" :rows="2"></el-input>
                                <el-button type="primary" @click="submitHandleAlert" style="margin-top: 10px;">提交处理</el-button>
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
import { ref, reactive, onMounted, watch,onUnmounted } from 'vue'; // 引入 computed
import { useRouter } from 'vue-router';
import http from '@/utils/http';
import { ElMessage, ElMessageBox } from 'element-plus';
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import dayjs from 'dayjs'


//子组件
import ZoneMonitor from '@/components/ZoneMonitor.vue'
import IdentityDetector from '@/components/IdentityDetector.vue'
import AbnormalDetection from "@/components/AbnormalDetection.vue";


//基础状态
const router = useRouter();
const backendApiBaseUrl = 'http://127.0.0.1:5000';
const currentUser = reactive({ username: '' });
const activeMenu = ref('users'); // 默认选中的菜单

const menuMap = {
    users: '用户管理',
    records: '签到记录',
    correction: '身份检测',
    monitor: '异常检测',
    zoneDetection: '目标检测',
    behaviorRecognition: '告警中心',
    checkin: '签到'
}

/** 分页状态 **/
const userPage = reactive({ page: 1, size: 10, total: 0 })
const recordPage = reactive({ page: 1, size: 10, total: 0 })
// const behaviorPage = reactive({ page: 1, size: 10, total: 0 })
const alertPage = ref({
  page: 1,
  size: 10,
  total: 0
});

/** 数据列表 **/
const users = ref([])
const records = ref([])
const alerts = ref([])



/** 新增/编辑用户 **/
const userForm = ref(null)
const createUserDialog = ref(false)
const editingUser = ref(false)
const newUserForm = reactive({
    id: null,
    username: '',
    email: '',
    password: '',
})
const userFormRules = {
    username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
    email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }],
    password: [
        { required: !editingUser.value, message: '请输入密码', trigger: 'blur' }
    ]
}

//告警响应
const filter = reactive({ dateRange: [] })
const behaviorDetailDialog = ref(false)
const currentAlert = reactive({
    id: null,
    type: '', // 'normal' 或 'abnormal'
    display_type: '', // 用于前端显示：'区域告警' 或 '异常行为'
    message: '',
    person_box: '', // 存储 JSON 字符串
    frame_path: '',
    timestamp: '',
    is_handled: false,
    handle_result: '',
    handled_time: ''
})
const handleResultInput = ref('');
async function fetchCurrentUser() {
    try {
        const response = await http.get('/current_user/');
        // 假设成功返回 { code: 0, data: { username: '...' } }
        if (response.data && response.data.username) {
            currentUser.username = response.data.username;
        }
    } catch (error) {
        console.error('获取当前用户信息失败:', error);
    }
}

async function fetchUsers() {
    try {
        const response = await http.get('/users', {
            params: { page: userPage.page, size: userPage.size }
        });
        console.log("【用户数据】后端返回:", response);
        // 统一从 response.data.items 获取
        users.value = response.data?.items || [];
        userPage.total = response.data?.total || 0;
    } catch (error) {
        console.error('获取用户列表失败:', error);
    }
}

async function fetchRecords() {
    try {
        const response = await http.get('/attendance/records', {
            params: { page: recordPage.page, size: recordPage.size }
        });
        console.log("【签到记录】后端返回的原始完整响应:", JSON.parse(JSON.stringify(response)));
        const fetchedItems = response.data?.items ? [...response.data.items] : []; // 使用扩展运算符进行浅拷贝
        const fetchedTotal = response.data?.total || 0;

        records.value = fetchedItems;
        recordPage.total = fetchedTotal;

        console.log("【签到记录】解析后 records.value:", records.value);
        console.log("【签到记录】解析后 recordPage.total:", recordPage.total);

    } catch (error) {
        console.error('获取签到记录失败，捕获到错误:', error);
        // 如果需要，可以更详细地打印错误类型
        if (error.code) {
            console.error('错误代码:', error.code);
        }
        if (error.message) {
            console.error('错误消息:', error.message);
        }
        if (error.response) {
            console.error('错误响应:', error.response);
        }
    }
}

async function fetchAlerts() {
    try {
        const params = {
            page: alertPage.value.page,
            size: alertPage.value.size,
            // ... (你的日期过滤逻辑)
        };
        const response = await http.get('/alerts', { params });
        console.log("【告警中心】后端返回:", response);

        alerts.value = (response.data?.items || []).map(a => ({
            ...a,
            display_type: a.type === 'normal' ? '区域告警' : '异常行为',
            timestamp: dayjs(a.timestamp).format('YYYY-MM-DD HH:mm:ss'),
            handled_time: a.handled_time ? dayjs(a.handled_time).format('YYYY-MM-DD HH:mm:ss') : '—'
        }));
        alertPage.value.total = response.data?.total || 0;
    } catch (error) {
        console.error('获取告警数据失败:', error);
    }
}

/** 分页切换处理 **/
function handleUserPageChange(newPage) {
    userPage.page = newPage;
    fetchUsers();
}

function handleRecordPageChange(newPage) {
    recordPage.page = newPage;
    fetchRecords();
}

// 【修复】分页变量名统一
function handleAlertPageChange(newPage) {
    alertPage.value.page = newPage;
    fetchAlerts();
}

//打开告警详情对话框
function openAlertDetail(alert) {
    Object.assign(currentAlert, alert);
    handleResultInput.value = alert.handle_result || '';
    alertDetailDialog.value = true;
}

/** 打开编辑用户 **/
function openEditUser(row) {
    editingUser.value = true
    Object.assign(newUserForm, {
        id: row.id,
        username: row.username,
        email: row.email,
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

// 【核心修改】删除告警记录
async function deleteAlert(row) {
    try {
        await ElMessageBox.confirm('此操作将永久删除该告警记录, 是否继续?', '提示', {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
        });
        const url = `/alerts/${row.type}/${row.id}`; // 后端 /api/alerts/<alert_type>/<alert_id>
        await http.delete(url);
        ElMessage.success('删除成功');
        fetchRecognitions(); // 重新获取数据
    } catch (error) {
        console.error("删除告警失败:", error);
        if (error !== 'cancel') { // 避免取消操作的报错
            ElMessage.error('删除失败');
        }
    }
}

// 【新增】处理告警
async function handleAlert(row) {
    ElMessageBox.prompt('请输入处理意见', '处理告警', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: row.handle_result || '', // 默认值
        inputValidator: (value) => {
            if (!value) return '处理意见不能为空';
            if (value.length > 250) return '处理意见过长';
            return true;
        },
        inputErrorMessage: '输入不合法'
    }).then(async ({ value }) => {
        try {
            const url = `/api/alerts/${row.type}/${row.id}/handle`;
            await http.post(url, { handle_result: value });
            ElMessage.success('告警处理成功');
            fetchRecognitions(); // 刷新列表
        } catch (error) {
            console.error("处理告警失败:", error);
            ElMessage.error('处理告警失败');
        }
    }).catch(() => {
        ElMessage.info('取消处理');
    });
}

// 【新增】在详情对话框中提交处理意见
async function submitHandleAlert() {
    if (!handleResultInput.value.trim()) {
        ElMessage.warning('处理意见不能为空');
        return;
    }
    if (handleResultInput.value.length > 250) {
        ElMessage.warning('处理意见过长');
        return;
    }
    try {
        const url = `/api/alerts/${currentAlert.type}/${currentAlert.id}/handle`;
        await http.post(url, { handle_result: handleResultInput.value });
        ElMessage.success('告警处理成功');
        behaviorDetailDialog.value = false; // 关闭对话框
        fetchRecognitions(); // 刷新列表
    } catch (error) {
        console.error("提交处理失败:", error);
        ElMessage.error('提交处理失败');
    }
}

// 【新增】清空所有告警
// eslint-disable-next-line @typescript-eslint/no-unused-vars
async function clearAllAlerts() {
    try {
        await ElMessageBox.confirm('此操作将永久清空所有告警记录, 是否继续?', '提示', {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
        });
        await http.post('/api/alerts/clear');
        ElMessage.success('所有告警已清空');
        await fetchAlerts(); // 刷新列表
    } catch (error) {
        console.error("清空告警失败:", error);
        if (error !== 'cancel') {
            ElMessage.error('清空失败');
        }
    }
}

function getAlertImageUrl(alert) {
    if (!alert || !alert.frame_path) return '';
    return `${backendApiBaseUrl}/static/${alert.frame_path}`; // 加上 /static
}

/**
 * 生成并下载日报 PDF
 * 调用 Dify 工作流：把起止日期作为入参，工作流返回 pdf url
 */
async function generateDailyReport() {
  if (filter.dateRange.length !== 2) return

  const [start, end] = filter.dateRange.map(d => dayjs(d).format('YYYY-MM-DD'))

  try {
    // 1. 调 Dify 工作流（以流式应用为例，把 workflow 的 endpoint 换成你自己的）
    const difyRes = await axios.post(
      'https://api.dify.ai/v1/workflows/YOUR_WORKFLOW_ID/executions',
      {
        // 工作流入参，名称必须和你配置的一致
        inputs: { start_date: start, end_date: end },
        response_mode: 'blocking',   // 等待执行完返回
        user: currentUser.username
      },
      {
        headers: { Authorization: `Bearer ${import.meta.env.VITE_DIFY_API_KEY}` }
      }
    )

    // 2. 取 pdf url（假设工作流在 outputs 里返回了一个 pdf_url 字段）
    const { pdf_url: pdfUrl } = difyRes.data.data.outputs

    // 3. 浏览器自动下载
    const link = document.createElement('a')
    link.href = pdfUrl
    link.download = `日报_${start}_${end}.pdf`
    link.style.display = 'none'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    ElMessage.success('已生成并下载日报')
  } catch (e) {
    console.error(e)
    ElMessage.error('生成失败，请稍后重试')
  }
}

/** 监控菜单切换 **/
watch(activeMenu, (newMenu) => {
    console.log(`菜单切换到: ${newMenu}`);
    switch (newMenu) {
        case 'users':
            fetchUsers();
            break;
        case 'records':
            console.log("开始获取记录");
            fetchRecords();
            break;
        case 'behaviorRecognition': // 你的告警中心 index
            fetchAlerts();
            break;
        case 'checkin':
            router.push('/checkin');
            break;
        // 其他菜单项...
    }
}, { immediate: true });

onMounted(() => {
    console.log("AdminIndex.vue 已挂载 (onMounted)");
    fetchCurrentUser();
});

onUnmounted(() => {
});

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
