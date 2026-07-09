# 多模态新闻推荐系统 — Multi-Model Recommendation System

> **基于正交提示混合专家与动态蒸馏的 LLM + PromptMM 双擎新闻推荐平台**

---

## 🏗 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vue.js)                        │
│   NewsPage (用户端)          Admin (管理后台)                │
│   IntelligentRecommend.vue   Spider.vue                     │
└──────────────┬────────────────────┬─────────────────────────┘
               │ HTTP/REST          │ HTTP/REST
               ▼                    ▼
┌──────────────────────────────────────────────────────────────┐
│               Django Backend (newsapi)                       │
│                                                              │
│  ┌─────────────────────┐   ┌──────────────────────────┐     │
│  │   LLM Agent 引擎     │   │  PromptMM 排序引擎        │     │
│  │                     │   │                          │     │
│  │ DeepSeek-v4-flash   │   │ Student_LightGCN         │     │
│  │   ↓                 │   │   ↓                      │     │
│  │ 意图解析 + 解释生成  │   │ 纯ID Embedding + 点积    │     │
│  │   ↓                 │   │   ↓                      │     │
│  │ 多轮对话记忆         │   │ 毫秒级精排打分           │     │
│  │ (AgentConversation) │   │ (Phase 3.2 模型加载)     │     │
│  └─────────┬───────────┘   └───────────┬──────────────┘     │
│            │                           │                     │
│            └─────────┬─────────────────┘                     │
│                      ▼                                       │
│           Hybrid Pipeline (混合流水线)                        │
│     Intent → Recall → Rank → Explain 四阶段串联              │
└──────────────────────────────────────────────────────────────┘
               │                          │
               ▼                          ▼
┌──────────────────────┐   ┌──────────────────────────────────┐
│   MySQL (news)       │   │  PromptMM Training (离线)         │
│   - 新闻/用户/历史    │   │  - Teacher (多模态GCN)            │
│   - 对话记忆          │   │  - Student (LightGCN纯ID)        │
│   - 推荐/评论         │   │  - DTS 动态温度蒸馏               │
└──────────────────────┘   └──────────────────────────────────┘
```

## 🚀 核心创新点

| 创新点 | 说明 |
|---|---|
| **LLM + 深度学习双擎** | DeepSeek Agent 负责语义理解与自然交互; PromptMM Student 负责毫秒级个性化打分 |
| **混合流水线 (Hybrid Pipeline)** | Intent(LLM) → Recall(DB) → Rank(PromptMM) → Explain(LLM) 四阶段协同, 兼顾语义理解与精准排序 |
| **多轮对话记忆** | AgentConversation 模型持久化上下文, 每次请求注入最近 3 轮对话, 实现真正的多轮交互式推荐 |
| **DTS 动态温度蒸馏** | 梯度驱动的自适应温度调度: T_t = T_{t-1}·exp(-η·∂L/∂T), EMA 平滑 + Warmup |
| **ProMoE 正交专家门控** | Gram-Schmidt 正交化 + ||G^T G - I||_F 惩罚 Loss, 确保模态独立专家互不干扰 |

## 📂 项目结构

```
multi-model-recommendation-system/
├── FinalProject/newsapi/          # Django 后端
│   ├── newsServer/                # 路由 + 设置
│   │   ├── urls.py                # 全 API 路由 (含 Agent 端点)
│   │   ├── settings.py            # Django 配置 (含 DEEPSEEK_API_KEY)
│   │   └── models/                # 视图层
│   │       ├── user.py            # 用户注册/登录/画像
│   │       ├── news.py            # 新闻 CRUD/推荐/评论
│   │       ├── spider.py          # 爬虫控制 (协作式取消)
│   │       ├── deepseek_agent_view.py  # DeepSeek Agent API
│   │       └── intelligent_agent.py    # 规则推荐 API
│   ├── Recommend/                 # ⭐ 推荐引擎核心
│   │   ├── DeepSeekAgent.py       # DeepSeek LLM 客户端
│   │   ├── HybridPipeline.py      # Intent→Recall→Rank→Explain 流水线
│   │   ├── PromptMMInference.py   # PromptMM 排序引擎 (桩→模型)
│   │   ├── NewsRecommendAgent.py  # 规则评分推荐引擎
│   │   ├── LLMInterface.py        # LLM 抽象层 (DashScope/ModelScope)
│   │   └── LLMConfig.py           # LLM 配置 (含 DeepSeek)
│   ├── Spider/                    # 新闻爬虫
│   │   ├── NewsUrlSpider.py       # URL 采集 (协作式 DB 状态取消)
│   │   └── NewsDetailSpider.py    # 详情抓取 (Selenium headless)
│   └── news_api/models.py         # ⭐ Django ORM 模型 (含 AgentConversation)
├── PromptMM/                      # 多模态知识蒸馏训练
│   ├── codes/Models.py            # Teacher (多模态GCN) + Student (LightGCN)
│   ├── codes/main_DTS.py          # DTS 蒸馏训练主程序
│   └── README.md
├── NewsPage/                      # 用户端 Vue 前端
│   └── src/views/
│       ├── IntelligentRecommend.vue  # 智能推荐对话界面
│       └── Register.vue              # 注册页
├── admin/                         # 管理后台 Vue 前端
│   └── src/views/
│       └── Spider.vue             # 爬虫控制面板
└── CLAUDE.md                      # ⭐ 论文-代码实现度矩阵
```

## 🔌 API 端点速查

### LLM Agent (DeepSeek)
| 方法 | 端点 | 说明 |
|---|---|---|
| POST | `/api/agent/deepseek/chat/` | 对话式推荐 (单轮意图解析) |
| GET | `/api/agent/deepseek/profile/` | 用户偏好画像生成 |
| **POST** | **`/api/agent/deepseek/hybrid/`** | **混合流水线推荐 (全链路)** ⭐ |

### 新闻 QA Agent
| 方法 | 端点 | 说明 |
|---|---|---|
| POST | `/api/agent/news-qa/` | 新闻智能问答 (RAG) |
| GET | `/api/agent/vector-status/` | 向量化进度查询 |

### 智能推荐 (规则引擎)
| 方法 | 端点 | 说明 |
|---|---|---|
| GET | `/api/intelligent/recommend/` | 规则评分推荐 (keywords + 多维度) |

## ⚡ 快速启动

### 1. 配置 DeepSeek API Key
```bash
# 方式一: 环境变量
export DEEPSEEK_API_KEY="sk-your-key"

# 方式二: 编辑 FinalProject/newsapi/newsServer/settings.py
DEEPSEEK_API_KEY = "sk-your-key"
```

### 2. 初始化数据库
```bash
cd FinalProject/newsapi
python manage.py makemigrations news_api
python manage.py migrate
```

### 3. 启动后端
```bash
python manage.py runserver 0.0.0.0:8000
```

### 4. 测试混合推荐流水线
```bash
curl -X POST http://localhost:8000/api/agent/deepseek/hybrid/ \
  -H "Content-Type: application/json" \
  -d '{"userid": 100000, "user_query": "推荐人工智能相关的科技新闻", "top_k": 10}'
```

## 📊 开发阶段

| Phase | 状态 | 内容 |
|---|---|---|
| Phase 1 | ✅ | 基础设施: 用户系统/新闻爬虫/管理后台 |
| Phase 2 | ✅ | 规则推荐引擎 + DTS 蒸馏训练 |
| Phase 3.1 | ✅ | DeepSeek Agent + 多轮对话记忆 + Hybrid Pipeline |
| Phase 3.2 | 🔴 | PromptMM 模型加载 (Student_LightGCN .pt → 在线推理) |
| Phase 4 | 🔴 | 端到端部署优化 + 性能压测 |
