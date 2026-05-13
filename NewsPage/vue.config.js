const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    proxy: {
      // 拦截所有以 '/api' 开头的请求
      '/api': {
        target: 'http://127.0.0.1:8000', // 你的 Django 后端地址
        changeOrigin: true,              // 允许跨域
        pathRewrite: {
          '^/api': ''                    // 核心魔法：把 '/api' 抹掉。这样 '/api/news/all/' 就会变成后端的 '/news/all/'
        }
      }
    }
  }
})