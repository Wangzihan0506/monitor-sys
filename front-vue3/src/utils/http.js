import axios from 'axios'
import { ElMessage } from 'element-plus';
import Cookies from "js-cookie";
//import router from '@/router';

const REMOTE_HOST = window.location.hostname || '127.0.0.1'  // 远程主机地址

axios.defaults.withCredentials = true;  // 允许请求携带cookie参数

const baseURL = `http://${REMOTE_HOST}:5000/api/`
console.log("baseURL:", baseURL);

const http = axios.create({
    baseURL: 'http://localhost:5000/api', //
    timeout: 60000, // 请求超时时间
    withCredentials: true // 允许跨域请求发送 cookie
});

// 获取 csrftoken
// eslint-disable-next-line @typescript-eslint/no-unused-vars
async function get_csrftoken() {
    await http({
        url: 'get_csrftoken/',
        method: 'get'
    }).then(res => {
        if (res.data.code == 200) {
            console.log("code");
        }
    })

    const csrf_token = Cookies.get('csrftoken')

    return csrf_token
}

//请求拦截器
http.interceptors.request.use(
  (config) => {
    // 在每个请求发送出去之前，执行这个函数
    const token = localStorage.getItem('token');

    // 如果本地存储中有 token，就把它加到请求头里
    if (token) {
      // 'Authorization' 是后端检查的标准请求头字段
      // 'Bearer ' 是 JWT token 的标准前缀，注意后面有个空格
      config.headers['Authorization'] = `Bearer ${token}`;
    }

    // 必须返回 config 对象，否则请求会卡住
    return config;
  },
  (error) => {
    // 对请求错误做些什么
    console.error('请求在发送时出错:', error);
    return Promise.reject(error);
  }
);


// 响应拦截器
http.interceptors.response.use(

  // 参数一：处理 HTTP 状态码为 2xx 的情况
  (response) => {
    const res = response.data;

    if (res.code === 0) {

      return res;

    } else {

      // 1. 弹出一个统一的错误提示
      ElMessage({
        message: res.msg || '操作失败，但服务器未返回明确错误信息。',
        type: 'error',
        duration: 5 * 1000,
      });

      // 2.创建一个自定义的错误对象并 reject
      // 这个对象模仿了 Axios 的错误结构，包含了原始的 response 信息
      const customError = {
        isBusinessError: true, // 添加一个自定义标志
        response: response,    // 把完整的原始 response 放进去
        message: res.msg || '业务逻辑错误',
      };
      return Promise.reject(customError);
    }
  },

  // 参数二：处理 HTTP 状态码非 2xx 的情况
  (error) => {
    console.error('HTTP请求错误:', error); // 打印详细错误以供调试

    // 确保有 error.response，否则可能是网络中断等问题
    const message = error.response?.data?.msg || error.message || '服务器请求发生未知错误';

    ElMessage({
      message: message,
      type: 'error',
      duration: 5 * 1000,
    });

    // 直接 reject 原始的 Axios 错误
    return Promise.reject(error);
  }
);

export default http