<template>
  <div class="intelligent-recommend-container">
    <HeaderMenu activename="4"></HeaderMenu>

    <!-- 智能对话区域 -->
    <div class="chat-section">
      <div class="chat-header">
        <div class="header-left">
          <h2>🤖 智能推荐助手</h2>
          <p class="subtitle">Powered by DeepSeek · 多轮对话 · 上下文记忆</p>
        </div>
        <div class="header-right">
          <Button
            type="error"
            size="small"
            ghost
            icon="md-trash"
            @click="clearMemory"
            :loading="isClearing"
            class="clear-btn">
            清空记忆
          </Button>
        </div>
      </div>

      <!-- 对话历史 -->
      <div class="chat-history" ref="chatHistory">
        <!-- 欢迎消息 -->
        <div v-if="chatMessages.length === 1 && !isLoading" class="welcome-tip">
          <Icon type="ios-chatbubbles" size="40" color="#ccc"/>
          <p>向我描述你想看的内容，我会结合你的兴趣为你精准推荐</p>
        </div>

        <div v-for="(msg, index) in chatMessages" :key="index"
             :class="['message', msg.type === 'user' ? 'user-message' : 'bot-message']">
          <div class="message-avatar">
            {{ msg.type === 'user' ? '👤' : '🤖' }}
          </div>
          <div class="message-content">
            <!-- 纯文本 -->
            <div class="message-text" v-if="msg.text">{{ msg.text }}</div>

            <!-- LLM 自然语言解释 (流式打字机效果) -->
            <div v-if="msg.explanation || msg._streaming || msg.text" class="llm-explanation">
              <Icon type="ios-bulb" size="16" />
              <span>
                {{ msg.text || msg.explanation }}
                <span v-if="msg._streaming" class="typing-cursor">|</span>
              </span>
            </div>

            <!-- 流水线追踪 (可折叠) -->
            <div v-if="msg.pipelineTrace" class="pipeline-trace">
              <span class="trace-label">🔍 流水线:</span>
              <Tag v-for="(val, key) in msg.pipelineTrace" :key="key"
                   color="success"
                   size="small">{{ key }}:{{ val }}</Tag>
            </div>

            <!-- 内嵌推荐新闻列表 -->
            <div v-if="msg.newsCards && msg.newsCards.length > 0" class="inline-news-cards">
              <div class="cards-title">
                <Icon type="ios-paper" size="16" />
                <span>为你推荐 ({{ msg.newsCards.length }} 条)</span>
              </div>
              <div
                v-for="(card, ci) in msg.newsCards"
                :key="'nc-'+ci"
                class="inline-news-item"
                @click="openNewsDetail(card.newsid)">
                <div class="inline-news-rank">{{ ci + 1 }}</div>
                <div class="inline-news-body">
                  <div class="inline-news-title">{{ card.title }}</div>
                  <div class="inline-news-meta">
                    <Tag size="small" color="blue">{{ card.category_name }}</Tag>
                    <span class="meta-score">⭐ {{ (card.recommend_score * 100).toFixed(0) }}分</span>
                    <span class="meta-read">{{ card.readnum }} 阅读</span>
                  </div>
                  <div class="inline-news-reason" v-if="card.reason">
                    <Icon type="ios-lightbulb-outline" size="12" /> {{ card.reason }}
                  </div>
                </div>
              </div>
              <!-- 在聊天窗口中展开全部卡片 -->
              <div v-if="msg.totalCount > 5" class="show-all-link" @click.stop="showAllResults()">
                <Icon type="ios-arrow-down" /> 查看全部 {{ msg.totalCount }} 条推荐
              </div>
            </div>

            <!-- 快捷建议 -->
            <div v-if="msg.suggestions && msg.suggestions.length > 0" class="message-suggestions">
              <Tag
                v-for="(tag, idx) in msg.suggestions"
                :key="idx"
                size="small"
                color="primary"
                @click.native="useSuggestion(tag)"
                style="cursor: pointer; margin: 2px;">
                {{ tag }}
              </Tag>
            </div>

            <!-- 时间戳 -->
            <div class="message-time">{{ msg.time }}</div>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-if="isLoading" class="message bot-message">
          <div class="message-avatar">🤖</div>
          <div class="message-content">
            <div class="loading-dots">
              <span></span><span></span><span></span>
            </div>
            <div class="loading-text">⏳ 流水线运行中: Intent → Recall → Rank → Explain</div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-section">
        <div class="input-row">
          <Input
            v-model="userInput"
            placeholder="描述你想看的内容，如：推荐人工智能相关的深度科技新闻..."
            @on-enter="sendRequest"
            :disabled="isLoading"
            clearable
            size="large"
            class="main-input">
            <Button
              slot="append"
              type="primary"
              @click="sendRequest"
              :loading="isLoading"
              icon="md-send">
              发送
            </Button>
          </Input>
        </div>

        <!-- 快捷建议按钮 -->
        <div class="quick-actions">
          <Button size="small" @click="useSuggestion('给我推荐今天的科技新闻')" ghost type="primary">
            📱 今日科技
          </Button>
          <Button size="small" @click="useSuggestion('我想看和人工智能有关的国内深度文章')" ghost type="primary">
            🤖 AI深度
          </Button>
          <Button size="small" @click="useSuggestion('推荐财经和国际新闻，不要娱乐')" ghost type="primary">
            💰 财经国际
          </Button>
          <Button size="small" @click="useSuggestion('根据我最近的阅读历史推荐一些深度长文')" ghost type="primary">
            📚 历史推荐
          </Button>
          <Button size="small" @click="useSuggestion('换一批推荐，但不要和刚才太相似')" ghost type="primary">
            🔄 换一批
          </Button>
        </div>
      </div>
    </div>

    <!-- 完整推荐结果展示区域 (点击"查看全部"后展示) -->
    <div v-if="showFullResults && fullRecommendations.length > 0" class="results-section">
      <div class="results-header">
        <h3>📋 全部推荐结果 ({{ fullRecommendations.length }}条)</h3>
        <Button size="small" @click="showFullResults = false" icon="md-close">收起</Button>
      </div>

      <Row :gutter="16">
        <Col
          v-for="item in displayRecommendations"
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

              <div class="recommend-reason" v-if="item.reason">
                <Icon type="ios-lightbulb-outline" size="14" />
                <span>{{ item.reason }}</span>
              </div>

              <div class="card-footer">
                <span class="meta">
                  <Icon type="ios-eye-outline" /> {{ item.readnum }}
                </span>
                <span class="meta">
                  <Icon type="ios-chatboxes-outline" /> {{ item.comments }}
                </span>
                <Tag size="small" color="blue">{{ item.category_name }}</Tag>
                <span class="score">⭐{{ (item.recommend_score * 100).toFixed(0) }}</span>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      <div class="load-more" v-if="hasMoreResults">
        <Button @click="loadMore" :loading="loadingMore" type="default">加载更多</Button>
      </div>
    </div>
  </div>
</template>

<script>
import HeaderMenu from "../components/HeaderMenu";
import { deepseekHybridRecommendStream, clearDeepseekMemory, updateHistory } from '@/api';

export default {
  name: "IntelligentRecommend",
  components: { HeaderMenu },
  data() {
    const now = new Date();
    const timeStr = now.getHours().toString().padStart(2,'0') + ':' +
                    now.getMinutes().toString().padStart(2,'0');
    return {
      userInput: '',
      isLoading: false,
      isClearing: false,
      loadingMore: false,
      chatMessages: [
        {
          type: 'bot',
          text: '你好！我是基于 DeepSeek 的智能推荐助手。我可以理解你的自然语言描述，结合你的阅读偏好，为你精准推荐新闻。试试告诉我你想看什么？',
          time: timeStr,
          suggestions: [
            '给我推荐今天的科技新闻',
            '我想看人工智能相关的深度文章',
            '推荐财经和国际新闻，不要娱乐'
          ]
        }
      ],
      // 完整结果缓存
      fullRecommendations: [],
      showFullResults: false,
      displayCount: 8,
      lastIntent: null,
      // 流式控制
      streamAborter: null,       // AbortController 引用
      streamingMsgIndex: -1,     // 正在流式更新的消息索引
    };
  },
  computed: {
    displayRecommendations() {
      return this.fullRecommendations.slice(0, this.displayCount);
    },
    hasMoreResults() {
      return this.displayCount < this.fullRecommendations.length;
    }
  },
  methods: {
    // ========== 核心：发送流式推荐请求 ==========
    sendRequest() {
      if (!this.userInput.trim() || this.isLoading) return;

      const input = this.userInput.trim();
      this.userInput = '';

      const userId = sessionStorage.getItem('userId');
      if (!userId) {
        this.$Message.warning('请先登录');
        this.$router.push('/login');
        return;
      }

      // 取消上次未完成的流
      if (this.streamAborter) {
        this.streamAborter.abort();
        this.streamAborter = null;
      }

      const now = new Date();
      const timeStr = now.getHours().toString().padStart(2,'0') + ':' +
                      now.getMinutes().toString().padStart(2,'0');

      // 添加用户消息
      this.chatMessages.push({ type: 'user', text: input, time: timeStr });

      // 预插入助手消息占位 (后续流式填充)
      const botMsgIndex = this.chatMessages.length;
      const botMsg = {
        type: 'bot',
        text: '',                      // 打字机文本
        explanation: '正在分析你的需求...',
        newsCards: [],                 // 收到 phase1 后填充
        totalCount: 0,
        pipelineTrace: {},
        time: timeStr,
        suggestions: [],
        _streaming: true,             // 标记流式进行中
      };
      this.chatMessages.push(botMsg);
      this.streamingMsgIndex = botMsgIndex;

      this.isLoading = true;
      this.$nextTick(() => this.scrollToBottom());

      // 发起流式请求
      this.streamAborter = deepseekHybridRecommendStream(
        userId, input, 20,
        {
          // ---- Start: 连接建立 ----
          onStart: (data) => {
            const msg = this.chatMessages[botMsgIndex];
            if (msg) msg.explanation = data.msg || '正在分析你的需求...';
          },

          // ---- Status: 流水线进度 ----
          onStatus: (data) => {
            const msg = this.chatMessages[botMsgIndex];
            if (msg) msg.explanation = data.msg || '处理中...';
            this.$nextTick(() => this.scrollToBottom());
          },

          // ---- Phase1: 结构化数据到达, 立即渲染新闻卡片 ----
          onPhase1: (data) => {
            const msg = this.chatMessages[botMsgIndex];
            if (!msg) return;

            const newsCards = (data.recommendations || []).map(r => ({
              newsid: r.newsid,
              title: r.title || '无标题',
              category_name: r.category_name || '综合',
              recommend_score: r.recommend_score || 0,
              readnum: r.readnum || 0,
              comments: r.comments || 0,
              reason: r.reason || '',
              date: r.date || '',
              pic_url: r.pic_url || '',
              mainpage: r.mainpage || '',
            }));

            msg.newsCards = newsCards.slice(0, 5);
            msg.totalCount = data.total;
            msg.pipelineTrace = data.pipeline_trace || {};
            msg.explanation = '';  // 清空占位文本, 准备接收流式解释

            // 清空 text 准备接收打字机内容
            msg.text = '';

            this.fullRecommendations = newsCards;
            this.lastIntent = data.intent;
            this.displayCount = 8;
            this.showFullResults = false;

            if (data.total > 0) {
              this.$Message.success(`DeepSeek 为你找到 ${data.total} 条推荐`);
            } else {
              this.$Message.info('未找到匹配新闻，试试其他关键词');
            }
          },

          // ---- Text Chunk: 打字机追加 ----
          onText: (chunk) => {
            const msg = this.chatMessages[botMsgIndex];
            if (!msg) return;
            msg.text = (msg.text || '') + chunk;
            // 首块文本到达时关闭 loading
            if (this.isLoading && msg.text.length > 0) {
              this.isLoading = false;
            }
            this.$nextTick(() => this.scrollToBottom());
          },

          // ---- Done: 流结束 ----
          onDone: (data) => {
            const msg = this.chatMessages[botMsgIndex];
            if (msg) {
              msg._streaming = false;
              msg.suggestions = this.getSmartSuggestions(input, this.lastIntent || {});
              // 如果没有收到任何 text, 用 fallback
              if (!msg.text) {
                msg.text = `为你找到 ${data.total} 篇相关新闻。`;
              }
            }
            this.isLoading = false;
            this.streamAborter = null;
            this.streamingMsgIndex = -1;
            this.$nextTick(() => this.scrollToBottom());
          },

          // ---- Error: 流失败 ----
          onError: (err) => {
            console.error('SSE Stream 错误:', err);
            const msg = this.chatMessages[botMsgIndex];
            if (msg) {
              msg._streaming = false;
              msg.text = msg.text || '抱歉，推荐服务暂时不可用。请稍后再试。';
              msg.newsCards = [];
            }
            this.isLoading = false;
            this.streamAborter = null;
            this.streamingMsgIndex = -1;
            this.$Message.error('流式请求失败，请重试');
          },
        }
      );
    },

    // ========== 智能跟进建议 ==========
    getSmartSuggestions(input, intent) {
      const suggestions = [];
      const kw = intent.keywords || [];
      const cats = intent.categories || [];

      if (cats.length > 0) {
        suggestions.push(`继续推荐更多${cats[0]}新闻`);
      }
      if (kw.length > 0) {
        suggestions.push(`深入搜索"${kw[0]}"相关内容`);
      }
      if (input.includes('科技') || kw.some(k => ['AI','人工智能','科技'].includes(k))) {
        suggestions.push('推荐人工智能创业相关新闻');
      }
      if (input.includes('财经') || cats.includes('财经')) {
        suggestions.push('推荐股票市场最新动态');
      }

      suggestions.push('换一批推荐');
      suggestions.push('根据我的阅读历史推荐');

      // 去重截断
      return [...new Set(suggestions)].slice(0, 4);
    },

    // ========== 清空记忆 ==========
    async clearMemory() {
      const userId = sessionStorage.getItem('userId');
      if (!userId) {
        this.$Message.warning('请先登录');
        return;
      }

      this.isClearing = true;
      try {
        const res = await clearDeepseekMemory(userId);
        if (res.status === '200') {
          // 清空本地对话列表 (保留欢迎消息)
          const welcomeMsg = this.chatMessages[0];
          this.chatMessages = [welcomeMsg];
          this.fullRecommendations = [];
          this.showFullResults = false;
          this.$Message.success(res.message || '记忆已清空，我们可以开启全新的话题啦！');
        } else {
          this.$Message.error(res.message || '清空失败');
        }
      } catch (error) {
        console.error('清空记忆失败:', error);
        this.$Message.error('清空失败，请稍后重试');
      } finally {
        this.isClearing = false;
      }
    },

    // ========== 快捷建议 ==========
    useSuggestion(text) {
      this.userInput = text;
      this.sendRequest();
    },

    // ========== 展示完整结果 ==========
    showAllResults() {
      this.showFullResults = true;
      this.$nextTick(() => {
        const section = document.querySelector('.results-section');
        if (section) section.scrollIntoView({ behavior: 'smooth' });
      });
    },

    // ========== 新闻详情跳转 ==========
    openNewsDetail(newsid) {
      const userId = sessionStorage.getItem('userId');
      if (userId) {
        updateHistory(userId, newsid);
      }
      this.$router.push(`/newspage/${newsid}`);
    },

    // ========== 工具函数 ==========
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

    loadMore() {
      this.loadingMore = true;
      setTimeout(() => {
        this.displayCount += 8;
        this.loadingMore = false;
      }, 300);
    },

    scrollToBottom() {
      const container = this.$refs.chatHistory;
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    }
  },
  beforeDestroy() {
    // 清理未完成的流式连接
    if (this.streamAborter) {
      this.streamAborter.abort();
      this.streamAborter = null;
    }
  },
  mounted() {
    // 初始滚动
    this.$nextTick(() => this.scrollToBottom());
  },
  watch: {
    chatMessages: {
      deep: true,
      handler() {
        this.$nextTick(() => this.scrollToBottom());
      }
    }
  }
};
</script>

<style scoped>
.intelligent-recommend-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  padding-bottom: 50px;
}

/* ========== 聊天区域 ========== */
.chat-section {
  max-width: 900px;
  margin: 0 auto;
  padding: 30px 20px;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 0 4px;
}

.header-left h2 {
  color: #fff;
  font-size: 26px;
  margin: 0 0 4px 0;
}

.subtitle {
  font-size: 13px;
  color: rgba(255,255,255,0.65);
  margin: 0;
}

.clear-btn {
  border-color: rgba(255,100,100,0.5) !important;
  color: rgba(255,150,150,0.9) !important;
}
.clear-btn:hover {
  background: rgba(255,80,80,0.15) !important;
}

/* ========== 对话历史 ========== */
.chat-history {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(12px);
  border-radius: 16px;
  padding: 24px;
  max-height: 500px;
  overflow-y: auto;
  margin-bottom: 20px;
  border: 1px solid rgba(255,255,255,0.08);
}

.welcome-tip {
  text-align: center;
  padding: 40px 0;
  color: rgba(255,255,255,0.5);
}
.welcome-tip p {
  margin-top: 12px;
  font-size: 14px;
}

.message {
  display: flex;
  margin-bottom: 20px;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}

.user-message { flex-direction: row-reverse; }
.user-message .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  margin-right: 10px;
}
.bot-message .message-content {
  background: rgba(255,255,255,0.12);
  color: rgba(255,255,255,0.92);
  margin-left: 10px;
  border: 1px solid rgba(255,255,255,0.08);
}

.message-avatar {
  font-size: 30px;
  flex-shrink: 0;
  line-height: 40px;
}

.message-content {
  max-width: 78%;
  padding: 14px 18px;
  border-radius: 14px;
  position: relative;
}

.message-text {
  line-height: 1.7;
  margin-bottom: 6px;
  white-space: pre-wrap;
  word-break: break-word;
}

/* LLM 解释 */
.llm-explanation {
  background: rgba(255,215,0,0.12);
  border-left: 3px solid #ffc107;
  padding: 10px 14px;
  border-radius: 6px;
  margin: 8px 0;
  font-size: 14px;
  color: rgba(255,255,255,0.9);
  display: flex;
  align-items: flex-start;
  gap: 8px;
}
.llm-explanation i { color: #ffc107; flex-shrink: 0; margin-top: 1px; }

/* 打字机光标闪烁 */
.typing-cursor {
  display: inline-block;
  color: #ffc107;
  font-weight: bold;
  animation: blink 0.8s infinite;
  margin-left: 1px;
}
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* Pipeline trace */
.pipeline-trace {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  margin: 8px 0;
  font-size: 12px;
}
.trace-label {
  color: rgba(255,255,255,0.5);
  margin-right: 4px;
}

/* 内嵌新闻卡片 */
.inline-news-cards {
  margin: 10px 0 4px;
  border-top: 1px solid rgba(255,255,255,0.08);
  padding-top: 8px;
}
.cards-title {
  font-size: 13px;
  color: rgba(255,255,255,0.6);
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}
.inline-news-item {
  display: flex;
  align-items: flex-start;
  padding: 10px 12px;
  margin-bottom: 6px;
  background: rgba(255,255,255,0.06);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}
.inline-news-item:hover {
  background: rgba(255,255,255,0.12);
  border-color: rgba(102,126,234,0.4);
  transform: translateX(4px);
}
.inline-news-rank {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-size: 12px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-right: 12px;
  margin-top: 2px;
}
.inline-news-body { flex: 1; min-width: 0; }
.inline-news-title {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  line-height: 1.5;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.inline-news-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: rgba(255,255,255,0.5);
}
.meta-score { color: #ffc107; }
.inline-news-reason {
  margin-top: 4px;
  font-size: 12px;
  color: rgba(255,255,255,0.45);
  display: flex;
  align-items: center;
  gap: 4px;
}
.show-all-link {
  text-align: center;
  padding: 8px;
  color: #667eea;
  cursor: pointer;
  font-size: 13px;
  border-radius: 6px;
  transition: background 0.2s;
}
.show-all-link:hover { background: rgba(102,126,234,0.1); }

/* 快捷建议 */
.message-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 8px;
}

.message-time {
  font-size: 11px;
  color: rgba(255,255,255,0.3);
  margin-top: 8px;
  text-align: right;
}
.user-message .message-time { text-align: left; }

/* 加载 */
.loading-dots {
  display: flex;
  gap: 5px;
  margin-bottom: 8px;
}
.loading-dots span {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: rgba(255,255,255,0.6);
  animation: bounce 1.4s infinite ease-in-out both;
}
.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
.loading-text {
  font-size: 13px;
  color: rgba(255,255,255,0.45);
}

/* ========== 输入区 ========== */
.input-section {
  background: rgba(255,255,255,0.08);
  backdrop-filter: blur(12px);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid rgba(255,255,255,0.08);
}

.main-input /deep/ .ivu-input {
  background: rgba(255,255,255,0.1);
  color: #fff;
  border: 1px solid rgba(255,255,255,0.15);
  font-size: 15px;
}
.main-input /deep/ .ivu-input::placeholder {
  color: rgba(255,255,255,0.4);
}
.main-input /deep/ .ivu-input:focus {
  border-color: rgba(102,126,234,0.6);
  box-shadow: 0 0 0 2px rgba(102,126,234,0.2);
}

.quick-actions {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* ========== 完整结果区 ========== */
.results-section {
  max-width: 900px;
  margin: 30px auto;
  padding: 0 20px;
}

.results-header {
  background: rgba(255,255,255,0.1);
  backdrop-filter: blur(12px);
  padding: 18px 24px;
  border-radius: 12px;
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid rgba(255,255,255,0.08);
}
.results-header h3 {
  margin: 0;
  color: #fff;
  font-size: 18px;
}

.news-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 12px;
  height: 100%;
  background: rgba(255,255,255,0.95) !important;
}
.news-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.25);
}
.card-title {
  font-weight: bold;
  font-size: 15px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.card-image {
  width: 100%;
  height: 140px;
  overflow: hidden;
  border-radius: 8px;
  margin-bottom: 10px;
}
.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}
.news-card:hover .card-image img { transform: scale(1.05); }

.card-content { padding: 4px 0; }
.summary {
  font-size: 13px;
  color: #666;
  line-height: 1.6;
  margin-bottom: 10px;
  height: 42px;
  overflow: hidden;
}
.recommend-reason {
  background: #fff9e6;
  padding: 6px 10px;
  border-radius: 6px;
  margin-bottom: 10px;
  font-size: 12px;
  color: #856404;
  border-left: 3px solid #ffc107;
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid #eee;
  font-size: 12px;
  color: #999;
  gap: 8px;
}
.meta { display: flex; align-items: center; gap: 3px; }
.score { color: #f59e0b; font-weight: 600; }

.load-more {
  text-align: center;
  margin-top: 30px;
}

@media (max-width: 768px) {
  .chat-header h2 { font-size: 20px; }
  .message-content { max-width: 88%; }
  .chat-history { max-height: 380px; padding: 16px; }
}
</style>
