import Vue from 'vue';
import axios from 'axios';
import ViewUI from 'view-design';
import vuescroll from 'vuescroll';
import VideoPlayer from 'vue-video-player';
import ElementUI from 'element-ui';
import locale from 'element-ui/lib/locale/lang/zh-CN';  // 新增：引入中文语言包
import 'view-design/dist/styles/iview.css';
import 'vuescroll/dist/vuescroll.css';
import 'element-ui/lib/theme-chalk/index.css';
import 'video.js/dist/video-js.css'; // [修改] 使用 import 替代 require
// [修改] 删掉或注释掉下面这行，它是报错的主因
// import 'vue-video-player/src/custom-theme.css';

import App from './App';
import router from './router';

Vue.use(VideoPlayer);
Vue.use(ElementUI, { locale });  // 修改：传入中文语言包配置
Vue.use(vuescroll);
Vue.use(ViewUI);

Vue.config.productionTip = false;
Vue.prototype.$axios = axios;

// 修改后的 main.js 实例化部分
new Vue({
  router,
  // [关键修复] 使用 render 函数代替 template 属性
  // h 是 createElement 的缩写，这行代码直接告诉 Vue 渲染 App 组件
  render: h => h(App)
}).$mount('#app'); // 使用 $mount 显式挂载到 index.html 的 #app 节点上
