<template>
    <div class="register-wrapper">
        <el-card class="register-card">
            <!-- 标题区 -->
            <div class="register-header">
                <h2 class="register-title">注册新用户</h2>
                <p class="sub-title">欢迎加入餐厅安全监测系统</p>
            </div>

            <!-- 注册表单 -->
            <el-form ref="registerForm" :model="userParams" :rules="rules" label-position="top" size="medium">
                <el-form-item label="用户名" prop="username">
                    <el-input v-model="userParams.username" placeholder="请输入用户名" />
                </el-form-item>

                <el-form-item label="邮箱" prop="email">
                    <el-input v-model="userParams.email" placeholder="请输入邮箱，用于找回密码" />
                </el-form-item>

                <el-form-item label="密码" prop="password">
                    <el-input v-model="userParams.password" type="password" placeholder="请输入密码" show-password />
                </el-form-item>

                <el-form-item label="确认密码" prop="confirmPassword">
                    <el-input v-model="userParams.confirmPassword" type="password" placeholder="请再次输入密码" show-password />
                </el-form-item>

                <el-form-item label="验证码" prop="verify_code">
                    <div class="verify-code">
                        <el-input v-model="userParams.verify_code" placeholder="请输入验证码" style="flex: 1" />
                        <img :src="verifyCodeImg" @click="getVerifyCode" alt="验证码" title="点击刷新" />
                    </div>
                </el-form-item>

                <el-form-item>
                    <el-button type="primary" :loading="loading" style="width: 100%" @click="register">
                        注册
                    </el-button>
                </el-form-item>

                <el-form-item>
                    <el-button type="text" @click="goToLogin">
                        已有账号？返回登录
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
const registerForm = ref(null)
const loading = ref(false)
const verifyCodeImg = ref('')

// 表单数据模型
const userParams = ref({
    username: '',
    email: '',
    password: '',
    confirmPassword: '', // 用于前端校验
    verify_code: ''
})

// 自定义校验函数：确认密码
const validatePass = (rule, value, callback) => {
    if (value === '') {
        callback(new Error('请再次输入密码'))
    } else if (value !== userParams.value.password) {
        callback(new Error('两次输入的密码不一致!'))
    } else {
        callback()
    }
}

// 校验规则
const rules = {
    username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
    email: [
        { required: true, message: '请输入邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入有效的邮箱地址', trigger: ['blur', 'change'] }
    ],
    password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
    confirmPassword: [{ required: true, validator: validatePass, trigger: 'blur' }],
    verify_code: [{ required: true, message: '请输入验证码', trigger: 'blur' }]
}

// 路由实例
const router = useRouter()

/**
 * 获取验证码图片 (与登录页逻辑相同)
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
 * 注册
 */
const register = () => {
    registerForm.value.validate(async (valid) => {
        if (!valid) return
        loading.value = true
        try {
            // 向后端发送注册请求 (不发送 confirmPassword)
            await http.post(
                '/register/',
                {
                    username: userParams.value.username,
                    password: userParams.value.password,
                    email: userParams.value.email,
                    verify_code: userParams.value.verify_code
                },
                { withCredentials: true }
            )

            ElNotification({
                title: '注册成功！',
                message: '接下来，请录入您的人脸信息用于登录验证。',
                type: 'success',
                duration: 3000
            })

            // 注册成功后，跳转到人脸录入页面
            // 可以在 query 中传递刚注册的用户名，方便人脸录入组件使用
            router.push({
                path: '/face-enroll',
                query: { username: userParams.value.username }
            })

        } catch (err) {
            ElNotification({
                title: '注册失败',
                type: 'error',
                message: err.response?.data?.message || err.message
            })
            // 失败后刷新验证码
            getVerifyCode()
        } finally {
            loading.value = false
        }
    })
}

/**
 * 跳转到登录页面
 */
const goToLogin = () => {
    router.push('/login')
}

// 组件挂载后立即加载验证码
onMounted(() => {
    getVerifyCode()
})
</script>

<style scoped>
/* 样式与登录页保持一致，仅修改类名前缀以示区分 */
.register-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    background: #f0f2f5;
}

.register-card {
    width: 400px;
    padding: 24px;
    border-radius: 8px;
}

.register-header {
    text-align: center;
    margin-bottom: 20px;
}

.register-title {
    font-size: 20px;
    font-weight: bold;
}

.sub-title {
    color: #888;
    margin-top: 8px;
}

.verify-code {
    display: flex;
    align-items: center;
}

.verify-code img {
    cursor: pointer;
    margin-left: 10px;
    height: 38px; /* 与 Element Plus medium size input 高度一致 */
}
</style>