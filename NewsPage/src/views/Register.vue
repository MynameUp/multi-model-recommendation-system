<template>
  <div class="login-vue" :style="bgStyle">
    <!-- 暗色渐变遮罩 -->
    <div class="overlay"></div>
    
    <div class="auth-container">
      <!-- 顶部 Logo 区域 -->
      <div class="logo-section">
        <img src="../assets/imgs/logo.png" alt="新闻中心Logo" class="logo">
        <h1 class="title">注册账号</h1>
        <p class="subtitle">创建您的新闻中心账户，开启个性化阅读</p>
      </div>

      <div class="form-content">
        <!-- 用户ID -->
        <div class="input-group">
          <Input class="custom-input" prefix="ios-contact" v-model="account" placeholder="用户ID / User ID" size="large" clearable @on-blur="verifyUserid" @on-focus="clearError('account')" />
          <transition name="fade">
            <p class="error-msg" v-show="accountError"><Icon type="ios-alert" size="14" /> {{accountError}}</p>
          </transition>
        </div>

        <!-- 用户名 -->
        <div class="input-group">
          <Input class="custom-input" prefix="ios-person" v-model="username" placeholder="用户名 / Username" size="large" clearable @on-blur="verifyUsername" @on-focus="clearError('username')" @keyup.enter.native="submit" />
          <transition name="fade">
            <p class="error-msg" v-show="usernameError"><Icon type="ios-alert" size="14" /> {{usernameError}}</p>
          </transition>
        </div>

        <!-- 密码 -->
        <div class="input-group">
          <Input class="custom-input" type="password" v-model="pwd" prefix="md-lock" placeholder="密码 / Password" size="large" clearable @on-blur="verifyPwd" @on-focus="clearError('pwd')" @keyup.enter.native="submit" />
          <transition name="fade">
            <p class="error-msg" v-show="pwdError"><Icon type="ios-alert" size="14" /> {{pwdError}}</p>
          </transition>
        </div>

        <!-- 性别选择 -->
        <div class="input-group">
          <Select class="custom-select" v-model="gender" size="large" placeholder="请选择性别" @on-change="clearError('gender')">
            <Option v-for="item in genderlist" :value="item.value" :key="item.value">{{ item.label }}</Option>
          </Select>
          <transition name="fade">
            <p class="error-msg" v-show="genderError"><Icon type="ios-alert" size="14" /> {{genderError}}</p>
          </transition>
        </div>

        <!-- 注册按钮 -->
        <Button :loading="isShowLoading" class="submit-btn" type="success" size="large" long @click="submit">
          <span v-if="!isShowLoading">注 册</span>
          <span v-else>处理中...</span>
        </Button>

        <!-- 底部链接 -->
        <div class="action-links">
          <span class="link-item" @click="tologin">
            <Icon type="ios-log-in" size="16" /> 已有账号？立即登录
          </span>
        </div>
      </div>
    </div>

    <!-- 词云弹窗优化 -->
    <Modal v-model="word" title="请选择感兴趣的热门标签" @on-ok="ok" @on-cancel="cancel" cancel-text="跳过" class-name="tag-modal">
      <div class="tagspace">
        <Tag v-for="(item,index) in taglist" :key="index" :name="item" closable size="large" color="primary" @on-close="deleteTags(item)">
          {{ item }}
        </Tag>
        <span v-if="taglist.length === 0" class="empty-tip">暂未选择任何标签，请点击下方词云选择</span>
      </div>
      <!-- 动态词云容器 -->
      <div class="wordcloud-container">
        <div class="wordcloud" id="wordcloud"></div>
      </div>
    </Modal>
  </div>
</template>

<script>
import * as echarts from 'echarts';
import 'echarts-wordcloud';
import { getTags, register, login } from '@/api';

export default {
  name: 'UserRegister',
  data() {
    return {
      username: '',
      updata: '',
      gender: '',
      genderlist: [
        { value: '男', label: '男' },
        { value: '女', label: '女' },
      ],
      wordlist: [],
      word: false,
      charts: null,
      cloud: [],
      taglist: [],
      account: '',
      pwd: '',
      accountError: '',
      usernameError: '',
      pwdError: '',
      genderError: '',
      isShowLoading: false,
      bgStyle: {},
      redirect: undefined,
    };
  },
  watch: {
    $route: {
      handler(route) {
        this.redirect = route.query && route.query.redirect;
      },
      immediate: true,
    },
    // 监听 word 弹窗打开，确保词云 DOM 加载完毕后再渲染 ECharts
    word(newVal) {
      if (newVal) {
        this.$nextTick(() => {
          this.initChart();
        });
      }
    }
  },
  created() {
    // 动态背景逻辑
    const day = new Date().getDay();
    const bgIndex = day === 0 ? 6 : day;
    this.bgStyle = {
      backgroundImage: `url(${require('../assets/imgs/bg0' + bgIndex + '.jpg')})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat'
    };
  },
  mounted() {
    // 提前获取词云数据
    getTags().then((res) => {
      this.wordlist = res.message;
      res.message.forEach((item) => {
        this.cloud.push({
          name: item,
          value: Math.random() * 50 + 10,
        });
      });
    });
  },
  methods: {
    // 初始化 ECharts
    initChart() {
      const chartDom = document.getElementById('wordcloud');
      if (chartDom && !this.charts) {
        const chart = echarts.init(chartDom);
        chart.on('click', this.eConsole);
        this.charts = chart;
      }
      if (this.charts) {
        this.renderCloud(this.charts);
      }
    },
    // 清除错误提示
    clearError(field) {
      if (field === 'account') this.accountError = '';
      if (field === 'username') this.usernameError = '';
      if (field === 'pwd') this.pwdError = '';
      if (field === 'gender') this.genderError = '';
    },
    verifyUserid() {
      if (!this.account) this.accountError = '账号不能为空';
    },
    verifyUsername() {
      if (!this.username) this.usernameError = '用户名不能为空';
    },
    verifyPwd() {
      if (!this.pwd) this.pwdError = '密码不能为空';
    },
    verifyGender() {
      if (!this.gender) this.genderError = '请选择性别';
    },
    tologin() {
      this.$router.push({ name: 'login' });
    },
    submit() {
      this.verifyUserid();
      this.verifyUsername();
      this.verifyPwd();
      this.verifyGender();
      
      if (this.account && this.pwd && this.gender && this.username) {
        this.word = true; // 打开弹窗
      } else {
        this.$Message.warning('请检查并填写完整信息');
      }
    },
    renderCloud(chartInstance) {
      const option = {
        series: [{
          type: 'wordCloud',
          shape: 'circle',
          left: 'center',
          top: 'center',
          width: '90%',
          height: '90%',
          sizeRange: [14, 50],
          rotationRange: [-45, 45],
          rotationStep: 15,
          gridSize: 10,
          drawOutOfBound: false,
          layoutAnimation: true,
          textStyle: {
            fontFamily: 'sans-serif',
            fontWeight: 'bold',
            color: () => `rgb(${[
              Math.round(Math.random() * 100 + 100),
              Math.round(Math.random() * 100 + 100),
              Math.round(Math.random() * 100 + 100),
            ].join(',')})`,
          },
          emphasis: {
            focus: 'self',
            textStyle: { shadowBlur: 10, shadowColor: '#333' },
          },
          data: this.cloud,
        }],
      };
      chartInstance.setOption(option, true);
    },
    ok() {
      this.isShowLoading = true;
      register(this.account, this.pwd, this.username, String(this.taglist.join()), this.gender).then((res) => {
        if (res.message === 'Success.') {
          sessionStorage.setItem('userId', res.data.userid);  // 使用后端返回的真实数字ID
          sessionStorage.setItem('userName', res.data.username);  // 使用后端返回的用户名，防止本地值与服务端不一致
          sessionStorage.setItem('token', 'i_am_token');
          this.$router.push({ path: this.redirect || '/' });
          this.$Message.success('成功注册！欢迎加入！');
        } else {
          this.accountError = '注册失败，账号可能已存在';
          this.isShowLoading = false;
        }
      }).catch(() => {
        this.isShowLoading = false;
        this.$Message.error('网络请求失败');
      });
    },
    cancel() {
      if (this.account && this.pwd) {
        this.isShowLoading = true;
        login(this.account, this.pwd).then((res) => {
          if (res.message === 'Success.') {
            sessionStorage.setItem('userId', res.data.userid);
            sessionStorage.setItem('userName', res.data.username);
            sessionStorage.setItem('token', 'i_am_token');
            this.$router.push({ path: this.redirect || '/' });
            this.$Message.success('登录成功！');
          } else {
            this.accountError = '账号或密码错误';
            this.isShowLoading = false;
          }
        });
      }
    },
    deleteTags(item) {
      this.taglist = this.taglist.filter((tag) => tag !== item);
    },
    eConsole(param) {
      if (param.name && !this.taglist.includes(param.name)) {
        this.taglist.push(param.name);
        this.cloud = this.cloud.filter((word) => word.name !== param.name);
        this.renderCloud(this.charts);
      } else {
        this.$Message.warning('该标签已选择');
      }
    }
  },
};
</script>

<style scoped>
/* 全屏背景与基础布局 */
.login-vue {
  position: relative;
  width: 100vw;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}

/* 黑色半透明渐变遮罩 */
.overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.4) 0%, rgba(0, 0, 0, 0.7) 100%);
  z-index: 1;
}

/* 毛玻璃主容器 */
.auth-container {
  position: relative;
  z-index: 2;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  width: 450px;
  max-width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  text-align: center;
  border-radius: 20px;
  padding: 40px 35px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.18);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.auth-container::-webkit-scrollbar {
  width: 6px;
}
.auth-container::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
}

/* 顶部 Logo 区域 */
.logo-section {
  margin-bottom: 25px;
}
.logo-section .logo {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  object-fit: cover;
  margin-bottom: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  transition: transform 0.3s ease;
}
.logo-section .logo:hover {
  transform: scale(1.05) rotate(5deg);
}
.logo-section .title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #fff;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
  letter-spacing: 2px;
}
.logo-section .subtitle {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
}

/* 表单输入区域 */
.form-content .input-group {
  margin: 18px auto;
  width: 100%;
  max-width: 340px;
  text-align: left;
}

/* 深度定制 ViewUI 的 Input 组件以适应毛玻璃 */
.custom-input /deep/ .ivu-input {
  background-color: rgba(255, 255, 255, 0.15);
  color: #fff;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 10px;
  padding-left: 35px;
  font-size: 14px;
  height: 44px;
  transition: all 0.3s ease;
}
.custom-input /deep/ .ivu-input:focus {
  border-color: rgba(255, 255, 255, 0.8);
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.2);
  background-color: rgba(255, 255, 255, 0.25);
}
.custom-input /deep/ .ivu-input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}
.custom-input /deep/ .ivu-icon {
  color: rgba(255, 255, 255, 0.85);
  font-size: 18px;
  line-height: 44px;
}

/* 深度定制 ViewUI 的 Select 组件 */
.custom-select /deep/ .ivu-select-selection {
  background-color: rgba(255, 255, 255, 0.15);
  color: #fff;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 10px;
  height: 44px;
  transition: all 0.3s ease;
}
.custom-select /deep/ .ivu-select-selection:hover,
.custom-select /deep/ .ivu-select-selection-focused {
  border-color: rgba(255, 255, 255, 0.8);
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.2);
}
.custom-select /deep/ .ivu-select-selected-value,
.custom-select /deep/ .ivu-select-placeholder {
  color: #fff !important;
  line-height: 44px;
  font-size: 14px;
}
.custom-select /deep/ .ivu-icon {
  color: rgba(255, 255, 255, 0.85);
  line-height: 44px;
}

/* 错误提示文字 */
.error-msg {
  color: #ff6b6b;
  margin: 4px 0 0 5px;
  font-size: 12px;
  height: 18px;
  display: flex;
  align-items: center;
  gap: 5px;
}

/* 渐变特效注册按钮 */
.submit-btn {
  width: 100%;
  max-width: 340px;
  margin: 10px auto 20px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 10px;
  background: linear-gradient(135deg, #19be6b 0%, #33c759 100%);
  border: none;
  box-shadow: 0 4px 15px rgba(25, 190, 107, 0.4);
  height: 46px;
  transition: all 0.3s ease;
}
.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(25, 190, 107, 0.5);
}

/* 底部操作链接 */
.action-links {
  margin-top: 15px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.85);
}
.action-links .link-item {
  cursor: pointer;
  transition: all 0.3s ease;
  padding: 5px 8px;
  border-radius: 6px;
  color: #ffd93d;
  font-weight: bold;
}
.action-links .link-item:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.15);
}

/* Vue 过渡动画 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}

/* ====== 弹窗内部样式精修 ====== */
.tagspace {
  min-height: 60px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 15px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.tagspace .empty-tip {
  color: #999;
  font-size: 13px;
  width: 100%;
  text-align: center;
}
.wordcloud-container {
  width: 100%;
  height: 350px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #eee;
  overflow: hidden;
}
.wordcloud {
  width: 100%;
  height: 100%;
}
</style>