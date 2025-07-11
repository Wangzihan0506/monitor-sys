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

                <el-form-item label="验证码" prop="verify_code">
                    <div class="verify-code">
                        <el-input v-model="userParams.verify_code" placeholder="请输入验证码" style="flex: 1" />
                        <img :src="verifyCodeImg" @click="getVerifyCode" alt="验证码" title="点击刷新" />
                    </div>
                </el-form-item>

                <el-form-item>
                    <el-button type="primary" :loading="loading" style="width: 100%" @click="login">
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElNotification } from 'element-plus'
import http from '@/utils/http'

// 表单引用与状态
const loginForms = ref(null)
const resetForms = ref(null)
const loading = ref(false)
const verifyCodeImg = ref('')
const resetPasswordShow = ref(false)
const tipMsg = ref('')
const resetPasswordBtn = ref(false)

// 表单数据模型
const userParams = ref({
    username: '',
    password: '',
    verify_code: '',
    email: ''
})

// 校验规则
const rules = {
    username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
    password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
    verify_code: [{ required: true, message: '请输入验证码', trigger: 'blur' }]
}

// 路由实例
const router = useRouter()

/**
 * 获取验证码图片
 */
const getVerifyCode = async () => {
    try {
        const res = await http.get('/get_verify_code/', {
            responseType: 'blob',
            withCredentials: true
        })
        verifyCodeImg.value = URL.createObjectURL(res.data)
    } catch (err) {
        console.error('获取验证码失败：', err)
    }
}

/**
 * 登录
 */
const login = () => {
    loginForms.value.validate(async (valid) => {
        if (!valid) return
        loading.value = true
        try {
            // 向后端发送登录请求
            await http.post(
                '/login/',
                {
                    username: userParams.value.username,
                    password: userParams.value.password,
                    verify_code: userParams.value.verify_code
                },
                { withCredentials: true }
            );

            // --- 核心修改点在这里 ---
            // 密码验证成功后，给出提示，并跳转到人脸验证页面
            ElNotification({
                title: '密码验证成功',
                message: '为了您的账户安全，请完成人脸识别二次验证。',
                type: 'info',
                duration: 3000
            });

            // 跳转到人脸登录页面，并携带用户名
            // 用户名是识别人脸的关键
            router.push({
                path: '/face-login',
                query: { username: userParams.value.username }
            });

            // 下面的旧跳转逻辑不再需要
            /*
            const redirectPath = route.query.redirect
                ? route.query.redirect
                : (data.role === 'user' ? '/index' : '/admin');

            if (route.query.queryParams) {
                router.push({
                    path: redirectPath,
                    query: JSON.parse(decodeURIComponent(route.query.queryParams))
                });
            } else {
                router.push(redirectPath);
            }
            */
        } catch (err) {
            ElNotification({
                title: '登录失败',
                type: 'error',
                message: err.response?.data?.message || err.message
            });
            getVerifyCode();
        } finally {
            loading.value = false;
        }
    });
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
    userParams.value.email = ''
}

/**
 * 重置密码
 */
const resetPassword = async () => {
    if (!userParams.value.email) {
        ElNotification({ title: '请输入邮箱', type: 'warning' })
        return
    }
    resetPasswordBtn.value = true
    try {
        await http.post(
            '/reset_password/',
            { email: userParams.value.email },
            { withCredentials: true }
        )
        ElNotification({
            title: '已发送重置邮件，请查收',
            type: 'success'
        })
        hideResetPassword()
    } catch (err) {
        ElNotification({
            title: '重置失败',
            type: 'error',
            message: err.response?.data?.message || err.message
        })
    } finally {
        resetPasswordBtn.value = false
    }
}

// 组件挂载后立即加载验证码
onMounted(() => {
    getVerifyCode()
})
</script>

<style scoped>
.login-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    background: #f0f2f5;
}

.login-card {
    width: 400px;
    padding: 24px;
    border-radius: 8px;
}

.login-header {
    text-align: center;
    margin-bottom: 20px;
}

.login-title {
    font-size: 20px;
    font-weight: bold;
}

.tip-msg {
    color: #f56c6c;
    margin-top: 8px;
}

.verify-code {
    display: flex;
    align-items: center;
}

.verify-code img {
    cursor: pointer;
    margin-left: 10px;
    height: 38px;
}
</style>