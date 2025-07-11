<template>
  <div class="welcome-container">
    <h1 class="welcome-title">{{ appName }}</h1>
    <p class="welcome-description">欢迎来到 {{ appName }}！请选择登录或注册以继续。</p>

    <div class="auth-options">
      <!-- 使用 router-link 进行路由导航 -->
      <!-- to="/login" 指向你的登录页面路由路径 -->
      <!-- to="/register" 指向你的注册页面路由路径 -->
      <!-- 更好的做法是使用路由名称 -->
      <router-link :to="{ name: 'login' }" class="auth-button login-button">登录</router-link>
      <router-link :to="{ name: 'register' }" class="auth-button register-button">注册</router-link>

      <!-- 如果你的路由没有命名，可以使用路径 -->
      <!-- <router-link to="/login" class="auth-button login-button">登录</router-link> -->
      <!-- <router-link to="/register" class="auth-button register-button">注册</router-link> -->
    </div>
  </div>
</template>

<script>
export default {
  name: 'WelcomePage', // 组件名称
  data() {
    return {
      appName: '餐厅安全监测系统' // 在这里设置你的应用名称
    };
  }
  // 如果这个页面不需要复杂的逻辑，<script> 部分可以很简单甚至省略 data
}
</script>

<style scoped>
/* 样式使页面看起来更好一些 */
.welcome-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 80vh; /* 至少占视口高度的80% */
  text-align: center;
  padding: 20px;
  background-color: #f8f9fa; /* 轻微的背景色 */
}

.welcome-title {
  font-size: 2.5em;
  color: #333;
  margin-bottom: 20px;
}

.welcome-description {
  font-size: 1.2em;
  color: #666;
  margin-bottom: 30px;
  max-width: 600px; /* 限制描述宽度 */
}

.auth-options {
  display: flex;
  gap: 20px; /* 按钮之间的间距 */
}

.auth-button {
  display: inline-block; /* 使 padding 和 margin 生效 */
  padding: 12px 25px;
  font-size: 1.1em;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  text-decoration: none; /* 移除 router-link 的下划线 */
  transition: background-color 0.3s ease, opacity 0.3s ease;
}

.login-button {
  background-color: #007bff; /* 蓝色背景 */
  color: white;
}

.login-button:hover {
  background-color: #0056b3; /* 悬停变深 */
  opacity: 0.9;
}

.register-button {
  background-color: #28a745; /* 绿色背景 */
  color: white;
}

.register-button:hover {
  background-color: #218838; /* 悬停变深 */
  opacity: 0.9;
}
</style>