<template>
  <div class="carousel-wrapper">
    <el-carousel ref="myCarousel" :interval="8000" height="420px" arrow="never" indicator-position="none">
      <el-carousel-item v-for="(item, index) in displayData" :key="'info2-'+index">
        <div class="split-panel">
          
          <div class="left-img" @click="toNewsDetail(item.newsid)">
            <img :src="item.pic_url" :onerror="defaultImg" alt="新闻封面">
          </div>
          
          <div class="right-panel">
            <div class="text-top" @click="toNewsDetail(item.newsid)">
              <h2 class="title">{{ item.title }}</h2>
              <div class="divider-line"></div>
              <p class="desc">{{ item.desc }}</p>
            </div>
            
            <div class="bottom-area">
              <div class="icon-group">
                <div class="circle-icon green"><Icon type="md-text" /></div>
                <div class="circle-icon red"><Icon type="md-share" /></div>
                <div class="circle-icon yellow"><Icon type="md-star" /></div>
                <div class="circle-icon blue"><Icon type="md-notifications" /></div>
              </div>
              
              <div class="nav-controller">
                <Icon type="ios-arrow-back" class="nav-arrow" @click.native="prevSlide" />
                <span class="page-text"><b>{{ index + 1 }}</b> / {{ displayData.length }}</span>
                <Icon type="ios-arrow-forward" class="nav-arrow" @click.native="nextSlide" />
              </div>
            </div>

          </div>
        </div>
      </el-carousel-item>
    </el-carousel>
  </div>
</template>

<script>
// 💡 新增：引入获取所有新闻的接口 getAllNewsDetail
import { getPicture, getAllNewsDetail } from '@/api'

export default {
  name: "HeaderPicture",
  data() {
    return {
      newsdetail: [], // 最终用来渲染轮播图的数据列表
    }
  },
  computed: {
    defaultImg () {
      return 'this.src="' + require('@/assets/imgs/404.jpg') + '"'
    },
    // 动态计算属性，负责剥离正文的 HTML 标签，生成摘要
    displayData() {
      return this.newsdetail.map(item => {
        let descText = item.mainpage || item.desc || '';
        // 剥离 HTML 标签，并截取前 120 个字符作为摘要
        descText = descText.replace(/<[^>]+>/g, '').slice(0, 120) + '...';
        if (descText === '...') {
          descText = '点击查看完整新闻报道，掌握最新全球资讯脉搏，深度解析社会热点话题...';
        }
        
        return {
          newsid: item.newsid || item.news_id,
          title: item.title || '无标题',
          pic_url: item.pic_url,
          desc: descText
        }
      });
    }
  },
  created() {
    this.fetchCarouselData();
  },
  methods: {
    // 💡 万能图片提取器：防止后端传来的 pic_url 格式乱七八糟
    extractPicUrl(picStr) {
      if (!picStr || picStr === '[]' || picStr === 'None') return null;
      try {
        let cleanStr = String(picStr).replace(/'/g, '"');
        let parsed = JSON.parse(cleanStr);
        return Array.isArray(parsed) ? parsed[0] : parsed;
      } catch (e) {
        let urls = String(picStr).match(/https?:\/\/[^'"\]\s]+/g);
        return urls ? urls[0] : picStr;
      }
    },
    // 主获取逻辑
    fetchCarouselData() {
      getPicture().then(res => {
        let rawData = res.message;
        let parsedData = [];
        if (typeof rawData === 'string') {
          try { 
            parsedData = JSON.parse(rawData); 
          } catch (e) {
            console.warn("数据解析异常，已启用兜底机制", e); // 💡 加上这行打印日志，ESLint 就不报错了
          }
        } else {
          parsedData = rawData || [];
        }

        if (parsedData.length > 0) {
          // 如果热点 API 有数据，直接清洗图片并使用
          this.newsdetail = parsedData.map(item => ({
            ...item,
            pic_url: this.extractPicUrl(item.pic_url)
          }));
        } else {
          // 💡 第一层兜底：热点没图，去全部新闻里随机抽！
          this.fetchFallbackNews();
        }
      }).catch(err => {
        console.log("热点图片获取失败，启动备用方案", err);
        this.fetchFallbackNews();
      })
    },
    // 💡 随机抽取带图新闻的兜底方案
    fetchFallbackNews() {
      getAllNewsDetail().then(res => {
        let allNews = res.newslist || [];
        let newsWithPics = [];

        // 筛选出所有带真实图片的新闻
        for (let i = 0; i < allNews.length; i++) {
          let item = allNews[i];
          let extractedPic = this.extractPicUrl(item.pic_url);
          if (extractedPic) {
            newsWithPics.push({
              newsid: item.news_id || item.newsid,
              title: item.title,
              pic_url: extractedPic,
              mainpage: item.mainpage || item.origin || ''
            });
          }
        }

        if (newsWithPics.length > 0) {
          // 打乱数组顺序 (Shuffle)
          newsWithPics.sort(() => 0.5 - Math.random());
          // 取前 5 条作为轮播图
          this.newsdetail = newsWithPics.slice(0, 5);
        } else {
          // 💡 终极兜底：如果整个数据库连一张图都找不出来，再用本地图片死扛
          this.newsdetail = [
            {
              newsid: 'fallback-1',
              title: '暂无带图新闻，请开启爬虫抓取',
              pic_url: require('@/assets/imgs/bg01.jpg'), 
              desc: '系统检测到当前数据库中没有包含图片的真实新闻。这通常是因为爬虫尚未抓取到带有图片的新闻数据，请检查爬虫状态。'
            }
          ];
        }
      }).catch(err => console.error("全部兜底方案失败", err));
    },
    toNewsDetail(newsid) {
      if (String(newsid).startsWith('fallback')) {
        this.$Message.info('此为演示数据，真实新闻请点击下方列表');
        return;
      }
      this.$router.push({path:'/newspage/'+newsid})
    },
    prevSlide() { this.$refs.myCarousel.prev(); },
    nextSlide() { this.$refs.myCarousel.next(); }
  }
}
</script>

<style scoped>
.carousel-wrapper {
  max-width: 1200px;
  margin: 20px auto;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  border-radius: 4px;
  overflow: hidden;
}
.split-panel {
  display: flex;
  width: 100%;
  height: 100%;
  background: #fff;
}
.left-img {
  flex: 0 0 68%;
  height: 100%;
  cursor: pointer;
  overflow: hidden;
}
.left-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}
.left-img:hover img {
  transform: scale(1.03);
}

.right-panel {
  flex: 0 0 32%;
  padding: 40px 30px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  background: #fff;
}
.text-top {
  cursor: pointer;
}
.title {
  font-size: 24px;
  font-weight: bold;
  color: #333;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.title:hover {
  color: #d32f2f;
}
.divider-line {
  width: 100%;
  height: 1px;
  background-color: #eee;
  margin: 20px 0;
}
.desc {
  font-size: 14px;
  color: #666;
  line-height: 1.8;
  display: -webkit-box;
  -webkit-line-clamp: 5;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-align: justify;
}

.bottom-area {
  margin-top: auto;
}
.icon-group {
  display: flex;
  gap: 15px;
  margin-bottom: 30px;
}
.circle-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.3s;
}
.circle-icon.green { border-color: #8bc34a; color: #8bc34a; }
.circle-icon.red { border-color: #e53935; color: #e53935; }
.circle-icon.yellow { border-color: #ffca28; color: #ffca28; }
.circle-icon.blue { border-color: #29b6f6; color: #29b6f6; }
.circle-icon:hover { transform: translateY(-3px); }

.nav-controller {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 10px;
}
.nav-arrow {
  font-size: 24px;
  color: #333;
  cursor: pointer;
  transition: color 0.3s;
}
.nav-arrow:hover {
  color: #d32f2f;
}
.page-text {
  font-size: 16px;
  color: #999;
}
.page-text b {
  font-size: 20px;
  color: #333;
}
</style>