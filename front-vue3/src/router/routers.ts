// 路由
// constantRoute.js

export const constantRoute = [
    {
        path: "/",
        component: () => import("@/views/welcome/WelcomePage.vue"),
        name: "welcome",
        meta: {
            title: "欢迎",
            isMenu: false,
            icon: "Start"
        }
    },
    {
        path: "/login",
        component: () => import("@/views/login/LoginIndex.vue"),
        name: "login",
        meta: {
            title: "登录",
            icon: "UserFilled",
            isMenu: false,
        },

    },

    {
        //人脸登录页面
        path: "/face-login/:username",
        component: () => import("@/views/face/FaceLogin.vue"),
        name: "faceLogin", // 独立的路由名称
        props: true,
        meta: {
            title: "人脸登录",
            isMenu: false,
            icon: "CameraFilled" // 例如摄像头图标
        }
    },

    {
        path: "/register",
        component: () => import("@/views/register/RegisterIndex.vue"),
        name: "register",
        meta: {
            title: "注册",
            isMenu: false,
            icon:"Edit",
        }
    },
    {
        // 人脸录入页面
        path: "/face-enroll",
        component: ()=>import("@/views/face/FaceEnroll.vue"), // 人脸录入组件
        name: "faceEnroll", // 独立的路由名称
        meta: {
            title: "人脸录入",
            isMenu: false,
            icon: "CameraFilled"
        }
    },

    {
        // 主页面 (登录成功后进入)
        path: "/home",
        component: ()=>import("@/views/admin/AdminIndex.vue"),
        name: "home",
        meta: {
            title: "首页",
            icon: "House",
            isMenu: true, // 这个页面应该在菜单中显示
        },
    },

    {
        path: '/admin',
        component: () => import("@/views/register/RegisterIndex.vue"),  // 路由组件
        name: 'admin',  // 路由名字
        meta: {
            title: '管理',  // 菜单标题
            // isMenu:true,  // 该路由是否是菜单，如果是则显示为菜单，如果不是则不显示
            icon: 'UserFilled'  // 菜单左侧图标，支持element-plus所有图标
        }
    },

    {
        path: '/checkin',
        component: () => import("@/views/home/HomeIndex.vue"),  // 路由组件
        name: 'checkin',  // 路由名字
        meta: {
            title: '签到',  // 菜单标题
            // isMenu:true,  // 该路由是否是菜单，如果是则显示为菜单，如果不是则不显示
            icon: 'UserFilled'  // 菜单左侧图标，支持element-plus所有图标
        }
    },

];
  

// 异步路由
export const asnycRoute = [

]