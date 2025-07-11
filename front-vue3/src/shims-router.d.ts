/* eslint-disable */
// 这是一个为 JavaScript 文件 ./router 导出的模块提供基本类型的示例
// 你需要根据你的 router/index.js 实际导出的内容来调整这个声明
declare module './router' {
  import { Router } from 'vue-router'; // 假设你导出了一个 Router 实例
  const router: Router; // 声明导出的变量及其类型
  export default router; // 如果是默认导出
  // 如果有命名导出，也在这里声明，例如：
  // export const constantRoute: Array<any>;
  // export const asnycRoute: Array<any>;
}