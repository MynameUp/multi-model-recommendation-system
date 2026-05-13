<template>
  <div class="user-qa-history">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2 class="page-title">
        <Icon type="ios-chatboxes" />
        我的问答历史
      </h2>
      <div class="header-actions">
        <Button type="primary" size="small" @click="loadHistory" :loading="loading">
          <Icon type="ios-refresh" />
          刷新
        </Button>
        <Button type="text" size="small" @click="goBack">
          <Icon type="ios-arrow-back" />
          返回
        </Button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-section" v-if="stats && !loading">
      <Row :gutter="16">
        <Col :xs="24" :sm="8">
          <Card class="stat-card stat-total">
            <div class="stat-content">
              <div class="stat-icon">
                <Icon type="ios-chatbubbles" size="32" />
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.total_questions }}</div>
                <div class="stat-label">总问答数</div>
              </div>
            </div>
          </Card>
        </Col>
        <Col :xs="24" :sm="8">
          <Card class="stat-card stat-recent">
            <div class="stat-content">
              <div class="stat-icon">
                <Icon type="ios-time" size="32" />
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ historyList.length }}</div>
                <div class="stat-label">已加载记录</div>
              </div>
            </div>
          </Card>
        </Col>
        <Col :xs="24" :sm="8">
          <Card class="stat-card stat-news">
            <div class="stat-content">
              <div class="stat-icon">
                <Icon type="ios-newspaper" size="32" />
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ uniqueNewsCount }}</div>
                <div class="stat-label">询问新闻数</div>
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>

    <!-- 搜索和筛选 -->
    <div class="filter-section">
      <Input
        v-model="searchKeyword"
        placeholder="搜索问答内容..."
        clearable
        @on-change="handleSearch"
        class="search-input"
      >
        <Icon type="ios-search" slot="prefix" />
      </Input>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <Spin size="large">
        <Icon type="ios-loading" size="18" class="demo-spin-icon-load"></Icon>
        <div>加载中...</div>
      </Spin>
    </div>

    <!-- 错误状态 -->
    <Alert
      v-else-if="error"
      type="error"
      show-icon
      class="error-alert"
    >
      {{ error }}
      <template slot="desc">
        <Button type="text" size="small" @click="loadHistory">点击重试</Button>
      </template>
    </Alert>

    <!-- 空状态 -->
    <div v-else-if="filteredHistory.length === 0" class="empty-state">
      <Icon type="ios-chatbubbles-outline" size="64" class="empty-icon" />
      <p class="empty-text">暂无问答历史</p>
      <p class="empty-hint">快去新闻详情页提问吧~</p>
      <Button type="primary" @click="$router.push('/')" class="go-browse-btn">
        浏览新闻
      </Button>
    </div>

    <!-- 问答历史列表 -->
    <div v-else class="history-list">
      <Card
        v-for="(item, index) in paginatedHistory"
        :key="'qa-' + index"
        class="qa-card"
      >
        <div class="qa-header">
          <div class="qa-meta">
            <Tag color="blue">
              <Icon type="ios-document" />
              新闻ID: {{ item.news_id }}
            </Tag>
            <Tag color="default">
              <Icon type="ios-time" />
              {{ item.time }}
            </Tag>
          </div>
          <div class="qa-actions">
            <Button
              size="small"
              type="primary"
              @click="viewNews(item.news_id)"
            >
              <Icon type="ios-open" />
              查看新闻
            </Button>
          </div>
        </div>

        <div class="qa-body">
          <!-- 问题部分 -->
          <div class="qa-item qa-question">
            <div class="qa-label">
              <Icon type="ios-help-circle" />
              问
            </div>
            <div class="qa-text">{{ item.question }}</div>
          </div>

          <!-- 回答部分 -->
          <div class="qa-item qa-answer">
            <div class="qa-label">
              <Icon type="ios-checkmark-circle" />
              答
            </div>
            <div class="qa-text">{{ item.answer }}</div>
          </div>
        </div>
      </Card>

      <!-- 分页 -->
      <div class="pagination-wrapper" v-if="filteredHistory.length > pageSize">
        <Page
          :total="filteredHistory.length"
          :page-size="pageSize"
          :current="currentPage"
          @on-change="handlePageChange"
          show-total
          show-elevator
        />
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'UserQAHistory',
  data() {
    return {
      historyList: [],
      filteredHistory: [],
      stats: null,
      loading: true,
      error: null,
      currentPage: 1,
      pageSize: 10,
      searchKeyword: ''
    }
  },
  computed: {
    // 分页后的历史记录
    paginatedHistory() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      return this.filteredHistory.slice(start, end)
    },
    // 唯一新闻数量
    uniqueNewsCount() {
      const newsIds = new Set(this.historyList.map(item => item.news_id))
      return newsIds.size
    }
  },
  mounted() {
    this.loadHistory()
  },
  methods: {
    /**
     * 加载问答历史
     */
    async loadHistory() {
      this.loading = true
      this.error = null

      try {
        const userId = this.getUserId()

        if (!userId) {
          this.error = '用户未登录'
          this.$Message && this.$Message.warning('请先登录')
          this.loading = false
          return
        }

        console.group('[QA History] 开始加载问答历史')
        console.log('用户ID:', userId)
        console.log('请求URL:', '/api/agent/user-qa-history/')
        console.log('请求参数:', { userId: userId, limit: 100 })

        // 获取问答历史
        const historyResponse = await axios.get('/api/agent/user-qa-history/', {
          params: {
            userId: userId,
            limit: 100
          }
        })

        console.log('API响应状态:', historyResponse.data.status)
        console.log('API响应数据:', historyResponse.data.data)

        if (historyResponse.data.status === '200') {
          const responseData = historyResponse.data.data

          // 检查数据结构
          if (responseData && typeof responseData === 'object' && !Array.isArray(responseData)) {
            // 新格式：{ history: [], stats: {} }
            this.historyList = responseData.history || []
            this.stats = responseData.stats || null

            console.log('使用新格式数据结构')
          } else if (Array.isArray(responseData)) {
            // 旧格式：直接是数组 []
            this.historyList = responseData
            this.stats = {
              total_questions: this.historyList.length,
              recent_7days_questions: this.getRecent7DaysCount(),
              unique_news_asked: this.uniqueNewsCount
            }

            console.log('使用旧格式数据结构（兼容）')
          } else {
            // 异常情况
            this.historyList = []
            this.stats = null
            console.warn('未知的数据结构:', responseData)
          }

          console.log('加载的历史记录数:', this.historyList.length)
          console.log('统计数据:', this.stats)

          if (this.historyList.length === 0) {
            console.warn('警告: 数据库中没有该用户的问答记录')
            console.log('提示: 请先在新闻详情页进行提问')
          }

          // 初始化筛选列表
          this.filteredHistory = [...this.historyList]
        } else {
          this.error = historyResponse.data.message || '数据加载失败'
          console.error('API返回错误状态:', historyResponse.data)
        }
      } catch (error) {
        console.error('[QA History] 加载问答历史失败:', error)
        console.error('错误详情:', error.response || error.message)
        this.error = '网络错误，请检查连接后重试'
        this.$Message && this.$Message.error('加载问答历史失败')
      } finally {
        this.loading = false
        console.groupEnd()
      }
    },



    /**
     * 获取最近7天的问答数量
     */
    getRecent7DaysCount() {
      const sevenDaysAgo = new Date()
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)

      return this.historyList.filter(item => {
        try {
          const itemDate = new Date(item.time)
          return itemDate >= sevenDaysAgo
        } catch (e) {
          return false
        }
      }).length
    },

    /**
     * 搜索处理
     */
    handleSearch() {
      if (!this.searchKeyword.trim()) {
        this.filteredHistory = [...this.historyList]
      } else {
        const keyword = this.searchKeyword.toLowerCase()
        this.filteredHistory = this.historyList.filter(item =>
          item.question.toLowerCase().includes(keyword) ||
          item.answer.toLowerCase().includes(keyword)
        )
      }
      this.currentPage = 1
    },

    /**
     * 查看新闻
     */
    viewNews(newsId) {
      if (!newsId) {
        this.$Message.warning('新闻ID无效')
        return
      }

      // 跳转到新闻详情页
      this.$router.push({
        path: `/newspage/${newsId}`
      }).catch(err => {
        console.error('路由跳转失败:', err)
        this.$Message.error('页面跳转失败')
      })
    },

    /**
     * 页码改变
     */
    handlePageChange(page) {
      this.currentPage = page
      // 滚动到顶部
      window.scrollTo({ top: 0, behavior: 'smooth' })
    },

    /**
     * 返回上一页
     */
    goBack() {
      this.$router.go(-1)
    },

    /**
     * 获取用户ID
     */
    getUserId() {
      try {
        // 尝试从多个位置获取用户ID
        const userStr = localStorage.getItem('user') ||
                       sessionStorage.getItem('user') ||
                       localStorage.getItem('userId') ||
                       sessionStorage.getItem('userId')

        if (userStr) {
          // 如果是数字字符串，直接返回
          if (!isNaN(userStr)) {
            return parseInt(userStr)
          }

          // 如果是JSON对象，解析后返回userid
          const user = JSON.parse(userStr)
          return user.userid || user.id || 1
        }
      } catch (e) {
        console.error('解析用户信息失败:', e)
      }
      return 1
    }
  }
}
</script>

<style scoped>
/* 页面容器 */
.user-qa-history {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f0f0f0;
}

.page-title {
  margin: 0;
  font-size: 24px;
  color: #17233d;
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

/* 统计卡片区域 */
.stats-section {
  margin-bottom: 24px;
}

.stat-card {
  margin-bottom: 16px;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stat-total .stat-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-recent .stat-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-news .stat-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #17233d;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #808695;
}

/* 搜索筛选区域 */
.filter-section {
  margin-bottom: 24px;
}

.search-input {
  max-width: 400px;
}

/* 加载状态 */
.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.demo-spin-icon-load {
  animation: ani-demo-spin 1s linear infinite;
}

@keyframes ani-demo-spin {
  from { transform: rotate(0deg); }
  50% { transform: rotate(180deg); }
  to { transform: rotate(360deg); }
}

/* 错误提示 */
.error-alert {
  margin-bottom: 24px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: #f8f8f9;
  border-radius: 8px;
}

.empty-icon {
  color: #c5c8ce;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 18px;
  color: #515a6e;
  margin-bottom: 8px;
}

.empty-hint {
  font-size: 14px;
  color: #808695;
  margin-bottom: 24px;
}

.go-browse-btn {
  margin-top: 16px;
}

/* 问答历史列表 */
.history-list {
  margin-top: 24px;
}

.qa-card {
  margin-bottom: 16px;
  transition: all 0.3s ease;
}

.qa-card:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.qa-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e8eaec;
}

.qa-meta {
  display: flex;
  gap: 8px;
  align-items: center;
}

.qa-actions {
  display: flex;
  gap: 8px;
}

.qa-body {
  line-height: 1.8;
}

.qa-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px;
  border-radius: 6px;
}

.qa-question {
  background: rgba(45, 140, 240, 0.05);
  border-left: 3px solid #2d8cf0;
}

.qa-answer {
  background: rgba(87, 173, 81, 0.05);
  border-left: 3px solid #57ad51;
}

.qa-label {
  font-weight: bold;
  color: #515a6e;
  min-width: 40px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.qa-question .qa-label {
  color: #2d8cf0;
}

.qa-answer .qa-label {
  color: #57ad51;
}

.qa-text {
  flex: 1;
  color: #17233d;
  word-wrap: break-word;
  white-space: pre-wrap;
}

/* 分页 */
.pagination-wrapper {
  margin-top: 24px;
  text-align: center;
  padding: 16px 0;
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .user-qa-history {
    padding: 12px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .page-title {
    font-size: 20px;
  }

  .stat-content {
    flex-direction: column;
    text-align: center;
  }

  .qa-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .qa-actions {
    width: 100%;
  }

  .qa-actions .ivu-btn {
    flex: 1;
  }
}

/* 动画效果 */
.qa-card {
  animation: fadeInUp 0.5s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
