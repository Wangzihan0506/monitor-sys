
import { defineStore } from 'pinia'
import { constantRoute, asnycRoute } from '@/router/routers'
import { reqLogin } from '@/api/user'
import router from '@/router'
// import {extend} from '@/utils/tools'
import cloneDeep from 'lodash/cloneDeep'
import { ElMessage } from 'element-plus'

// defineStore用来创建小仓库，参数1是仓库名，参数2是一个对象
let useUserStore = defineStore('User', {
    state: () => {
        return {
            // token:JSON.parse(localStorage.getItem('token')),
            userInfo: JSON.parse(localStorage.getItem('userInfo')),
            username: JSON.parse(localStorage.getItem('username')),
            avatar: JSON.parse(localStorage.getItem('avatar')),
            real_name: JSON.parse(localStorage.getItem('real_name')),
            userRouters: JSON.parse(localStorage.getItem('userRouters')),  // 获取用户的路由
            userButtons: JSON.parse(localStorage.getItem('userButtons')),  // 获取用户的按钮
            // menuRoutes: JSON.parse(localStorage.getItem('menuRoutes')) || constantRoute,  // 获取路由菜单，如果localStorage中已经有了则获取，如果没有则获取默认菜单constantRoute
            menuRoutes: constantRoute,  // 保存路由，这个没怎么用
            routersArr: [],  // 测试
        }
    },
    actions: {
        // 用户登录方法
        async userLogin(data) {

            await reqLogin(data).then(res => {
                if (res.data.code == 200) {
                    this.saveUserInfo(res)
                    return 'ok'
                } else {
                    return Promise.reject(new Error(res.data.msg))
                }
            })
        },

        // 保存用户数据到本地
        saveUserInfo(res) {
            // 保存登录信息
            this.userInfo = res.data.data
            this.username = res.data.data.username
            this.avatar = res.data.data.avatar
            this.real_name = res.data.data.real_name
            localStorage.setItem('userInfo', JSON.stringify(res.data.data))
            localStorage.setItem('username', JSON.stringify(res.data.data.username))
            localStorage.setItem('avatar', JSON.stringify(res.data.data.avatar))
            localStorage.setItem('real_name', JSON.stringify(res.data.data.real_name))

            // 获取用户能访问的路由和功能
            let userRouters = []
            res.data.data.routers.forEach(item => {
                if (item.code) {
                    userRouters.push(item.code)
                }
            })
            localStorage.setItem('userRouters', JSON.stringify(userRouters))  // 保存用户路由权限
            this.userRouters = userRouters  // 保存一份
            this.addUserRote(userRouters)

            // 获取用户能使用的按钮
            let userButtons = []
            res.data.data.buttons.forEach(item => {
                if (item.code) {
                    userButtons.push(item.code)
                }
            })
            localStorage.setItem('userButtons', JSON.stringify(userButtons))  // 保存用户能使用的按钮
            this.userButtons = userButtons  // 在仓库里保存一份
        }
        ,
        // 用户登出
        async userLogout() {
            try {
                // let res = await reqLogout()
            } catch (err) {
                console.log(err);
            }

            // 删除路由信息
            this.userRouters.forEach(item => {
                // 退出登录时，清除异步路由
                if (router.hasRoute(item)) {
                    router.removeRoute(item)
                }
            })
            this.userInfo = ''
            this.username = ''
            this.avatar = ''
            this.real_name = ''
            localStorage.clear();  // 清空保存在本地localStorage中的所有数据

        },
        // 获取用户有权限的菜单和按钮
        filterAsyncRoute(asnycRoute, userRouters, routersArr = []) {

            for (let item of asnycRoute) {
                if (item.children && item.children.length > 0) {
                    let ret = this.filterAsyncRoute(item.children, userRouters, [])
                    if (ret) {
                        item.children = ret
                        routersArr.push(item)
                    }
                } else {
                    if (userRouters.includes(item.name)) {
                        routersArr.push(item)
                    }
                }


            }

            return routersArr
        },
        // 把用户有权访问的路由添加进本地路由
        addUserRote(userRouters) {

            let userAsyncRoute = this.filterAsyncRoute(cloneDeep(asnycRoute), userRouters)
            this.menuRoutes = constantRoute.concat(userAsyncRoute)

            userAsyncRoute.forEach(item => {
                router.addRoute(item)  // 注册路由
            })

        }
    },
    getters: {

    }
})

export default useUserStore