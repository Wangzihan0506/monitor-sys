import http from '@/utils/http.js'

// —— 登录/重置密码相关接口 ——

// 获取验证码
// export const reqGetVerifyCode = () => http.get('get_verify_code/')

export const reqGetVerifyCode = () =>
    http.get('get_verify_code/', {
        responseType: 'blob',      // ← 告诉 Axios：把响应当成 Blob 处理
        withCredentials: true      // ← 如果你有设置 cookie，需要带上它
    })

// 重置密码
export const reqResetPassword = (data) => http.post('reset_password/', data)

// —— 用户管理模块的接口 ——
// URL 接口地址常量
const API = {
    ALLUSER_URL: 'custom_admin/acl/user/',         // 获取所有用户接口
    ADDUSER_URL: 'custom_admin/acl/user/save/',    // 添加用户
    UPDATAUSER_URL: 'custom_admin/acl/user/update/',  // 更新用户
    ALLROLE_URL: 'custom_admin/acl/user/allRole/', // 获取全部角色
    GETUSERROLE_URL: 'custom_admin/acl/user/getUserRole/', // 获取用户的角色
    SETUSERROLE_URL: 'custom_admin/acl/user/setUserRole/', // 更改用户的角色
    DELETEUSER_URL: 'custom_admin/acl/user/remove/',  // 删除单个账号
    BATCHDELETEUSER_URL: 'custom_admin/acl/user/batchRemove/' // 删除多个账号
}


// 拉取待补签用户（支持搜索、分页）
export const reqGetPatchUsers = ({ search = '', page = 1, per_page = 10 }) =>
    http.get('/attendance/patch/users', { params: { search, page, per_page } })

// 执行补签操作
export const reqPatchSign = ({ userId, patchTime }) =>
    http.post('/attendance/patch', { userId, patchTime })


// 获取所有用户接口方法（分页，可按用户名或类型搜索）
export const reqUserInfo = (page, size, username, search_type) =>
    http.get(
        API.ALLUSER_URL + `${page}/${size}/`,
        { params: { username, search_type } }
    )

export const reqLogin = data => http.post('/login/', data, { withCredentials: true })

// 添加或更新用户
export const reqAddOrUpdateUser = (data) => {
    if (data.id) {
        // 有 id 表示更新
        return http.put(API.UPDATAUSER_URL, data)
    } else {
        // 无 id 表示新增
        return http.post(API.ADDUSER_URL, data)
    }
}

// 获取全部角色
export const reqAllRole = () => http.get(API.ALLROLE_URL)

// 获取用户的角色
export const reqGetUserRole = (userId) => http.get(API.GETUSERROLE_URL + userId + '/')

// 更改用户角色
export const reqSetUserRole = (data) => http.post(API.SETUSERROLE_URL, data)

// 删除单个用户
export const reqRemoveUser = (userId) => http.delete(API.DELETEUSER_URL + userId + '/')

// 批量删除用户
export const reqBatchRemoveUser = (data) => http.put(API.BATCHDELETEUSER_URL, data)
