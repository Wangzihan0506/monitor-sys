

// 路由
// constantRoute.js
export const constantRoute = [
    {
        path: "/",
        component: () => import("@/views/login/LoginIndex.vue"),
        name: "login",
        meta: {
            title: "登录",
            isMenu: false,
            icon: "UserFilled"
        }
    },
    {
        path: "/index",
        component: () => import("@/views/home/HomeIndex.vue"),
        name: "index",
        meta: {
            title: "",
            icon: "House",
            isMenu: true,
        },
        // redirect: "/home",
        // children: [
        //     {
        //         path: "/home",
        //         component: () => import("@/views/home/HomeIndex.vue"),
        //         meta: {
        //             title: "首页",
        //             isMenu: true,
        //             icon: "House"
        //         }
        //     },
        // ]
    },

    {
        path: '/admin',  // 路由路径
        component: () => import('@/views/admin/AdminIndex.vue'),  // 路由组件
        name: 'admin',  // 路由名字
        meta: {
            title: '管理',  // 菜单标题
            // isMenu:true,  // 该路由是否是菜单，如果是则显示为菜单，如果不是则不显示
            icon: 'UserFilled'  // 菜单左侧图标，支持element-plus所有图标
        }
    },
];
  

// 异步路由
export const asnycRoute = [

]