<template>
  <div >
    <Menu mode="horizontal" :active-name="activename" >
      <MenuItem name="1">
        <img src="../assets/imgs/logo4.png" width="90px" style="margin-top: 10px;">
      </MenuItem>
      <MenuItem name="2" to="/home" >
        <Icon type="md-home"/>
        首页
      </MenuItem>
      <MenuItem name="3" to="/recommend" v-if="displayornot">
        <Icon type="ios-star"/>
        为你推荐
      </MenuItem>
       <MenuItem name="4" to="/intelligent-recommend" v-if="displayornot">
        <Icon type="ios-robot"/>
        智能推荐
      </MenuItem>
      <MenuItem name="5" to="/eventhot">
        <Icon type="md-clock"/>
        时事热点
      </MenuItem>
      <!--        <Badge dot style="display: inline-block; float: right; margin-right: 70px; margin-top: 4px;">-->
      <!--          <Icon type="ios-notifications-outline" size="30" ></Icon>-->
      <!--        </Badge>-->
      <Dropdown style="display: inline-block; float: right; margin-right: 2%; cursor: pointer;" trigger="click"  @on-click="userOperate" >
        <Badge v-if="this.tip === 1" dot  :offset=[12,8]>
          <Avatar :src="userImg" icon="ios-person" size="large"></Avatar>
        </Badge>
        <Badge v-if="this.tip === 0"  :offset=[12,8]>
          <Avatar :src="userImg" icon="ios-person" size="large"></Avatar>
        </Badge>
        <DropdownMenu slot="list">
          <DropdownItem name="1" @click.native="toMessage">
            <Icon type="ios-mail" style="margin-right: 5px;"></Icon>
            查看消息
          </DropdownItem>
          <DropdownItem name="2" @click.native="toUser">
            <Icon type="ios-person" style="margin-right: 5px;"></Icon>
            个人中心
          </DropdownItem>
          <!-- 新增：问答历史菜单项 -->
          <DropdownItem name="4" @click.native="toQAHistory" v-if="displayornot">
            <Icon type="ios-chatbubbles" style="margin-right: 5px;"></Icon>
            问答历史
          </DropdownItem>
          <DropdownItem divided name="3">
            <Icon type="ios-log-out" style="margin-right: 5px;"></Icon>
            退出登录
          </DropdownItem>
        </DropdownMenu>

      </Dropdown>
    </Menu>
  </div>
</template>

<script>
import { resetTokenAndClearUser } from '../utils'
// 1. 引入工具函数
import { getAvatarPath, isValidAvatarName } from '@/utils/avatar'
import { getTip } from '@/api'
export default {
  name: "HeaderMenu",
  data() {
    return{
      displayornot: Number(sessionStorage.getItem('userId')) !== 100000,
      tip: 0,
      userImg:getAvatarPath(''),
    }
  },
  created(){
    this.userImg = sessionStorage.getItem('userImg')
    if (sessionStorage.getItem('userId') !== null)
      getTip(sessionStorage.getItem('userId')).then(res => {
        // console.log(res)
        this.tip = res.message
        // console.log('tip',this.tip)
      })
    this.loadUserAvatar();
  },
  props: {
    'activename' : Number,
  },
  methods:{
    loadUserAvatar(){
      const storedUserImg = sessionStorage.getItem('userImg');
      if (isValidAvatarName(storedUserImg)){
        this.userImg = getAvatarPath(storedUserImg);
      }else{
        this.userImg = getAvatarPath('');
      }
    },
    toUser() {
      this.$router.push('/user')
    },
    toMessage() {
      this.$router.push('/message')
    },
    // 新增：跳转到问答历史页面
    toQAHistory() {
      this.$router.push('/user/qa-history')
    },
    userOperate(name) {
      switch (name) {
        case '1':
          // 基本资料
          // this.gotoPage('user')
          break
        case '2':
          // 消息
          // this.gotoPage('message')
          break
        case '4':
          // 问答历史（已在 toQAHistory 中处理）
          break
        case '3':
          resetTokenAndClearUser()
          this.$router.push({ name: 'login' })
          this.$Message.info('退出成功！！')
          break
      }
    },
  }
}
</script>

<style scoped>

</style>
