import axios from 'axios'
import { ElMessage } from 'element-plus';
import Cookies from "js-cookie";


let REMOTE_HOST = window.location.hostname || '127.0.0.1'  // 远程主机地址

axios.defaults.withCredentials = true;  // 允许请求携带cookie参数

let baseURL = `http://${REMOTE_HOST}:5000/api/`
console.log("baseURL:", baseURL);

const http = axios.create({
    // baseURL:`http://${REMOTE_HOST}:5000/api/`,  // 设置基础路径
    baseURL: baseURL,  // 设置基础路径
    timeout: 10000,  // 设置超时时间为10秒
});

// 获取 csrftoken
async function get_csrftoken() {
    await http({
        url: 'get_csrftoken/',
        method: 'get'
    }).then(res => {
        if (res.data.code == 200) {
            console.log("code");

        }
    })

    let csrf_token = Cookies.get('csrftoken')

    return csrf_token
}

// 请求拦截器
http.interceptors.request.use(async (config) => {
    // 请求拦截器，可以在这里面设置请求头等配置信息
    // 如果发送的是post，put，delete请求，则先获取csrf_token
    if (config.method == 'POST' || config.method == 'post' || config.method == 'PUT' || config.method == 'put' ||
        config.method == 'DELETE' || config.method == 'delete'
    ) {
        // 如果是post请求，则先获取csrftoken，flask发送post请求需要验证请求头中的csrftoken
        let csrf_token = await get_csrftoken()
        config.headers["X-CSRFToken"] = csrf_token
    }

    // if (userStore.username) {
    //     config.headers.username = userStore.username  // 如果用户已经登录了，则把用户名附加到请求头中
    // }

    return config
})

// 响应拦截器
http.interceptors.response.use((response) => {
    // 可以在这里添加请求成功后执行的操作
    return response
}, (error) => {
    // 请求发生错误时，显示错误消息
    let message = ''
    console.log(error);
    let status = error.response?.status
    switch (status) {
        case 401:
            message = 'token过期'
            break
        case 403:
            message = '没有权限访问'
            break
        case 404:
            message = '请求地址错误'
            break
        case 500:
            message = '服务器错误'
            break
        default:
            message = '网络错误'
            break
    }
    // 显示错误信息
    ElMessage({
        type: 'error',
        message
    })
    return Promise.reject(error)
})

export default http