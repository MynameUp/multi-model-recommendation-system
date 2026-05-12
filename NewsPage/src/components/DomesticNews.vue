<template>
  <Row style="background:url('https://www.hualigs.cn/image/60821cdb3c769.jpg');background-attachment: fixed;">
    <Col span="4"></Col>
    <Col span="12" style="height: auto; padding: 10px">
      <Card :bordered="false" class="newsitem" v-for="(item, index) in newslist.slice(0, a)" :key="'news'+index"
            :to="'/newspage/'+ item.newsid" style="border-radius: 12px;">
        <p slot="title" style="font-weight: 700;font-size: larger;">{{ item.title }}</p>
        
        <Row :lg="24" v-if="item.pic_url">
          <Col :lg="9" style="text-align: center">
            <img class="images" style="width: 200px; border-radius: 4px;" alt :onerror="defaultImg" :src="item.pic_url">
          </Col>
          <Col :lg="1"></Col>
          <Col :lg="14" style="color: #181818; font-size: 14px; line-height: 1.6;">
            {{ item.mainpage }}
          </Col>
        </Row>
        
        <Row :lg="24" v-else>
          <Col :lg="1"></Col>
          <Col :lg="22"><p style="color: #181818; font-size: 14px; line-height: 1.6;">{{ item.mainpage }}</p></Col>
          <Col :lg="1"></Col>
        </Row>
        
        <Row style="margin-top: 15px; color: #a8a8a8">
          <Col :lg="1"></Col>
          <Col :lg="5">
            <Icon size="20" type="ios-people"/> {{ item.readnum }} &nbsp;&nbsp;
            <Icon size="18" type="ios-megaphone-outline"/> {{ item.comments }}
          </Col>
          <Col :lg="11"></Col>
          <Col :lg="6" style="text-align: right;">
            <div>{{ item.date }}</div>
          </Col>
        </Row>
      </Card>
      
      <div align="center">
        <div class="load-more mr-bottom" v-if="a < newslist.length" @click='loadMore'
             style="text-align: center;margin-top: 20px;cursor: pointer;" v-show="spinShow">点击加载更多
        </div>
        <div class="load-more" v-else style="text-align: center;margin-top: 20px;cursor: pointer;" v-show="spinShow">没有更多了</div>
      </div>
    </Col>
    <UserHistory></UserHistory>
  </Row>
</template>

<script>
import { getTypeNewsDetail } from '@/api'
import UserHistory from "./UserHistory";

export default {
  name: "DomesticNews",
  components: { UserHistory },
  computed: {
    defaultImg () {
      return 'this.src="' + require('@/assets/imgs/404.jpg') + '"'
    }
  },
  data() {
    return {
      spinShow: false,
      a: 6,
      newslist: [],
    }
  },
  methods: {
    loadMore() {
      this.a += 6;
    }
  },
  created() {
    this.$Loading.start()
    // 获取当前路由中的分类 ID
    let categoryId = this.$route.params.id;
    
    getTypeNewsDetail(categoryId).then(res => {
      // 💡 彻底抛弃 eval()，直接读取后端传来的原生数组
      let rawList = res.newslist || [];
      
      this.newslist = rawList.map(item => {
        // 1. 安全解析图片
        let parsedPicUrl = null;
        if (item.pic_url && item.pic_url !== '[]') {
          try {
            let cleanStr = item.pic_url.replace(/'/g, '"');
            let urlArray = JSON.parse(cleanStr);
            parsedPicUrl = Array.isArray(urlArray) ? urlArray[0] : urlArray;
          } catch (e) {
            parsedPicUrl = item.pic_url;
          }
        }

        // 2. 剥离正文 HTML 标签生成纯文本简介
        let content = item.mainpage || item.origin || '';
        let safeMainpage = content.replace(/<[^>]+>/g, '') || '暂无内容简介...';
        if (safeMainpage.length > 100) {
          safeMainpage = safeMainpage.slice(0, 100) + '...';
        }

        // 3. 返回清洗好的标准数据结构
        return {
          newsid: item.news_id,         // 对齐后端的新字段名
          title: item.title || '无标题',
          pic_url: parsedPicUrl,
          mainpage: safeMainpage,
          date: item.date || '刚刚',
          readnum: item.readnum || 0,
          comments: item.comments || 0,
        }
      });
      
      this.spinShow = true;
    }).catch(err => {
      console.error("分类新闻加载失败:", err);
    }).finally(() => {
      this.$Loading.finish(); // 确保一定能关闭顶部加载条
    });
  },
}
</script>

<style scoped>
.images{
  width: 120px;
  height: 85px;
  object-fit: cover;
}
.load-more{
  width: 200px;
  border-radius: 50px;
  background: linear-gradient(45deg, #c2e7e8, #a3c2c3);
  font-weight: bold;
  font-size: 19px;
  padding: 8px 0;
}
.load-more:hover{
  background: linear-gradient(45deg, #a3c2c3, #c2e7e8);
}
.newsitem {
  margin-top: 10px;
}
</style>