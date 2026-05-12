<template>
  <div class="login-vue" :style="bgStyle">
    <div class="overlay"></div>
    
    <div class="auth-container">
      <div class="logo-section">
        <img src="../assets/imgs/logo.png" alt="新闻中心Logo" class="logo">
        <h1 class="title">新闻中心</h1>
        <p class="subtitle">实时资讯 · 全球视野 · 互动交流</p>
      </div>

      <div class="form-content">
        <div class="input-group">
          <Input 
            class="custom-input"
            prefix="ios-contact" 
            v-model="account" 
            placeholder="用户名 / User ID" 
            size="large"
            clearable 
            @on-blur="verifyAccount"
            @on-focus="clearError('account')"
          />
          <transition name="fade">
            <p class="error-msg" v-show="accountError">
              <Icon type="ios-alert" size="14" /> {{accountError}}
            </p>
          </transition>
        </div>

        <div class="input-group">
          <Input 
            class="custom-input"
            type="password" 
            v-model="pwd" 
            prefix="md-lock" 
            placeholder="密码 / Password" 
            size="large"
            clearable 
            @on-blur="verifyPwd"
            @on-focus="clearError('pwd')"
            @keyup.enter.native="submit" 
          />
          <transition name="fade">
            <p class="error-msg" v-show="pwdError">
              <Icon type="ios-alert" size="14" /> {{pwdError}}
            </p>
          </transition>
        </div>

        <Button 
          :loading="isShowLoading" 
          class="submit-btn" 
          type="primary" 
          size="large"
          long
          @click="submit">
          <span v-if="!isShowLoading">登 录</span>
          <span v-else>登录中...</span>
        </Button>

        <div class="action-links">
          <span class="link-item" @click="register">
            <Icon type="ios-person-add" size="16" /> 注册账号
          </span>
          <span class="divider">|</span>
          <span class="link-item" @click="forgetPwd">
             忘记密码
          </span>
          <span class="divider">|</span>
          <span class="link-item tourist-link" @click="tourists">
            <Icon type="ios-walk" size="16" /> 游客模式
          </span>
        </div>
      </div>

      <div class="features">
        <div class="feature-item">
          <div class="feature-icon">
            <Icon type="ios-paper" size="24" />
          </div>
          <span>海量资讯</span>
        </div>
        <div class="feature-item">
          <div class="feature-icon">
            <Icon type="ios-speedometer" size="24" />
          </div>
          <span>实时更新</span>
        </div>
        <div class="feature-item">
          <div class="feature-icon">
            <Icon type="ios-heart" size="24" />
          </div>
          <span>个性推荐</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { login, getTourists } from '@/api'

export default {
  name: "UserLogin",
  data() {
    return {
      account: '',
      pwd: '',
      accountError: '',
      pwdError: '',
      isShowLoading: false,
      bgStyle: {},
      redirect: undefined
    }
  },
  created() {
    // token存在直接跳转
    let token = sessionStorage.getItem('token')
    if (token !== null && token !== '') {
      this.$router.push({ name: 'home' })
    }
    this.setBackground();
  },
  watch: {
    $route: {
      handler(route) {
        this.redirect = route.query && route.query.redirect
      },
      immediate: true,
    },
  },
  methods: {
    setBackground() {
      let day = new Date().getDay();
      let bgIndex = day === 0 ? 6 : day; 
      this.bgStyle = {
        backgroundImage: `url(${require('../assets/imgs/bg0' + bgIndex + '.jpg')})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat'
      };
    },
    clearError(field) {
      if (field === 'account') this.accountError = '';
      if (field === 'pwd') this.pwdError = '';
    },
    tourists() {
      getTourists().then(res => {
        // 修改：提取头像文件名
        const headPortrait = res.data.headPortrait
        if (headPortrait && headPortrait !== '' && headPortrait !== 'null' && headPortrait !== 'undefined') {
          const fileName = headPortrait.split('/').pop()
          sessionStorage.setItem('userImg', fileName)
        } else {
          sessionStorage.setItem('userImg', '')
        }
        
        sessionStorage.setItem('userName', res.data.username)
        sessionStorage.setItem('userId', res.data.userid)
        sessionStorage.setItem('gender', res.data.gender)
        sessionStorage.setItem('token', 'i_am_token')
        this.$router.push({ path: this.redirect || '/' })
        this.$Message.success('欢迎游客！完整功能请注册并登录账号')
      })
    },
    verifyAccount() {
      if (this.account === '') {
        this.accountError = '账号不能为空'
      } else {
        this.accountError = ''
      }
    },
    verifyPwd() {
      if (this.pwd === '') {
        this.pwdError = '密码不能为空'
      } else {
        this.pwdError = ''
      }
    },
    register() {
      this.$router.push({ name: 'register' })
    },
    forgetPwd() {
      this.$Message.info('忘记密码功能暂未开放，请联系管理员')
    },
    submit() {
      this.verifyAccount();
      this.verifyPwd();
      
      if (this.account !== '' && this.pwd !== '') {
        this.isShowLoading = true
        login(this.account, this.pwd).then(res => {
          if (res.message === 'Success.') {
            // 修改：登录成功后提取头像文件名
            const headPortrait = res.data.headPortrait
            if (headPortrait && headPortrait !== '' && headPortrait !== 'null' && headPortrait !== 'undefined') {
              const fileName = headPortrait.split('/').pop()
              sessionStorage.setItem('userImg', fileName)
            } else {
              sessionStorage.setItem('userImg', '')
            }

            sessionStorage.setItem('userName', res.data.username)
            sessionStorage.setItem('userId', res.data.userid)
            sessionStorage.setItem('gender', res.data.gender)
            sessionStorage.setItem('token', 'i_am_token')
            this.$router.push({ path: this.redirect || '/' })
            this.$Message.success('登录成功！')
          } else {
            this.accountError = '账号或密码错误'
            this.pwdError = ''
            this.isShowLoading = false
            this.$Message.error('账号或密码错误')
          }
        }).catch(() => {
          this.isShowLoading = false
          this.$Message.error('网络请求失败')
        })
      }
    },
  },
}
</script>

<style scoped>
/* 保持原有样式不变 */
.login-vue {
  position: relative;
  width: 100vw;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}

.overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.4) 0%, rgba(0, 0, 0, 0.7) 100%);
  z-index: 1;
}

.auth-container {
  position: relative;
  z-index: 2;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  width: 420px;
  max-width: 90%;
  text-align: center;
  border-radius: 20px;
  padding: 45px 35px 25px 35px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.18);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.auth-container:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
}

.logo-section {
  margin-bottom: 25px;
}
.logo-section .logo {
  width: 75px;
  height: 75px;
  border-radius: 50%;
  object-fit: cover;
  margin-bottom: 15px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  transition: transform 0.3s ease;
}
.logo-section .logo:hover {
  transform: scale(1.05) rotate(5deg);
}
.logo-section .title {
  font-size: 26px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #fff;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
  letter-spacing: 3px;
}
.logo-section .subtitle {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
  letter-spacing: 1px;
}

.form-content .input-group {
  margin: 22px auto;
  width: 100%;
  max-width: 320px;
  text-align: left;
}

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

.error-msg {
  color: #ff6b6b;
  margin: 6px 0 0 5px;
  font-size: 12px;
  height: 18px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.submit-btn {
  width: 100%;
  max-width: 320px;
  margin: 10px auto 22px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 10px;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  border: none;
  box-shadow: 0 4px 15px rgba(79, 172, 254, 0.4);
  height: 46px;
  transition: all 0.3s ease;
}
.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(79, 172, 254, 0.5);
}

.action-links {
  margin-top: 15px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.action-links .link-item {
  cursor: pointer;
  transition: all 0.3s ease;
  padding: 5px 8px;
  border-radius: 6px;
}
.action-links .link-item:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.15);
}
.action-links .divider {
  opacity: 0.4;
}
.action-links .tourist-link {
  color: #ffd93d;
  font-weight: bold;
}

.features {
  display: flex;
  justify-content: space-around;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}
.features .feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
  transition: transform 0.3s ease;
}
.features .feature-item:hover {
  transform: translateY(-3px);
}
.features .feature-icon {
  margin-bottom: 8px;
  padding: 8px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}
.features .feature-item:hover .feature-icon {
  background: rgba(255, 255, 255, 0.2);
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}

@media (max-width: 480px) {
  .auth-container {
    width: 90%;
    padding: 30px 20px;
    border-radius: 15px;
  }
  .logo-section .logo {
    width: 60px;
    height: 60px;
  }
  .logo-section .title {
    font-size: 22px;
  }
  .action-links {
    font-size: 12px;
    flex-wrap: wrap;
  }
  .features .feature-item {
    font-size: 11px;
  }
  .features .feature-icon {
    padding: 6px;
  }
}
</style>