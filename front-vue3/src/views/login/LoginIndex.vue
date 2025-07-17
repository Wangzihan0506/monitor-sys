<template>
    <div class="login-wrapper">
        <el-card class="login-card">
            <!-- 标题区 -->
            <div class="login-header">
                <h2 class="login-title">
                    {{ resetPasswordShow ? '忘记密码' : '餐厅安全监测系统' }}
                </h2>
                <p v-if="tipMsg" class="tip-msg" v-html="tipMsg" />
            </div>

            <!-- 登录表单 -->
            <el-form v-if="!resetPasswordShow" ref="loginForms" :model="userParams" :rules="rules" label-position="top"
                size="medium">
                <el-form-item label="用户名" prop="username">
                    <el-input v-model="userParams.username" placeholder="请输入用户名" />
                </el-form-item>

                <el-form-item label="密码" prop="password">
                    <el-input v-model="userParams.password" type="password" placeholder="请输入密码" />
                </el-form-item>

                <!-- 滑块验证码 -->
                <el-form-item prop="sliderVerified" class="slider-verify-item">
                    <el-slider
                        v-model="sliderValue"
                        :min="0"
                        :max="100"
                        :step="1"
                        :show-tooltip="false"
                        :disabled="userParams.sliderVerified"
                        @input="onSliderChange"
                        class="slider-component"
                    ></el-slider>
                    <div v-if="!userParams.sliderVerified" class="slider-text">请拖动滑块验证</div>
                    <div v-else class="slider-text verified">验证成功！</div>
                </el-form-item>

                <el-form-item>
                    <el-button
                        type="primary"
                        style="width: 100%"
                        :loading="loading"
                        :disabled="loading"
                        @click="login"
                    >
                        登录
                    </el-button>
                </el-form-item>

                <el-form-item>
                    <el-button type="text" @click="showResetPassword">
                        忘记密码？
                    </el-button>
                </el-form-item>
            </el-form>

            <!-- 重置密码表单 -->
            <el-form v-else ref="resetForms" :model="userParams" label-position="top" size="medium">
                <el-form-item label="注册邮箱">
                    <el-input v-model="userParams.email" placeholder="请输入注册时的邮箱" />
                </el-form-item>

                <el-form-item>
                    <el-button type="primary" :loading="resetPasswordBtn" style="width: 100%" @click="resetPassword">
                        发送重置邮件
                    </el-button>
                </el-form-item>

                <el-form-item>
                    <el-button type="text" @click="hideResetPassword">
                        返回登录
                    </el-button>
                </el-form-item>
            </el-form>
        </el-card>
    </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue' // 引入 reactive
import { useRouter } from 'vue-router'
import { ElNotification, ElMessage } from 'element-plus' // 确保导入 ElMessage
import http from '@/utils/http'

// 表单引用与状态
const loginForms = ref(null) // 绑定到登录表单的 ref
const resetForms = ref(null) // 绑定到重置密码表单的 ref
const loading = ref(false) // 登录按钮的加载状态
const resetPasswordShow = ref(false) // 是否显示重置密码表单
const tipMsg = ref('') // 提示消息
const resetPasswordBtn = ref(false) // 重置密码按钮的加载状态
const router = useRouter()

// 表单数据模型
const userParams = reactive({ // 【核心修改】userParams 使用 reactive
    username: '',
    password: '',
    sliderVerified: false, // 滑块验证状态
    email: ''
})

// 滑块相关变量
const sliderValue = ref(0); // 滑块的当前值

// 校验规则
const rules = reactive({
    username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
    password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
    sliderVerified: [{
    validator: (rule, value, callback) => {
        // 不再关心 value (userParams.sliderVerified)
        // 直接检查滑块的实时值 sliderValue
        if (sliderValue.value !== 100) {
            callback(new Error('请完成滑块验证'));
        } else {
            callback();
        }
    },
    trigger: 'change'
}]
});

/**
 * 【核心修改】登录函数 - 统一命名为 login
 */
// 请用这个函数完整替换你现有的 login 函数

const login = async () => {
    // 增加一个防御性检查，如果正在加载，直接返回，防止重复点击
    if (loading.value) return;

    // 首先，确保表单引用存在
    if (!loginForms.value) {
        console.error("致命错误：无法找到 loginForms 的引用！");
        return;
    }

    try {
        loading.value = true; // 【第一步】立即开始加载，禁用按钮

        // 【第二步】执行表单验证
        await loginForms.value.validate();

        console.log('%c表单验证成功，准备发送网络请求...', 'color: green;');

        // 【第三步】发送网络请求
        const response = await http.post('/auth/login', {
            username: userParams.username,
            password: userParams.password,
            // 确保使用正确的状态
            sliderVerified: userParams.sliderVerified,
        });

        // 【第四步】处理后端返回的结果
        if (response && response.code === 0) {
            ElMessage.success('密码登录成功！请进行人脸验证。');
            if (response.token) {
                localStorage.setItem('token', response.token);
            }
            if (response.username) {
                router.replace({ name: 'faceLogin', params: { username: response.username } });
            } else {
                ElMessage.error('登录成功但缺少用户信息！');
            }
        } else {
            // 后端返回业务逻辑错误（如密码错误）
            ElMessage.error(response.msg || '登录失败，请检查您的凭据');
            // 登录失败后重置滑块
            sliderValue.value = 0;
            userParams.sliderVerified = false;
        }

    } catch (error) {
    console.error("捕获到错误:", error);

    if (error && error.fields) {
        // 1. 表单验证失败
        ElMessage.error('请检查您的输入并完成所有必填项！');

    } else if (error && error.isBusinessError) {
        // 2. 【新增】处理我们自定义的业务逻辑错误
        // 因为拦截器已经弹过消息了，这里通常可以什么都不做，或者只在控制台记录
        console.warn('捕获到业务逻辑失败:', error.message);
        // 如果需要，可以在这里重置滑块
        sliderValue.value = 0;
        userParams.sliderVerified = false;

    } else if (error && error.response) {
        // 3. 处理真实的 HTTP 网络错误
        const { status, data } = error.response;
        // 因为拦截器也弹过消息了，这里也可以简化
        console.error(`HTTP 错误 ${status}:`, data);
        // 网络失败后重置滑块
        sliderValue.value = 0;
        userParams.sliderVerified = false;

    } else {
        // 4. 处理其他所有未知错误
        ElMessage.error('发生未知错误，请检查网络或联系管理员');
    }

   }
};

/**
 * 显示重置密码表单
 */
const showResetPassword = () => {
    tipMsg.value = ''
    resetPasswordShow.value = true
}

/**
 * 隐藏重置密码表单
 */
const hideResetPassword = () => {
    tipMsg.value = ''
    resetPasswordShow.value = false
    // 清空邮箱字段
    userParams.email = '' // 【核心修改】直接访问 userParams 的属性
}

/**
 * 重置密码
 */
const resetPassword = async () => {
    if (!userParams.email) { // 【核心修改】使用 userParams
        ElNotification({ title: '请输入邮箱', type: 'warning' })
        return
    }
    resetPasswordBtn.value = true
    try {
        await http.post(
            '/reset_password/', // 【注意】这里的 /reset_password/ 接口路径
            { email: userParams.email }, // 【核心修改】使用 userParams
            { withCredentials: true }
        )
        ElNotification({
            title: '已发送重置邮件，请查收',
            type: 'success'
        })
        hideResetPassword()
    } catch (err) {
        console.error("重置密码失败:", err); // 打印详细错误
        ElNotification({
            title: '重置失败',
            type: 'error',
            message: err.response?.data?.msg || err.message // 检查 err.response?.data?.msg
        })
    } finally {
        resetPasswordBtn.value = false
    }
}

//滑块值改变时的回调
const onSliderChange = (value) => {
    // 简单模拟：如果滑块拖动到最大值，则认为验证成功
    if (value === 100) {
        userParams.sliderVerified = true; //更新表单的验证状态
        ElMessage.success('滑块验证成功！');
    } else {
        userParams.sliderVerified = false; // 重置表单验证状态
    }
};

// 组件挂载后，如果需要初始化一些数据，可以在这里调用
onMounted(() => {
    // 默认不需要获取验证码图片了
})
</script>

<style scoped>
/* 登录页面的整体布局 */
.login-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh; /* 保证至少占满视口高度 */
    background: linear-gradient(135deg, #7F7FD5, #86A8E7, #91EAE4); /* 渐变背景 */
}

/* 登录卡片样式 */
.login-card {
    width: 380px;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1); /* 柔和阴影 */
}

/* 标题样式 */
.login-title {
    text-align: center;
    color: #333;
    margin-bottom: 30px;
    font-size: 24px;
    font-weight: bold;
}

/* 按钮样式 */
.login-button {
    width: 100%;
    height: 45px;
    font-size: 16px;
    border-radius: 6px;
}

/* 滑块验证样式 */
.slider-verify-item {
    margin-bottom: 25px; /* 与登录按钮保持距离 */
}

.slider-component {
    width: 100%;
}

.slider-text {
    text-align: center;
    margin-top: 10px;
    font-size: 14px;
    color: #909399; /* 灰色提示 */
}
.slider-text.verified {
    color: #67C23A; /* 成功时绿色 */
    font-weight: bold;
}

/* 覆盖 Element UI 默认样式，使其更贴合设计 */
:deep(.el-input__inner) {
    height: 40px;
    line-height: 40px;
}
</style>