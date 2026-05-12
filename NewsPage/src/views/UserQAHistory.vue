<template>
  <div class="user-qa-history">
    <el-card class="box-card">
      <div slot="header" class="clearfix">
        <span>我的问答历史</span>
        <el-button style="float: right; padding: 3px 0" type="text" @click="loadHistory">
          <i class="el-icon-refresh"></i> 刷新
        </el-button>
      </div>

      <!-- 统计信息 -->
      <div class="stats-section" v-if="stats">
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="stat-item">
              <div class="stat-value">{{ stats.total_questions }}</div>
              <div class="stat-label">总问答数</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-item">
              <div class="stat-value">{{ stats.recent_7days_questions }}</div>
              <div class="stat-label">最近7天</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-item">
              <div class="stat-value">{{ stats.unique_news_asked }}</div>
              <div class="stat-label">询问新闻数</div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 问答历史列表 -->
      <div class="history-list">
        <el-timeline v-if="historyList.length > 0">
          <el-timeline-item
            v-for="(item, index) in historyList"
            :key="index"
            :timestamp="item.time"
            placement="top"
          >
            <el-card class="qa-card">
              <div class="qa-header">
                <el-tag size="small" type="info">新闻ID: {{ item.news_id }}</el-tag>
                <el-button 
                  size="mini" 
                  type="primary" 
                  @click="viewNews(item.news_id)"
                >
                  查看新闻
                </el-button>
              </div>
              
              <div class="qa-content">
                <div class="question-section">
                  <span class="label">问：</span>
                  <span class="text">{{ item.question }}</span>
                </div>
                
                <div class="answer-section">
                  <span class="label">答：</span>
                  <span class="text">{{ item.answer }}</span>
                </div>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>

        <el-empty v-else description="暂无问答历史"></el-empty>
      </div>

      <!-- 分页 -->
      <div class="pagination-section" v-if="historyList.length > 0">
        <el-pagination
          @current-change="handlePageChange"
          :current-page="currentPage"
          :page-size="pageSize"
          layout="total, prev, pager, next"
          :total="totalCount"
        >
        </el-pagination>
      </div>
    </el-card>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'UserQAHistory',
  data() {
    return {
      historyList: [],
      stats: null,
      currentPage: 1,
      pageSize: 20,
      totalCount: 0
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
      try {
        const userId = this.getUserId()
        
        // 获取问答历史
        const historyResponse = await axios.get('/api/agent/user-qa-history/', {
          params: {
            userId: userId,
            limit: this.pageSize
          }
        })
        
        if (historyResponse.data.status === '200') {
          this.historyList = historyResponse.data.data.history || []
          this.stats = historyResponse.data.data.stats
          this.totalCount = this.stats.total_questions || 0
        }
      } catch (error) {
        console.error('加载问答历史失败:', error)
        this.$message.error('加载失败')
      }
    },

    /**
     * 查看新闻
     */
    viewNews(newsId) {
      this.$router.push({
        path: '/news-detail',
        query: { id: newsId }
      })
    },

    /**
     * 页码改变
     */
    handlePageChange(page) {
      this.currentPage = page
      this.loadHistory()
    },

    /**
     * 获取用户ID
     */
    getUserId() {
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      return user.userid || 1
    }
  }
}
</script>

<style scoped>
.user-qa-history {
  padding: 20px;
}

.stats-section {
  margin-bottom: 30px;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 10px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.history-list {
  min-height: 300px;
}

.qa-card {
  margin-bottom: 10px;
}

.qa-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.qa-content {
  line-height: 1.8;
}

.question-section,
.answer-section {
  margin-bottom: 10px;
}

.label {
  font-weight: bold;
  color: #606266;
  margin-right: 5px;
}

.text {
  color: #303133;
}

.question-section .text {
  color: #409EFF;
}

.pagination-section {
  margin-top: 20px;
  text-align: center;
}
</style>
