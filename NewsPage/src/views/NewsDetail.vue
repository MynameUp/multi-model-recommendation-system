<template>
  <div class="mian-page">
    <HeaderMenu class="headmenu" :activename="7"></HeaderMenu>
    <div class="middle-page" style="background-color: #f6f8fa; padding-bottom: 40px;">
        <!-- 💡 增加一层外边距背景，让新闻主体像白纸一样浮出来 -->
        <Row :height="screenHeight">
          <Col :md="4"></Col>
          <Col :md="16">
            
            <div class="news-container">
              <!-- 1. 面包屑导航 -->
              <div class="breadcrumb" id="anchor1">
                <div class="red-block"></div>
                <span class="nav-text">
                  <router-link to="/" class="nav-link">新闻频道</router-link> 
                  &nbsp;>&nbsp; 
                  <router-link :to="'/domesticnews/' + category" class="nav-link">{{ sort }}</router-link>
                </span>
              </div>

              <!-- 2. 标题区 -->
              <h1 class="article-title">{{ title }}</h1>

              <!-- 3. Meta 信息栏 (来源、时间、阅读量) -->
              <div class="article-meta">
                <span>来源：新闻综合网络</span>
                <span class="divider">|</span>
                <span>{{ date ? date.replace('T', ' ') : '' }}</span>
                <span class="divider">|</span>
                <span>阅读：{{ readnum }}</span>
                <span class="divider">|</span>
                <a @click="toComments" class="comment-link">参与评论：{{ comments }}</a>
              </div>

              <!-- 4. 视频播放区 (如果有) -->
              <div style="margin: 30px auto; text-align: center;" v-if="videoshow">
                <video-player class="video-player vjs-custom-skin"
                              ref="videoPlayer"
                              :playsinline="true"
                              :options="playerOptions"
                              style="max-width: 800px; margin: 0 auto; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                </video-player>
              </div>

              <!-- 5. 正文与图片区 -->
              <div class="article-body">
                <!-- 图片优先居中展示 -->
                <div v-if="pic_url && pic_url.length > 0" class="image-wrapper">
                  <div v-for="(item,index) in pic_url" :key="'pic-'+index" style="margin-bottom: 20px;">
                    <img class="article-img" :src="item" alt :onerror="defaultImg">
                  </div>
                </div>
                
                <!-- HTML 正文渲染 -->
                <div class="html-content" v-html="origin"></div>
              </div>

              <!-- 6. 互动区 (移到文章末尾) -->
              <div class="article-actions">
                <div class="action-box">
                  <span class="action-label">感兴趣</span>
                  <Rate @on-change="upGivelike(1)" v-model="value" :count="1" icon="ios-thumbs-up" :clearable="true" class="rate-icon"/>
                </div>
                <div class="action-box">
                  <span class="action-label">不感兴趣</span>
                  <Rate @on-change="upGivelike(0)" v-model="value1" :count="1" icon="ios-thumbs-down" :clearable="true" class="rate-icon"/>
                </div>
                <!-- 新增：智能问答按钮 -->
                <div class="action-box qa-action-box">
                  <NewsQA
                    v-if="newsid"
                    :news-id="parseInt(newsid)"
                    :current-news="newsInfo"
                  />
                </div>
              </div>
            </div>

            <!-- 下方推荐阅读与评论区保持卡片化设计 -->
            <Divider class="section-divider">为你推荐</Divider>

            <Row :gutter="20" v-if="recsimilarlist.length !== 0">
              <Col :lg="12">
                <Carousel radius-dot dots="outside" autoplay :autoplay-speed="9000" v-model="Carouselvalue1" loop>
                  <CarouselItem v-for="(item, index) in recsimilarlist" :key="'recsim-'+index">
                    <Card v-if="!item.pic_url" class="rec-card" @click.native="toNewsDetail(item.newsid)">
                      <p slot="title" class="rec-title">{{item.title}}</p>
                      <p class="rec-desc" v-html="item.mainpage"></p>
                    </Card>
                    <div v-else class="pic_item" @click="toNewsDetail(item.newsid)">
                      <img :src="item.pic_url" class="images">
                      <div class="img-mask"><h2>{{ item.title.slice(0,20) }}</h2></div>
                    </div>
                  </CarouselItem>
                </Carousel>
              </Col>
              <Col :lg="12">
                <Carousel radius-dot dots="outside" loop autoplay :autoplay-speed="10000" v-model="Carouselvalue2">
                  <CarouselItem v-for="(item, index) in rechotlist" :key="'rechot-'+index">
                    <Card v-if="!item.pic_url" class="rec-card" @click.native="toNewsDetail(item.newsid)">
                      <p slot="title" class="rec-title">{{item.title}}</p>
                      <p class="rec-desc" v-html="item.mainpage"></p>
                    </Card>
                    <div v-else class="pic_item" @click="toNewsDetail(item.newsid)">
                      <img style="object-fit: cover;" :src="item.pic_url" class="images">
                      <div class="img-mask"><h2>{{ item.title.slice(0,20) }}</h2></div>
                    </div>
                  </CarouselItem>
                </Carousel>
              </Col>
            </Row>

            <!-- 评论输入区 -->
            <Row style="margin-top: 30px;">
              <Col :lg="24">
                <Card :bordered="false" shadow>
                  <h3 slot="title" style="font-size: 18px; color: #333;">发表评论</h3>
                  <Row>
                    <Input show-word-limit maxlength="500" v-model="comment" type="textarea" :autosize="{minRows: 4,maxRows: 10}" placeholder="理性发言，友善互动..."/>
                  </Row>
                  <Row style="margin-top: 15px; text-align: right;">
                    <Button size="large" type="primary" @click="submitComment" style="width: 120px;">发表</Button>
                  </Row>
                </Card>
              </Col>
            </Row>

            <!-- 评论列表区 -->
            <Row style="margin-top: 20px; margin-bottom: 50px;">
              <Col span="24">
                <Card id="comments" :bordered="false" shadow>
                  <h3 slot="title" style="font-size: 18px; color: #333;">最新评论 ({{ commentlists.length }})</h3>
                  <div v-if="commentlists.length === 0" class="empty-comment">
                    <Icon type="ios-chatbubbles-outline" size="40" color="#ccc"/>
                    <p>暂无评论，快来抢沙发吧！</p>
                  </div>
                  <div v-for="(item,index) in commentlists" :key="'comm-'+index" class="comment-item">
                    <div class="comment-header">
                      <Avatar icon="ios-person" :src="item.userheadPortrait" size="large"/>
                      <span class="comment-user">{{ item.username }}</span>
                      <span class="comment-time">{{ item.time ? item.time.replace('T', ' ') : '' }}</span>
                    </div>
                    <div class="comment-body">
                      <span v-if="item.tousername" class="reply-target">@{{ item.tousername }} </span>
                      <span class="comment-text">{{ item.comments }}</span>
                    </div>
                    <div v-if="Number(item.userid) !== Number(userid)" :id="'com'+item.userid" class="reply-section">
                      <Collapse simple class="custom-collapse">
                        <Panel name="1">
                          <span style="color: #666; font-size: 13px;">回复</span>
                          <div slot="content" class="reply-input-area">
                            <Input v-model="toUserComment" type="textarea" show-word-limit maxlength="500" :autosize="{minRows: 2,maxRows: 5}" placeholder="回复Ta..."></Input>
                            <div style="text-align: right; margin-top: 10px;">
                              <Button size="small" type="primary" @click="submitCommenttoUser(item.userid)">发送回复</Button>
                            </div>
                          </div>
                        </Panel>
                      </Collapse>
                    </div>
                    <Divider v-if="index !== commentlists.length - 1" dashed />
                  </div>
                </Card>
              </Col>
            </Row>

          </Col>
          <Col :md="4"></Col>
        </Row>
    </div>
    <el-backtop target=".headmenu"></el-backtop>
  </div>
</template>

<script>
import HeaderMenu from "../components/HeaderMenu";
import NewsQA from '@/components/NewsQA.vue';  // 新增导入问答组件
import { getNewsDetail, updateHistory, getSimilarnews, getHotNews, getComments, updateGiveLike, submitComments, submitCommentsToUser } from '@/api'
import { videoPlayer } from 'vue-video-player'

export default {
  name: "NewsDetail",
  components: {
    HeaderMenu,
    videoPlayer,
    NewsQA  // 新增注册组件
  },
  computed: {
    defaultImg() {
      return 'this.src="' + require('@/assets/imgs/404.jpg') + '"'
    },
    // 新增：计算属性，构建新闻信息对象
    newsInfo() {
      return {
        title: this.title || '',
        origin: '新闻综合网络',
        date: this.date || ''
      }
    }
  },
  created() {
    this.openFullScreen()
    this.fetchData()
    this.userid = sessionStorage.getItem('userId')
  },
  data()  {
    return {
      fullscreenLoading: false,
      videoshow: false,
      isShowLoading: true,
      userid: '',
      toUserComment: '',
      commentlists:[],
      recsimilarlist: [],
      rechotlist: [],
      sort: '',
      newsdetail: '',
      newsid: '',
      title: '',
      readnum: '',
      comments: '',
      category: '',
      origin: '',
      videourl: '',
      date: '',
      pic_url: [],
      Carouselvalue1: 1,
      Carouselvalue2: 2,
      comment: '',
      value: 0,
      value1: 0,
      screenHeight: document.documentElement.clientHeight - 70,
      screenWidth: document.documentElement.clientWidth,
      playerOptions: {
        playbackRates: [0.7, 1.0, 1.5, 2.0],
        autoplay: false,
        muted: false,
        loop: false,
        preload: 'auto',
        language: 'zh-CN',
        aspectRatio: '16:9', // 改为现在主流的 16:9 比例
        fluid: true,
        sources: [{ type: "", src: "" }],
        poster: "",
        notSupportedMessage: '此视频暂无法播放，请稍后再试',
        controlBar: {
          timeDivider: true,
          durationDisplay: true,
          remainingTimeDisplay: false,
          fullscreenToggle: true,
        }
      }
    }
  },
  watch: {
    screenHeight(val) {
      if (!this.timer) {
        this.screenHeight = val
        this.timer = true
        let that = this
        setTimeout(function () {
          that.timer = false
        }, 400)
      }
    },
    '$route':'fetchData'
  },
  methods: {
    extractImages(strData) {
      if (!strData || strData === '[]' || strData === 'None') return [];
      let urls = String(strData).match(/https?:\/\/[^'"\]\s]+/g);
      return urls || [];
    },
    cleanHtmlString(strData) {
      if (!strData) return '<p>暂无正文</p>';
      let clean = String(strData);
      if (clean.startsWith('[')) clean = clean.substring(1);
      if (clean.endsWith(']')) clean = clean.substring(0, clean.length - 1);
      clean = clean.replace(/^['"]/, '').replace(/['"]$/, '');
      clean = clean.replace(/>\s*,\s*</g, '><');
      clean = clean.replace(/',\s*'/g, '');
      return clean;
    },
    openFullScreen() {
      const loading = this.$loading({
        lock: true, text: '加载中...', spinner: 'el-icon-loading', background: 'rgba(255,255,255,0.8)'
      });
      setTimeout(() => loading.close(), 800);
    },
    submitComment() {
      if(!this.comment.trim()){
        this.$Message.warning('评论内容不能为空');
        return;
      }
      submitComments(sessionStorage.getItem('userId'), this.newsid, this.comment).then(() => {
        this.$Message.success('评论成功');
        this.$router.go(0);
      })
    },
    submitCommenttoUser(touserid) {
      if(!this.toUserComment.trim()){
        this.$Message.warning('回复内容不能为空');
        return;
      }
      submitCommentsToUser(sessionStorage.getItem('userId'), this.newsid, this.toUserComment, touserid).then(() => {
        this.$Message.success('回复成功');
        this.$router.go(0);
      })
    },
    upGivelike(type){
      if (type === 1){
        if (this.value === 0){
          this.value = 0
          updateGiveLike(sessionStorage.getItem('userId'), this.newsid, 0)
        } else {
          if (this.value1 === 1) this.value1 = 0
          this.value = 1
          updateGiveLike(sessionStorage.getItem('userId'), this.newsid, 1)
        }
      }else {
        if (this.value1 === 1){
          this.value = 0
          updateGiveLike(sessionStorage.getItem('userId'), this.newsid, 2)
        }else {
          if(this.value === 1) this.value = 0
          this.value1 = 1
          updateGiveLike(sessionStorage.getItem('userId'), this.newsid, 0)
        }
      }
    },
    toNewsDetail(newsid) {
      this.$router.push('/newspage/'+newsid)
    },
    toComments() {
      document.querySelector('#comments').scrollIntoView({behavior: "smooth", block: "center", inline: "nearest"})
    },
    fetchData(){
      this.isShowLoading = true
      Object.assign(this.$data, this.$options.data())
      this.userid = sessionStorage.getItem('userId')
      this.newsid = this.$route.params.id

      getNewsDetail(this.newsid, this.userid).then(res => {
        let msg = res.message;
        this.newsid = msg.newsid;
        this.date = msg.date;
        this.pic_url = this.extractImages(msg.pic_url);

        let vUrl = String(msg.videourl);
        if (vUrl && vUrl !== 'None' && vUrl !== '[]' && vUrl !== 'null') {
          this.playerOptions.sources[0].src = vUrl;
          this.videoshow = true;
        } else {
          this.videoshow = false;
        }

        this.comments = msg.comments || 0;
        this.newsdetail = msg;
        this.category = msg.category;
        this.title = msg.title;
        this.readnum = msg.readnum || 0;

        if(msg.givelike === 1) this.value = 1;
        if(msg.givelike === 2) this.value1 = 1;

        this.origin = this.cleanHtmlString(msg.origin || msg.mainpage);

        const categoryMap = ['美股', '国内', '国际', '社会', '体育', '娱乐', '军事', '科技', '财经', '股市', '全部'];
        this.sort = categoryMap[this.category] || '其他';

        this.$nextTick(() => {
            const anchor = document.querySelector('#anchor1');
            if (anchor) anchor.scrollIntoView({behavior: "smooth", block: "center", inline: "nearest"});
        });

        setTimeout(() => { this.isShowLoading = false }, 1000);
      }).catch(err => console.error("详情获取失败:", err));

      updateHistory(sessionStorage.getItem('userId'), this.newsid)

      getSimilarnews(this.newsid).then(res => {
        let list = res.newslist || [];
        this.recsimilarlist = list.map(news => ({
          newsid: news.newsid,
          title: news.title || '无标题',
          pic_url: this.extractImages(news.pic_url)[0] || '',
          mainpage: this.cleanHtmlString(news.mainpage).replace(/<[^>]+>/g, '').slice(0, 50) + '...'
        }));
      })

      getHotNews().then(res => {
        let list = res.newslist || [];
        this.rechotlist = list.map(news => ({
          newsid: news.newsid,
          title: news.title || '无标题',
          pic_url: this.extractImages(news.pic_url)[0] || '',
          mainpage: this.cleanHtmlString(news.mainpage).replace(/<[^>]+>/g, '').slice(0, 50) + '...'
        }));
      })

      getComments(this.newsid).then(res => {
        this.commentlists = res.commentlist || [];
      })
      this.$Loading.finish()
    },
  },
}
</script>

<style scoped>
/* ====== 核心：新闻主容器（模拟白纸排版） ====== */
.news-container {
  background-color: #ffffff;
  padding: 40px 60px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
  margin-top: 20px;
}

/* ====== 1. 面包屑导航 ====== */
.breadcrumb {
  display: flex;
  align-items: center;
  margin-bottom: 25px;
}
.red-block {
  width: 4px;
  height: 16px;
  background-color: #e10000;
  margin-right: 8px;
}
.nav-text {
  font-size: 14px;
  color: #666;
}

/* ====== 2. 标题区 ====== */
.article-title {
  font-size: 34px;
  font-weight: bold;
  color: #1a1a1a;
  line-height: 1.4;
  margin-bottom: 20px;
  text-align: left;
}

/* ====== 3. Meta 信息栏 ====== */
.article-meta {
  display: flex;
  align-items: center;
  font-size: 13px;
  color: #999;
  margin-bottom: 40px;
}
.divider {
  margin: 0 12px;
  color: #ddd;
}
.comment-link {
  color: #999;
  cursor: pointer;
  transition: color 0.3s;
}
.comment-link:hover {
  color: #e10000;
}

/* ====== 4. 正文与图片 ====== */
.article-body {
  margin-bottom: 50px;
}
.image-wrapper {
  text-align: center;
}
.article-img {
  max-width: 100%;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
/* 穿透修改 v-html 内部标签的样式 */
.html-content >>> p {
  font-size: 18px;
  line-height: 2;
  color: #333;
  margin-bottom: 20px;
  text-indent: 2em;
  text-align: justify;
}
.html-content >>> img {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 20px auto;
}

/* ====== 5. 底部点赞/踩互动区 ====== */
.article-actions {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 40px;
  padding-top: 30px;
  border-top: 1px dashed #eee;
}
.action-box {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.action-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 5px;
}
.rate-icon {
  font-size: 30px;
}

/* 新增：问答按钮样式优化 */
.qa-action-box {
  min-width: 120px;
}

/* ====== 其他组件美化 ====== */
.section-divider {
  font-size: 20px;
  font-weight: bold;
  color: #333;
  margin: 40px 0 20px 0;
}
.rec-card {
  height: 280px;
  cursor: pointer;
  border: none;
  background: #fff;
  transition: transform 0.3s;
}
.rec-card:hover {
  transform: translateY(-5px);
}
.rec-title {
  font-size: 18px;
  font-weight: bold;
}
.rec-desc {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  margin-top: 10px;
}
.pic_item {
  position: relative;
  width: 100%;
  height: 280px;
  cursor: pointer;
  border-radius: 8px;
  overflow: hidden;
}
.images {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.img-mask {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0,0,0,0.8));
  padding: 20px 15px 15px;
}
.img-mask h2 {
  color: #fff;
  font-size: 18px;
  margin: 0;
}

/* 评论区细化 */
.empty-comment {
  text-align: center;
  padding: 40px 0;
  color: #999;
}
.comment-item {
  padding: 15px 0;
}
.comment-header {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}
.comment-user {
  font-weight: bold;
  color: #333;
  margin-left: 10px;
  font-size: 15px;
}
.comment-time {
  margin-left: auto;
  color: #999;
  font-size: 13px;
}
.comment-body {
  padding-left: 50px;
  font-size: 15px;
  line-height: 1.6;
  color: #333;
}
.reply-target {
  color: #409eff;
  font-weight: bold;
}
.reply-section {
  padding-left: 50px;
  margin-top: 10px;
}
.custom-collapse {
  border: none;
  background-color: #f8f8f9;
  border-radius: 4px;
}
.custom-collapse >>> .ivu-collapse-header {
  border: none;
  height: 32px;
  line-height: 32px;
}
.custom-collapse >>> .ivu-collapse-content {
  background-color: transparent;
}
.nav-link {
  color: #666;
  text-decoration: none;
  transition: color 0.3s;
}
.nav-link:hover {
  color: #e10000;
}
.nav-link {
  color: #666;
  text-decoration: none;
  transition: color 0.3s;
}
.nav-link:hover {
  color: #e10000; /* 鼠标悬停变红 */
  text-decoration: underline;
}
</style>
