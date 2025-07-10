
import { createRouter, createWebHashHistory } from 'vue-router'
import { constantRoute } from './routers'

// 创建路由
let router = createRouter({
    // 路由模式，常见的模式有createWebHashHistory() 哈希模式，createWebHistory() HTML5模式
    history: createWebHashHistory(),
    routes: constantRoute,
    // 滚动行为
    scrollBehavior() {
        return {
            left: 0,
            top: 0
        }
    }
})
export default router