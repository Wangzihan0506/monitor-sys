const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000', // <--- 这里的端口号必须和你后端运行的端口号完全一致！
        changeOrigin: true,
        logLevel: 'debug'
      }
    }
  }
})
