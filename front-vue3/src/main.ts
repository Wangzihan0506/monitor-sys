import { createApp } from 'vue'
import App from './App.vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import ElementPlus from 'element-plus'
import router from './router'
import 'element-plus/dist/index.css';

const app = createApp(App);

app.use(ElementPlus, {
    locale: zhCn
})
app.use(router);

app.mount('#app')
