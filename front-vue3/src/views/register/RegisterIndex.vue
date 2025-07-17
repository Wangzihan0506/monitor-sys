<template>
    <div class="register-wrapper">
        <el-card class="register-card">
            <!-- 标题区 -->
            <div class="register-header">
                <h2 class="register-title">注册新用户</h2>
                <p class="sub-title">欢迎加入餐厅安全监测系统</p>
            </div>

            <!-- 注册表单 -->
            <el-form ref="registerFormRef" :model="userParams" :rules="rules" label-position="top" size="medium">
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

                <el-form-item prop="sliderVerified" class="slider-verify-item">
                    <el-slider
                        v-model="sliderValue"
                        :min="0"
                        :max="100"
                        :step="1"
                        :show-tooltip="false"
                        :disabled="isSliderVerified"
                        @change="onSliderChange"
                        class="slider-component"
                    ></el-slider>
                    <div v-if="!isSliderVerified" class="slider-text">请拖动滑块验证</div>
                    <div v-else class="slider-text verified">验证成功！</div>
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
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage,ElNotification } from 'element-plus';
import http from '@/utils/http';

// --- 状态和引用 ---
const registerFormRef = ref(null);
const loading = ref(false);
const router = useRouter();//路由实例

// --- 表单数据模型 ---
const userParams = reactive({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    sliderVerified: false,
});

// --- 滑块相关状态 ---
const sliderValue = ref(0);
const isSliderVerified = ref(false);

// --- 校验密码 ---
const validatePass = (rule, value, callback) => {
    if (value === '') {
        callback(new Error('请再次输入密码'));
    } else if (value !== userParams.password) {
        callback(new Error('两次输入的密码不一致!'));
    } else {
        callback();
    }
};

//规则
const rules = reactive({
    username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
    email: [
        { required: true, message: '请输入邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入有效的邮箱地址', trigger: ['blur', 'change'] }
    ],
    password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
    confirmPassword: [{ required: true, validator: validatePass, trigger: 'blur' }],
    sliderVerified: [{
        validator: (rule, value, callback) => {
            if (!value) {
                callback(new Error('请完成滑块验证'));
            } else {
                callback();
            }
        },
        trigger: 'change'
    }]
});

// --- 滑块逻辑 ---
const onSliderChange = (value) => {
    if (value === 100) {
        isSliderVerified.value = true;
        userParams.sliderVerified = true;
        ElMessage.success('滑块验证成功！');
    } else {
        if (isSliderVerified.value) {
            isSliderVerified.value = false;
            userParams.sliderVerified = false;
        }
    }
};

const register = async () => {
    try {
        await registerFormRef.value.validate();
    } catch (e) {
        return;
    }
    loading.value = true;

    let registrationSuccess = false;
    let registeredUsername = '';

    try {
        const response = await http.post(
            '/auth/register/',
            {
                username: userParams.username,
                password: userParams.password,
                email: userParams.email,
                sliderVerified: userParams.sliderVerified
            }
        );

         if (response && response.code === 0) { // 判断 code === 0
            registrationSuccess = true;
            registeredUsername = response.user.username;

            ElNotification({
                title: '注册成功！',
                message: '接下来，请录入您的人脸信息用于登录验证。',
                type: 'success',
                duration: 2000
            });

        } else {
             // 拦截器可能已经弹窗，这里可以再加一个保险
             ElMessage.error(response?.message || '注册失败，未知错误。');
        }

    } catch (err) {
         if (!err.response) { // 如果拦截器已经处理并弹窗，这里就不再重复弹窗
            console.error("注册失败，错误未被拦截器捕获:", err);
        }
        sliderValue.value = 0;
        isSliderVerified.value = false;
        userParams.sliderVerified = false;
    } finally {
        loading.value = false;
    }

     if (registrationSuccess && registeredUsername) {
        setTimeout(() => {
            router.push({
                name: 'faceEnroll',
                query: { username: registeredUsername }
            });
        }, 1500);
    }

};

// --- 跳转到登录页 ---
const goToLogin = () => {
    router.push({ name: 'login' });
};

</script>

<style scoped>
/* 你的样式很好，保持不变 */
.register-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: linear-gradient(135deg, #7F7FD5, #86A8E7, #91EAE4);
}

.register-card {
    width: 400px;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.register-header {
    text-align: center;
    margin-bottom: 20px;
}

.register-title {
    font-size: 24px;
    font-weight: bold;
}

.sub-title {
    color: #606266;
    margin-top: 8px;
}

.slider-verify-item {
    margin-bottom: 25px;
}

.slider-component {
    width: 100%;
}

.slider-text {
    text-align: center;
    margin-top: 10px;
    font-size: 14px;
    color: #909399;
}
.slider-text.verified {
    color: #67C23A;
    font-weight: bold;
}
</style>