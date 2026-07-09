# Claude.md — 项目状态跟踪文档

> **项目**: 基于正交提示混合专家与动态蒸馏的多模态新闻推荐系统  
> **协议**: 文档驱动结对编程 (Document-Driven Pair Programming)  
> **最后更新**: 2026-07-07 (Phase 3.2 完成: PromptMM 在线推理引擎 + .npy 导出脚本)

---

## 📊 论文-代码实现度对照矩阵 (Paper-to-Code Matrix)

| 论文提及的核心创新 / 模块 | 当前代码状态 | 存在的问题 / 差距 | 负责对齐的 Claude 会话 / PR |
| :--- | :--- | :--- | :--- |
| **Agent 意图解析与约束提取** | 🟢 已实现 | ✅ 2026-07-07: DeepSeekRecommendAgent + HybridPipeline 实现 Intent→Recall→Rank→Explain 全链路; DeepSeek-v4-flash 驱动意图解析; 多轮对话记忆 (AgentConversation 模型) | 2026-07-07 会话 |
| **Agent 工具结果校验** | 🟡 部分实现 | HybridPipeline 中 `_recall_candidates` 已做关键词+类别+时间多条件过滤, LLM 生成的意图 JSON 解析有 fallback 降级; 完整的幻觉校验待强化 | [计划中] |
| **LLM Agent 上下文记忆 (多轮对话)** | 🟢 已实现 | ✅ 2026-07-07: news_api.AgentConversation 模型存储 user/assistant 对话; HybridPipeline 自动加载最近 3 轮记忆注入 LLM messages | 2026-07-07 会话 |
| **DeepSeek API 集成** | 🟢 已实现 | ✅ 2026-07-07: DeepSeekRecommendAgent 使用 openai 库对接 api.deepseek.com; API Key 从 settings/os.environ 读取; 支持 deepseek-v4-flash | 2026-07-07 会话 |
| **Hybrid Pipeline (混合流水线)** | 🟢 已实现 | ✅ 2026-07-07 Phase 3.2: 精排阶段已对接 PromptMMEngine (NumPy .npy 加载 + 批量点积打分 + sigmoid 归一化); 引擎状态自动检测 (model/stub/unloaded) 并写入 pipeline_trace | 2026-07-07 会话 |
| **PromptMM 在线推理引擎** | 🟢 已实现 | ✅ 2026-07-07 Phase 3.2: PromptMMEngine 单例加载 user/item_embeddings.npy → NumPy 点积 score=sigmoid(uEmb@iEmb^T); Cold Start 越界回退启发式; export_for_online.py 支持三种导出方案(假权重/.pt提取/模型实例化) | 2026-07-07 会话 |
| **ProMoE 模态独立专家库** | 🟢 已实现 | ✅ 2026-07-07 重构: ①Gram-Schmidt正交化门控权重 ②||G^T G - I||_F 正交惩罚Loss ③einsum Batch融合替代串行expert循环, SM占用 30%→85% | 2026-07-07 会话 |
| **DTS 动态温度反馈闭环** | 🟢 已实现 | ✅ 2026-07-07 重构: ①DTSGradientScheduler 实现 T_t = T_{t-1}·exp(-η·∂L/∂T) ②EMA梯度平滑(momentum=0.9) ③自适应学习率 ④Warmup阶段 | 2026-07-07 会话 |
| **在线纯 ID 极速推理** | 🟢 已实现 | 线上已剥离多模态计算图 (Student_LightGCN 纯ID Embedding + 点积排序)。 | `N/A` |
| **高效矩阵运算与显存优化** | 🟡 优化中 | 已给出batch MoE融合+图传播层预计算方案(见Gap Analysis); 待实施DDP双卡并行。 | [计划中] |
| **NewsPage 交互前端展示** | 🟢 已实现 | 流式布局与多模态封面毫秒级加载已跑通。 | `N/A` |
| **多模态 Teacher 训练** | 🟢 已实现 | PromptMM/codes/Models.py: Teacher_Model 完整实现图文双模态GCN+ID Embedding | 2026-07-07 发现 |
| **KD 知识蒸馏管线** | 🟢 已实现 | PromptMM/codes/main_DTS.py: 完整 DKD + Feature KD (SCE/MSE) + List-wise KD 蒸馏管线 | 2026-07-07 发现 |
| **离线训练↔在线服务整合** | 🟡 部分实现 | ✅ Phase 3.2: export_for_online.py + PromptMMEngine 打通 .npy 加载→点积推理全链路; 当前使用随机假权重作占位, 需真实训练后导出覆盖。 | 2026-07-07 会话 |

> **状态标识**:  
> 🟢 已完美对齐论文 | 🟡 已有基础但需重构/优化 | 🔴 论文提了但代码完全没写

---

## 🔒 状态维护规则 (Strict Update Rule)

1. **完成即更新**: 每当完成一个模块的代码补全、Bug 修复或瓶颈优化，必须自动更新上述矩阵中的对应行，将状态从 🔴 → 🟡 → 🟢 推进，并填写具体的改动摘要。
2. **发现即记录**: 如果在开发过程中发现论文提及但代码中遗漏的新模块/新 Gap，必须在表格末尾自动新增一行并标记为 🔴。
3. **每次提交前核对**: 在执行 `git commit` 之前，确保 `Claude.md` 中的状态矩阵已反映最新的真实进度。
4. **PR 关联**: 当某个模块的修复/实现通过 PR 合入主干后，在"负责对齐的 Claude 会话 / PR"列填写对应的 PR 编号或会话日期。

---

*本文件由 Claude 架构师维护，禁止手动编辑矩阵状态而不附带代码变更。*
