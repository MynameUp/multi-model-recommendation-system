<template>
  <div class="intelligent-recommend-container">
    <HeaderMenu activename="4"></HeaderMenu>

    <!-- 智能对话区域 -->
    <div class="chat-section">
      <div class="chat-header">
        <h2>🤖 智能推荐助手</h2>
        <p class="subtitle">告诉我你想看什么，我来为你推荐</p>
      </div>

      <!-- 对话历史 -->
      <div class="chat-history" ref="chatHistory">
        <div v-for="(msg, index) in chatMessages" :key="index"
             :class="['message', msg.type === 'user' ? 'user-message' : 'bot-message']">
          <div class="message-avatar">
            {{ msg.type === 'user' ? '👤' : '🤖' }}
          </div>
          <div class="message-content">
            <div class="message-text">{{ msg.text }}</div>
            <div v-if="msg.suggestions" class="message-suggestions">
              <el-tag
                v-for="(tag, idx) in msg.suggestions"
                :key="idx"
                size="small"
                effect="plain"
                @click="useSuggestion(tag)"
                style="cursor: pointer; margin: 2px;">
                {{ tag }}
              </el-tag>
            </div>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-if="isLoading" class="message bot-message">
          <div class="message-avatar">🤖</div>
          <div class="message-content">
            <div class="loading-dots">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-section">
        <el-input
          v-model="userInput"
          placeholder="例如：给我推荐今天的科技新闻 / 我想看和人工智能有关的国内新闻..."
          @keyup.enter.native="sendRequest"
          :disabled="isLoading"
          clearable
          size="large">
          <el-button
            slot="append"
            icon="el-icon-s-promotion"
            @click="sendRequest"
            :loading="isLoading"
            type="primary">
            发送
          </el-button>
        </el-input>

        <!-- 快捷建议按钮 -->
        <div class="quick-actions">
          <el-button size="small" @click="useSuggestion('给我推荐今天的科技新闻')">
            📱 今日科技
          </el-button>
          <el-button size="small" @click="useSuggestion('我想看和人工智能有关的国内新闻')">
            🤖 AI资讯
          </el-button>
          <el-button size="small" @click="useSuggestion('不要娱乐新闻，多推荐财经和国际新闻')">
            💰 财经国际
          </el-button>
          <el-button size="small" @click="useSuggestion('根据我最近看的内容推荐一些深度文章')">
            📚 深度阅读
          </el-button>
          <el-button size="small" @click="useSuggestion('换一批，但不要和刚才太相似')">
            🔄 换一批
          </el-button>
        </div>
      </div>
    </div>

    <!-- 推荐结果区域 -->
    <div v-if="recommendations.length > 0" class="results-section">
      <div class="results-header">
        <h3>📋 推荐结果 ({{ recommendations.length }}条)</h3>
        <div class="sort-options">
          <el-radio-group v-model="sortBy" size="small" @change="sortResults">
            <el-radio-button label="score">综合评分</el-radio-button>
            <el-radio-button label="freshness">最新发布</el-radio-button>
            <el-radio-button label="heat">最热</el-radio-button>
          </el-radio-group>
        </div>
      </div>

      <Row :gutter="16">
        <Col
          v-for="(item, index) in displayRecommendations"
          :key="item.newsid"
          :xs="24" :sm="12" :md="8" :lg="6">
          <Card
            :bordered="false"
            class="news-card"
            @click.native="openNewsDetail(item.newsid)">
            <div slot="title" class="card-title">{{ item.title }}</div>

            <div class="card-image" v-if="item.pic_url">
              <img :src="getFirstImageUrl(item.pic_url)" alt="新闻图片">
            </div>

            <div class="card-content">
              <p class="summary">{{ truncateText(item.mainpage, 100) }}</p>

              <!-- 推荐理由 -->
              <div class="recommend-reason">
                <Icon type="ios-lightbulb-outline" size="16" />
                <span>{{ item.reason }}</span>
              </div>

              <!-- 评分详情 -->
              <div class="score-details">
                <div class="score-header" @click="toggleScoreDetail(index)">
                  <span class="score-badge">
                    综合评分: {{ (item.recommend_score * 100).toFixed(0) }}
                  </span>
                  <Icon
                    :type="item.showDetail ? 'ios-arrow-up' : 'ios-arrow-down'"
                    size="14" />
                </div>

                <div v-if="item.showDetail" class="score-breakdown">
                  <div class="score-item">
                    <span class="label">相似度:</span>
                    <Progress
                      :percent="item.score_breakdown.similarity * 100"
                      :stroke-width="4"
                      status="success" />
                  </div>
                  <div class="score-item">
                    <span class="label">热度:</span>
                    <Progress
                      :percent="item.score_breakdown.heat * 100"
                      :stroke-width="4"
                      status="normal" />
                  </div>
                  <div class="score-item">
                    <span class="label">新鲜度:</span>
                    <Progress
                      :percent="item.score_breakdown.freshness * 100"
                      :stroke-width="4"
                      status="warning" />
                  </div>
                  <div class="score-item">
                    <span class="label">兴趣匹配:</span>
                    <Progress
                      :percent="item.score_breakdown.user_interest * 100"
                      :stroke-width="4"
                      status="success" />
                  </div>
                  <div class="score-item">
                    <span class="label">内容质量:</span>
                    <Progress
                      :percent="item.score_breakdown.quality * 100"
                      :stroke-width="4" />
                  </div>
                </div>
              </div>

              <!-- 底部信息 -->
              <div class="card-footer">
                <span class="meta">
                  <Icon type="ios-eye-outline" /> {{ item.readnum }}
                </span>
                <span class="meta">
                  <Icon type="ios-chatboxes-outline" /> {{ item.comments }}
                </span>
                <span class="date">{{ formatDate(item.date) }}</span>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      <!-- 加载更多 -->
      <div class="load-more" v-if="hasMoreResults">
        <el-button @click="loadMore" :loading="loadingMore" type="default">
          加载更多
        </el-button>
      </div>
    </div>
  </div>
</template>

<script>
import HeaderMenu from "../components/HeaderMenu";
import axios from 'axios';

export default {
  name: "IntelligentRecommend",
  components: { HeaderMenu },
  data() {
    return {
      userInput: '',
      isLoading: false,
      loadingMore: false,
      chatMessages: [
        {
          type: 'bot',
          text: '你好！我是智能推荐助手。请告诉我你想看什么类型的新闻？',
          suggestions: [
            '给我推荐今天的科技新闻',
            '我想看和人工智能有关的国内新闻',
            '不要娱乐新闻，多推荐财经和国际新闻'
          ]
        }
      ],
      recommendations: [],
      displayCount: 8,
      sortBy: 'score',
      currentIntent: null
    };
  },
  computed: {
    displayRecommendations() {
      return this.recommendations.slice(0, this.displayCount);
    },
    hasMoreResults() {
      return this.displayCount < this.recommendations.length;
    }
  },
  methods: {
    async sendRequest() {
      if (!this.userInput.trim() || this.isLoading) return;

      const input = this.userInput.trim();
      this.userInput = '';

      // 添加用户消息
      this.chatMessages.push({
        type: 'user',
        text: input
      });

      this.isLoading = true;

      // 滚动到底部
      this.$nextTick(() => {
        this.scrollToBottom();
      });

      try {
        const userId = sessionStorage.getItem('userId');
        if (!userId) {
          this.$Message.warning('请先登录');
          this.$router.push('/login');
          return;
        }

        // 调用智能推荐API
        const response = await axios.get('/api/intelligent/recommend/', {
          params: {
            user_input: input,
            userid: userId,
            top_n: 20
          }
        });

        this.isLoading = false;

        if (response.data.status === '200') {
          const data = response.data.data;

          // 添加机器人回复
          this.chatMessages.push({
            type: 'bot',
            text: `我为你找到了 ${data.total} 条相关新闻，以下是综合评分最高的推荐：`,
            suggestions: this.getFollowUpSuggestions(input)
          });

          // 保存推荐结果
          this.recommendations = data.recommendations.map(item => ({
            ...item,
            showDetail: false
          }));

          this.currentIntent = input;

          // 滚动到底部
          this.$nextTick(() => {
            this.scrollToBottom();
          });

          this.$Message.success(`成功获取 ${data.total} 条推荐`);
        } else {
          this.$Message.error(response.data.message || '推荐失败');
        }
      } catch (error) {
        this.isLoading = false;
        console.error('智能推荐错误:', error);
        this.$Message.error('请求失败，请稍后重试');

        this.chatMessages.push({
          type: 'bot',
          text: '抱歉，我遇到了一些问题。请稍后再试。'
        });
      }
    },

    useSuggestion(text) {
      this.userInput = text;
      this.sendRequest();
    },

    getFollowUpSuggestions(currentInput) {
      // 根据当前输入生成后续建议
      const suggestions = [];

      if (currentInput.includes('科技') || currentInput.includes('AI')) {
        suggestions.push('推荐更多人工智能相关内容');
        suggestions.push('我想看科技创业相关的新闻');
      }

      if (currentInput.includes('财经')) {
        suggestions.push('推荐股票市场最新动态');
        suggestions.push('我想看投资理财相关文章');
      }

      suggestions.push('换一批推荐');
      suggestions.push('根据我的历史推荐');

      return suggestions;
    },

    toggleScoreDetail(index) {
      this.recommendations[index].showDetail = !this.recommendations[index].showDetail;
    },

    sortResults() {
      switch (this.sortBy) {
        case 'score':
          this.recommendations.sort((a, b) => b.recommend_score - a.recommend_score);
          break;
        case 'freshness':
          this.recommendations.sort((a, b) => new Date(b.date) - new Date(a.date));
          break;
        case 'heat':
          this.recommendations.sort((a, b) => b.readnum - a.readnum);
          break;
      }
    },

    loadMore() {
      this.loadingMore = true;
      setTimeout(() => {
        this.displayCount += 8;
        this.loadingMore = false;
      }, 500);
    },

    openNewsDetail(newsid) {
      // 更新阅读历史
      const userId = sessionStorage.getItem('userId');
      if (userId) {
        axios.get('/api/news/his/', {
          params: {
            userid: userId,
            newsid: newsid
          }
        });
      }

      this.$router.push(`/newspage/${newsid}`);
    },

    getFirstImageUrl(picUrlStr) {
      if (!picUrlStr) return '';
      try {
        const urls = eval(picUrlStr);
        return Array.isArray(urls) && urls.length > 0 ? urls[0] : '';
      } catch {
        return picUrlStr;
      }
    },

    truncateText(text, maxLength) {
      if (!text) return '';
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    },

    formatDate(dateStr) {
      if (!dateStr) return '';
      try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('zh-CN');
      } catch {
        return dateStr;
      }
    },

    scrollToBottom() {
      const container = this.$refs.chatHistory;
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    }
  },
  mounted() {
    // 初始化排序
    this.sortResults();
  }
};
</script>

<style scoped>
.intelligent-recommend-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding-bottom: 50px;
}

/* 聊天区域样式 */
.chat-section {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
}

.chat-header {
  text-align: center;
  color: white;
  margin-bottom: 30px;
}

.chat-header h2 {
  font-size: 28px;
  margin-bottom: 10px;
}

.subtitle {
  font-size: 14px;
  opacity: 0.9;
}

.chat-history {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 20px;
  max-height: 400px;
  overflow-y: auto;
  margin-bottom: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.message {
  display: flex;
  margin-bottom: 20px;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-message {
  flex-direction: row-reverse;
}

.user-message .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  margin-right: 10px;
}

.bot-message .message-content {
  background: #f0f0f0;
  color: #333;
  margin-left: 10px;
}

.message-avatar {
  font-size: 32px;
  flex-shrink: 0;
}

.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 16px;
  position: relative;
}

.message-text {
  line-height: 1.6;
  margin-bottom: 8px;
}

.message-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

/* 加载动画 */
.loading-dots {
  display: flex;
  gap: 5px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #667eea;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

/* 输入区域 */
.input-section {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.quick-actions {
  margin-top: 15px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.quick-actions .el-button {
  border-radius: 20px;
}

/* 推荐结果区域 */
.results-section {
  max-width: 1200px;
  margin: 30px auto;
  padding: 0 20px;
}

.results-header {
  background: white;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.results-header h3 {
  margin: 0;
  color: #333;
}

.news-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 12px;
  height: 100%;
}

.news-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
}

.card-title {
  font-weight: bold;
  font-size: 16px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-image {
  width: 100%;
  height: 150px;
  overflow: hidden;
  border-radius: 8px;
  margin-bottom: 12px;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.news-card:hover .card-image img {
  transform: scale(1.05);
}

.card-content {
  padding: 10px 0;
}

.summary {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  margin-bottom: 12px;
  height: 60px;
  overflow: hidden;
}

.recommend-reason {
  background: linear-gradient(135deg, #fff9e6 0%, #fff3cd 100%);
  padding: 8px 12px;
  border-radius: 8px;
  margin-bottom: 12px;
  font-size: 12px;
  color: #856404;
  border-left: 3px solid #ffc107;
}

.recommend-reason i {
  margin-right: 5px;
}

.score-details {
  margin-bottom: 12px;
}

.score-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 6px;
  transition: background 0.2s;
}

.score-header:hover {
  background: #e9ecef;
}

.score-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
}

.score-breakdown {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  margin-top: 8px;
}

.score-item {
  margin-bottom: 8px;
}

.score-item:last-child {
  margin-bottom: 0;
}

.score-item .label {
  font-size: 12px;
  color: #666;
  display: block;
  margin-bottom: 4px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid #eee;
  font-size: 12px;
  color: #999;
}

.meta {
  display: flex;
  align-items: center;
  gap: 4px;
}

.date {
  font-style: italic;
}

.load-more {
  text-align: center;
  margin-top: 30px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-header h2 {
    font-size: 22px;
  }

  .message-content {
    max-width: 85%;
  }

  .results-header {
    flex-direction: column;
    gap: 10px;
  }
}
</style>
