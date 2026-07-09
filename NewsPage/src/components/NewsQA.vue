<template>
  <div class="news-qa-container">
    <!-- 问答对话框触发按钮 -->
    <el-button 
      type="primary" 
      icon="el-icon-chat-dot-round" 
      @click="showQADialog = true"
      class="qa-trigger-btn"
    >
      智能问答
    </el-button>

    <!-- 问答对话框 -->
    <el-dialog
      title="新闻智能问答"
      :visible.sync="showQADialog"
      width="70%"
      :close-on-click-modal="false"
      custom-class="qa-dialog"
    >
      <div class="qa-content">
        <!-- 当前新闻信息 -->
        <div class="current-news-info">
          <h4>当前新闻</h4>
          <p class="news-title">{{ currentNews.title }}</p>
          <p class="news-meta">
            <span>来源: {{ currentNews.origin }}</span>
            <span>时间: {{ currentNews.date }}</span>
          </p>
        </div>

        <!-- 问答历史区域 -->
        <div class="qa-history" ref="qaHistory">
          <div v-if="qaList.length === 0" class="empty-tip">
            <i class="el-icon-chat-line-round"></i>
            <p>您可以问我关于这篇新闻的任何问题</p>
            <div class="quick-questions">
              <el-tag 
                v-for="(q, index) in quickQuestions" 
                :key="index"
                size="small"
                @click="askQuickQuestion(q)"
                class="quick-question-tag"
              >
                {{ q }}
              </el-tag>
            </div>
          </div>

          <div v-for="(item, index) in qaList" :key="index" class="qa-item">
            <!-- 用户问题 -->
            <div class="question-item">
              <div class="avatar user-avatar">
                <i class="el-icon-user"></i>
              </div>
              <div class="question-bubble">
                {{ item.question }}
              </div>
            </div>

            <!-- AI回答 -->
            <div class="answer-item">
              <div class="avatar ai-avatar">
                <i class="el-icon-service"></i>
              </div>
              <div class="answer-bubble">
                <div v-if="item.loading" class="loading-answer">
                  <i class="el-icon-loading"></i> 思考中...
                </div>
                <div v-else class="answer-content">
                  {{ item.answer }}
                </div>
                
                <!-- 相关新闻 -->
                <div v-if="item.relatedNews && item.relatedNews.length > 0" class="related-news">
                  <p class="related-title">📰 相关新闻：</p>
                  <div 
                    v-for="(news, idx) in item.relatedNews" 
                    :key="idx"
                    class="related-news-item"
                    @click="viewRelatedNews(news)"
                  >
                    <span class="news-similarity">相似度: {{ (news.similarity * 100).toFixed(0) }}%</span>
                    <span class="news-title-text">{{ news.title }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="qa-input-area">
          <el-input
            v-model="currentQuestion"
            type="textarea"
            :rows="3"
            placeholder="请输入您关于这篇新闻的问题..."
            @keyup.enter.native="handleEnterKey"
            :disabled="isAsking"
          ></el-input>
          <div class="input-actions">
            <el-select v-model="selectedLLM" size="small" style="width: 150px; margin-right: 10px;">
              <el-option label="快速模式" value="fallback"></el-option>
              <el-option label="智能模式" value="dashscope"></el-option>
            </el-select>
            <el-button 
              type="primary" 
              @click="submitQuestion"
              :loading="isAsking"
              :disabled="!currentQuestion.trim()"
            >
              {{ isAsking ? '思考中...' : '发送' }}
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'NewsQA',
  props: {
    // 当前新闻ID
    newsId: {
      type: Number,
      required: true
    },
    // 当前新闻信息
    currentNews: {
      type: Object,
      default: () => ({
        title: '',
        origin: '',
        date: ''
      })
    }
  },
  data() {
    return {
      showQADialog: false,
      currentQuestion: '',
      isAsking: false,
      qaList: [],
      selectedLLM: 'fallback', // fallback 或 dashscope
      quickQuestions: [
        '这篇新闻讲了什么？',
        '关键人物有哪些？',
        '事件的背景是什么？',
        '这条新闻为什么重要？',
        '有类似新闻吗？'
      ]
    }
  },
  methods: {
    /**
     * 提交问题
     */
    async submitQuestion() {
      if (!this.currentQuestion.trim() || this.isAsking) {
        return
      }

      const question = this.currentQuestion.trim()
      this.currentQuestion = ''

      // 添加问题到列表
      this.qaList.push({
        question: question,
        answer: '',
        relatedNews: [],
        loading: true
      })

      this.isAsking = true

      // 滚动到底部
      this.$nextTick(() => {
        this.scrollToBottom()
      })

      try {
        // 调用后端API
        // 前端请求: /api/agent/news-qa/
        // 代理重写: /agent/news-qa/
        // 后端匹配: agent/news-qa/ ✅
        const response = await axios.post('/api/agent/news-qa/', {
          userId: this.getUserId(),
          newsId: this.newsId,
          question: question,
          llmType: this.selectedLLM
        })

        if (response.data.status === '200') {
          // 更新最后一条问答的答案
          const lastQA = this.qaList[this.qaList.length - 1]
          lastQA.answer = response.data.data.answer
          lastQA.relatedNews = response.data.data.relatedNews || []
          lastQA.loading = false

          this.$message.success('回答完成')
        } else {
          throw new Error(response.data.message || '回答失败')
        }
      } catch (error) {
        console.error('[News QA] 问答失败:', error)
        const lastQA = this.qaList[this.qaList.length - 1]
        lastQA.answer = '抱歉，回答失败：' + (error.message || '网络错误')
        lastQA.loading = false

        this.$message.error('问答失败，请重试')
      } finally {
        this.isAsking = false

        // 滚动到底部
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      }

    },

    /**
     * 快速提问
     */
    askQuickQuestion(question) {
      this.currentQuestion = question
      this.submitQuestion()
    },

    /**
     * 查看相关新闻
     */
    viewRelatedNews(news) {
      // 关闭对话框
      this.showQADialog = false

      // 跳转到相关新闻页面
      this.$router.push({
        path: '/news-detail',
        query: {id: news.id}
      })

      this.$message.info(`正在查看: ${news.title}`)
    },

    /**
     * 处理回车键
     */
    handleEnterKey(event) {
      // 如果按住Shift+Enter，允许换行
      if (!event.shiftKey) {
        event.preventDefault()
        this.submitQuestion()
      }
    },

    /**
     * 滚动到对话底部
     */
    scrollToBottom() {
      const container = this.$refs.qaHistory
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    },

    /**
     * 获取用户ID
     */
    getUserId() {
      // 从sessionStorage获取用户ID（与登录时存储的位置一致）
      const userId = sessionStorage.getItem('userId')
      if (userId) {
        const parsed = parseInt(userId)
        if (!isNaN(parsed)) return parsed  // 防止 'kcsciso' 等非数字污染
      }

      // 兼容旧版本：尝试从localStorage获取user对象
      try {
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        if (user.userid || user.id) {
          const parsed = parseInt(user.userid || user.id)
          if (!isNaN(parsed)) return parsed
        }
      } catch (e) {
        console.warn('[News QA] 解析用户信息失败:', e)
      }

      // 兜底: 游客ID
      return 100000
    }
  }
}
</script>
<style scoped>
.news-qa-container {
  display: inline-block;
}
.qa-trigger-btn {
  margin-left: 10px;
  padding-top: 10px;
}
.qa-dialog ::v-deep .el-dialog__body {
  padding: 20px;
  height: 600px;
}
.qa-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.current-news-info {
  padding-bottom: 15px;
  border-bottom: 2px solid #409EFF;
  margin-bottom: 15px;
}
.current-news-info h4 {
  margin: 0 0 10px 0;
  color: #409EFF;
}
.news-title {
  font-size: 16px;
  font-weight: bold;
  margin: 5px 0;
  color: #303133;
}
.news-meta {
  font-size: 12px;
  color: #909399;
}
.news-meta span {
  margin-right: 20px;
}
.qa-history {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 15px;
}
.empty-tip {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
}
.empty-tip i {
  font-size: 48px;
  margin-bottom: 10px;
}
.quick-questions {
  margin-top: 20px;
}
.quick-question-tag {
  margin: 5px;
  cursor: pointer;
  transition: all 0.3s;
}
.quick-question-tag:hover {
  background-color: #409EFF;
  color: white;
}
.qa-item {
  margin-bottom: 20px;
}
.question-item,
.answer-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 10px;
}
.question-item {
  flex-direction: row-reverse;
}
.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}
.user-avatar {
  background-color: #409EFF;
  color: white;
  margin-left: 10px;
}
.ai-avatar {
  background-color: #67C23A;
  color: white;
  margin-right: 10px;
}
.question-bubble,
.answer-bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 8px;
  line-height: 1.6;
  word-wrap: break-word;
}
.question-bubble {
  background-color: #409EFF;
  color: white;
}
.answer-bubble {
  background-color: white;
  color: #303133;
  border: 1px solid #DCDFE6;
}
.loading-answer {
  color: #909399;
  font-style: italic;
}
.answer-content {
  white-space: pre-wrap;
}
.related-news {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px dashed #DCDFE6;
}
.related-title {
  font-weight: bold;
  margin-bottom: 10px;
  color: #606266;
}
.related-news-item {
  padding: 8px;
  margin: 5px 0;
  background-color: #f5f7fa;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 13px;
}
.related-news-item:hover {
  background-color: #ecf5ff;
  transform: translateX(5px);
}
.news-similarity {
  display: inline-block;
  background-color: #E6A23C;
  color: white;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
  margin-right: 8px;
}
.news-title-text {
  color: #409EFF;
}
.qa-input-area {
  border-top: 1px solid #DCDFE6;
  padding-top: 15px;
}
.input-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-top: 10px;
}
</style>
