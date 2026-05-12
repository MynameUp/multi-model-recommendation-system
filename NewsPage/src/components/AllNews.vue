<template>
  <Row style="background:url('https://www.hualigs.cn/image/60821cdb3c769.jpg');background-attachment: fixed;">
    <Col span="4"></Col>
    <Col span="12" style="height: auto; padding: 10px">
      <Card :bordered="false" class="newsitem" v-for="(item, index) in newslist.slice(0, a)" :key="'news'+index" :to="'/newspage/'+ item.newsid" style="border-radius: 12px;">
        <p slot="title" style="font-weight: 700;font-size: larger;">{{ item.title }}</p>
        
        <Row :lg="24" v-if="item.pic_url">
          <Col :lg="9" style="text-align: center">
              <img class="images" style="width: 200px;" :src="item.pic_url">
          </Col>
          <Col :lg="1"></Col>
          <Col :lg="14" style="color: #181818">
            {{ item.mainpage }}
          </Col>
        </Row>
        
        <Row :lg="24" v-else>
          <Col :lg="1"></Col>
          <Col :lg="22"><p style="color: #181818">{{ item.mainpage }}</p></Col>
          <Col :lg="1"></Col>
        </Row>
        
        <Row style="margin-top: 10px; color: #a8a8a8">
          <Col :lg="1"></Col>
          <Col :lg="5"><Icon size="20" type="ios-people" />{{ item.readnum }} &nbsp;&nbsp; <Icon size="18" type="ios-megaphone-outline" />{{ item.comments }}</Col>
          <Col :lg="11"></Col>
          <Col :lg="6" style="text-align: right;">
            <div>{{ item.date }}</div>
          </Col>
        </Row>
      </Card>

      <div align="center">
        <div class="load-more mr-bottom" v-if="a < newslist.length" @click='loadMore'
             style="text-align: center;margin-top: 20px;cursor: pointer;">点击加载更多
        </div>
        <div class="load-more" v-else style="text-align: center;margin-top: 20px;cursor: pointer;">没有更多了</div>
      </div>
    </Col>
    <UserHistory></UserHistory>
  </Row>
</template>

<script>
import { getAllNewsDetail } from '@/api'
import UserHistory from "./UserHistory";

export default {
  name: "AllNews",
  components: { UserHistory },
  data() {
    return {
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
    getAllNewsDetail().then(res => {
      let rawList = res.newslist || []; 
      
      this.newslist = rawList.map(item => {
        // 安全处理图片解析
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

        // 💡 核心修改：融合 mainpage 和 origin，并剥离所有的 HTML 标签
        let content = item.mainpage || item.origin || '';
        let safeMainpage = content.replace(/<[^>]+>/g, '') || '暂无内容简介...';
        
        if (safeMainpage.length > 100) {
          safeMainpage = safeMainpage.slice(0, 100) + '...';
        }

        return {
          newsid: item.news_id,
          title: item.title || '无标题',
          pic_url: parsedPicUrl,
          mainpage: safeMainpage,
          date: item.date || '刚刚',
          readnum: item.readnum || 0,
          comments: item.comments || 0,
        }
      });
    }).catch(err => {
      console.error("加载新闻列表失败:", err);
    });
  }
}
</script>

<style scoped>
.images {
  width: 100px;
  height: 80px;
  object-fit: cover;
}
.load-more {
  width: 200px;
  border-radius: 50px;
  background: linear-gradient(45deg, #c2e7e8, #a3c2c3);
  font-weight: bold;
  font-size: 19px;
  padding: 10px 0; /* 加一点内边距让按钮更好看 */
}
.load-more:hover {
  background: linear-gradient(45deg, #a3c2c3, #c2e7e8);
}
.newsitem {
  margin-top: 10px;
}
</style>