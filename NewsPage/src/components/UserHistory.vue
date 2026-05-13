<template>
  <Col span="5" >
    <div class="bjdiv">
      <h3 style="margin-top: 20px; margin-left: 50px; font-size: 20px;">浏览记录</h3>
      <Timeline v-if="historylist.length > 0" style="margin-top: 20px; margin-left: 30px;cursor: pointer;color: #181818">
        <TimelineItem v-for="(item, index) in historylist.slice(0, 10)" :key="'his-'+index" @click.native="toNewsPage(item.newsid)">
          <p class="time" style="font-size:18px; font-weight: bold">{{ item.title }}</p>
          <p class="content" style="color: #666; margin-top: 5px;">{{ item.time }}</p>
        </TimelineItem>
      </Timeline>
      <div v-else style="margin: 30px 0; text-align: center; color: #ccc;">
        暂无浏览记录...
      </div>
    </div>
  </Col>
</template>

<script>
import { getUserHistory } from '@/api'

export default {
  name: "UserHistory",
  data() {
    return {
      historylist: [],
    }
  },
  created() {
    let userId = sessionStorage.getItem('userId');
    if (userId) {
      getUserHistory(userId).then(res => {
        let listObj = res.newslist || {};
        this.historylist = [];

        // 💡 真相大白：后端的 key 就是新闻标题，value 才是详情
        for (let titleKey in listObj) {
          let item = listObj[titleKey];
          this.historylist.push({
            // 把键（titleKey）直接作为标题展示
            title: titleKey.length > 13 ? titleKey.slice(0, 13) + '...' : titleKey,
            newsid: item.newsid || item.id,
            time: item.time ? item.time.replace('T', ' ') : '刚刚'
          });
        }

        // 选做：如果你希望最新的历史记录在最上面，可以加上这一行翻转数组
        this.historylist.reverse();

      }).catch(err => console.error('历史记录加载失败', err));
    }
  },
  methods: {
    toNewsPage(newsid) {
      this.$router.push('/newspage/' + newsid);
      setTimeout(() => { this.$router.go(0); }, 100); // 优化 3：确保点击侧边栏历史记录时，页面能强制刷新加载新数据
    }
  }
}
</script>

<style scoped>
.bjdiv {
  background: transparent;
  color: #fff;
  background-color: rgba(28,49,78,0.25);
  border-radius: 20px;
  padding-bottom: 20px; /* 增加一点底部边距更美观 */
}
/* 删除了无用的 banner_bg 样式 */
</style>