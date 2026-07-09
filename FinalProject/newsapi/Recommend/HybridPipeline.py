# -*- coding: utf-8 -*-
"""
    Author: AI Architect
    Desc: 混合推荐流水线 (Hybrid Pipeline)

    将 DeepSeek LLM Agent 的上下文理解能力与 PromptMM 排序引擎串联:

        User Query
           │
           ▼
    ┌─────────────────┐
    │ 1. Intent Extract│  ← DeepSeek Agent + 对话记忆 + 用户画像
    │    (LLM 解析意图) │
    └────────┬────────┘
             │ keywords, categories, time_range
             ▼
    ┌─────────────────┐
    │ 2. Recall (粗排) │  ← Django ORM 从 newsdetail 检索候选集
    │    (DB 多条件过滤)│
    └────────┬────────┘
             │ candidate_ids (≤ 200)
             ▼
    ┌─────────────────┐
    │ 3. Rank  (精排)  │  ← PromptMMInference.rank() 重排序
    │    (模型打分排序) │     当前: 启发式桩 | Phase 3.2: Student_LightGCN
    └────────┬────────┘
             │ top_k news_ids with scores
             ▼
    ┌─────────────────┐
    │ 4. Explain(生成) │  ← DeepSeek Agent 生成自然语言推荐理由
    │    (LLM 生成解释) │
    └────────┬────────┘
             │
             ▼
      结构化推荐结果 + 自然语言解释
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from django.db.models import Q

from Recommend.DeepSeekAgent import DeepSeekRecommendAgent
from Recommend.PromptMMInference import get_engine as get_promptmm_engine

logger = logging.getLogger(__name__)

# 每轮对话保留的历史消息数量
MAX_HISTORY_ROUNDS = 6  # 3 轮对话 = 6 条消息 (user + assistant 交替)


# =============================================================================
#  意图解析 (Step 1)
# =============================================================================

def _extract_intent(
    agent: DeepSeekRecommendAgent,
    userid: int,
    user_query: str,
    history_messages: List[Dict[str, str]],
) -> Dict:
    """
    利用 DeepSeek LLM 解析用户意图

    Args:
        agent: DeepSeek 推荐智能体实例
        userid: 用户 ID
        user_query: 当前用户输入
        history_messages: 最近 N 轮历史对话 [{"role":"user","content":"..."}, ...]

    Returns:
        {
            "keywords": [...],
            "categories": [...],
            "category_ids": [...],
            "time_range_days": None | int,
            "primary_topic": "...",
            "query_type": "general" | "refresh" | "history",
            "explanation": "..."
        }
    """
    # 构建带记忆的 messages
    system_prompt = agent._build_system_prompt(userid)
    messages = [{'role': 'system', 'content': system_prompt}]

    # 注入最近 N 轮历史对话
    if history_messages:
        messages.extend(history_messages[-MAX_HISTORY_ROUNDS:])

    # 当前 Query
    messages.append({'role': 'user', 'content': user_query})

    llm_output = agent._call_llm(messages, temperature=0.3, max_tokens=512)

    intent = {
        'keywords': [],
        'categories': [],
        'category_ids': [],
        'time_range_days': None,
        'primary_topic': '',
        'query_type': 'general',
        'explanation': '',
    }

    if llm_output:
        try:
            cleaned = llm_output.strip()
            if cleaned.startswith('```'):
                cleaned = cleaned.split('\n', 1)[-1]
                if cleaned.endswith('```'):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()
            parsed = json.loads(cleaned)
            intent_data = parsed.get('intent', parsed)

            intent['keywords'] = intent_data.get('keywords', [])
            intent['categories'] = intent_data.get('categories', [])
            intent['time_range_days'] = intent_data.get('time_range_days')
            intent['primary_topic'] = intent_data.get('primary_topic', '')
            intent['query_type'] = intent_data.get('query_type', 'general')
            intent['explanation'] = parsed.get('explanation', '')

            # 将类别名映射为 category_id
            category_name_to_id = {
                '美股': 0, '国内': 1, '国际': 2, '体育': 4,
                '娱乐': 5, '军事': 6, '科技': 7, '财经': 8, '股市': 9,
            }
            for cat_name in intent['categories']:
                cid = category_name_to_id.get(cat_name)
                if cid is not None and cid not in intent['category_ids']:
                    intent['category_ids'].append(cid)

        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"意图 JSON 解析失败, 使用关键词降级: {e}")
            # 降级: 用 jieba 简单分词提取关键词
            try:
                import jieba
                words = jieba.lcut(user_query)
                stop = {'的', '了', '是', '我', '想', '看', '要', '给', '推荐', '新闻', '一下', '一些', '什么'}
                intent['keywords'] = [w for w in words if len(w) > 1 and w not in stop][:5]
                intent['explanation'] = llm_output[:200] if llm_output else ''
            except ImportError:
                intent['explanation'] = '意图解析降级模式'
    else:
        # LLM 不可用: 完全降级
        try:
            import jieba
            words = jieba.lcut(user_query)
            stop = {'的', '了', '是', '我', '想', '看', '要', '给', '推荐', '新闻', '一下', '一些', '什么'}
            intent['keywords'] = [w for w in words if len(w) > 1 and w not in stop][:5]
        except ImportError:
            intent['keywords'] = [user_query[:20]]
        intent['explanation'] = '基于关键词匹配的降级推荐'

    # 合并用户历史标签作为补充关键词
    try:
        from news_api.models import user as UserModel
        u = UserModel.objects.filter(userid=userid).first()
        if u and u.tags and u.tags != '综合':
            user_tag_list = [t.strip() for t in u.tags.split(',') if t.strip()]
            for t in user_tag_list:
                if t not in intent['keywords']:
                    intent['keywords'].append(t)
    except Exception:
        pass

    logger.info(
        f"意图解析完成 | userid={userid} | "
        f"keywords={intent['keywords'][:5]} | "
        f"categories={intent['categories']} | "
        f"time_range={intent['time_range_days']}"
    )
    return intent


# =============================================================================
#  候选召回 (Step 2)
# =============================================================================

def _recall_candidates(intent: Dict, userid: int, max_candidates: int = 200) -> List[int]:
    """
    从数据库检索候选新闻 ID 列表

    Args:
        intent: 解析后的用户意图
        userid: 用户 ID
        max_candidates: 最大候选数

    Returns:
        [news_id, ...]
    """
    from news_api.models import newsdetail, history

    queryset = newsdetail.objects.all()

    # 类别过滤
    if intent['category_ids']:
        queryset = queryset.filter(category__in=intent['category_ids'])

    # 时间范围过滤
    if intent['time_range_days']:
        threshold = datetime.now() - timedelta(days=intent['time_range_days'])
        threshold_str = threshold.strftime('%Y-%m-%d')
        # MySQL 字符串日期比较 (格式: YYYY-MM-DD 或 YYYY年MM月DD日)
        queryset = queryset.filter(
            Q(date__gte=threshold_str) |
            Q(date__contains=str(threshold.year))
        )

    # 关键词匹配 (标题或 keywords 字段)
    if intent['keywords']:
        kw_filter = Q()
        for kw in intent['keywords'][:8]:
            kw_filter |= Q(title__icontains=kw) | Q(keywords__icontains=kw)
        queryset = queryset.filter(kw_filter)

    # "换一批": 排除用户已浏览过的
    if intent['query_type'] == 'refresh':
        viewed_ids = list(
            history.objects.filter(userid=userid)
            .values_list('history_newsid', flat=True)
            .order_by('-id')[:50]
        )
        if viewed_ids:
            queryset = queryset.exclude(news_id__in=viewed_ids)

    # 按日期降序取候选
    candidate_ids = list(
        queryset.order_by('-date', '-news_id')
        .values_list('news_id', flat=True)[:max_candidates]
    )

    # 如果关键词匹配结果太少, 用热门新闻补足
    if len(candidate_ids) < 20 and intent['keywords']:
        from news_api.models import newshot
        hot_ids = list(
            newshot.objects.all()
            .order_by('-news_hot')
            .values_list('news_id', flat=True)[:max_candidates]
        )
        for hid in hot_ids:
            if hid not in candidate_ids:
                candidate_ids.append(hid)
            if len(candidate_ids) >= max_candidates:
                break

    logger.info(f"候选召回完成 | userid={userid} | candidates={len(candidate_ids)}")
    return candidate_ids[:max_candidates]


# =============================================================================
#  精排 (Step 3)
# =============================================================================

def _rank_candidates(
    userid: int,
    candidate_ids: List[int],
    top_k: int = 20,
) -> List[Tuple[int, float]]:
    """
    调用 PromptMM 推理引擎进行精排

    Args:
        userid: 用户 ID
        candidate_ids: 候选新闻 ID 列表
        top_k: Top-K

    Returns:
        ([(news_id, score), ...], engine_status)  按分数降序 + 引擎状态
    """
    engine = get_promptmm_engine()
    ranked = engine.rank(userid, candidate_ids, top_k)
    engine_status = 'model' if engine.is_loaded() else 'stub'
    logger.info(
        f"精排完成 | userid={userid} | top_k={len(ranked)} | "
        f"engine={engine_status}"
    )
    return ranked, engine_status


# =============================================================================
#  解释生成 (Step 4)
# =============================================================================

def _generate_explanation(
    agent: DeepSeekRecommendAgent,
    userid: int,
    user_query: str,
    ranked_news: List[Dict],
) -> str:
    """
    利用 LLM 为 Top-K 推荐结果生成自然语言解释

    Args:
        agent: DeepSeek 智能体
        userid: 用户 ID
        user_query: 原始用户输入
        ranked_news: 精排后的新闻列表 (含 title, score, category 等)

    Returns:
        自然语言推荐解释
    """
    if not ranked_news:
        return "抱歉，未找到匹配的新闻。请尝试调整搜索条件。"

    # 构建新闻摘要供 LLM 参考
    news_summary_lines = []
    for i, news in enumerate(ranked_news[:5], 1):
        news_summary_lines.append(
            f"{i}. [{news.get('category_name', '综合')}] {news.get('title', '无标题')[:50]}"
        )

    news_summary = '\n'.join(news_summary_lines)

    explain_prompt = (
        f"用户输入: {user_query}\n\n"
        f"为你推荐的 Top-5 新闻:\n{news_summary}\n\n"
        f"请用 2-3 句话向用户解释: 为什么推荐这些新闻？"
        f"要求亲切自然, 中文, 80 字以内。"
    )

    messages = [
        {
            'role': 'system',
            'content': '你是新闻推荐助手的解释引擎。用简洁亲切的中文解释推荐理由。'
        },
        {'role': 'user', 'content': explain_prompt},
    ]

    llm_output = agent._call_llm(messages, temperature=0.5, max_tokens=200)
    if llm_output:
        return llm_output.strip()
    else:
        # 降级解释
        cats = set(n.get('category_name', '') for n in ranked_news[:5])
        return f"为你精选了 {len(ranked_news)} 篇相关新闻，涵盖 {', '.join(list(cats)[:3])} 等领域。"


# =============================================================================
#  对话记忆管理
# =============================================================================

# =============================================================================
#  Phase 4.2: 异步长期记忆压缩器
# =============================================================================

def compress_user_memory(userid: int):
    """
    后台异步压缩用户的对话历史为长期记忆摘要。

    触发条件: AgentConversation 记录 >= 5 条
    行为:
        1. 提取历史对话文本
        2. 调用 DeepSeek LLM 压缩为 80 字摘要
        3. 合并已有 agent_summary_memory
        4. 更新 user.agent_summary_memory
        5. 删除已压缩的 AgentConversation 记录
    """
    import threading as _threading

    def _do_compress():
        try:
            from news_api.models import AgentConversation, user as UserModel
            from Recommend.DeepSeekAgent import DeepSeekRecommendAgent

            # 检查是否需要压缩
            conv_count = AgentConversation.objects.filter(userid=userid).count()
            if conv_count < 5:
                logger.debug(f"记忆压缩跳过 | userid={userid} | count={conv_count} < 5")
                return

            # 获取历史对话
            records = list(
                AgentConversation.objects.filter(userid=userid)
                .order_by('created_at')
            )
            if not records:
                return

            # 提取对话文本
            conv_lines = []
            for r in records:
                role_tag = '用户' if r.role == 'user' else '助手'
                conv_lines.append(f"[{role_tag}]: {r.content[:120]}")
            conv_text = '\n'.join(conv_lines)

            # 获取已有长期记忆
            user_obj = UserModel.objects.filter(userid=userid).first()
            existing_summary = ''
            if user_obj and user_obj.agent_summary_memory:
                existing_summary = user_obj.agent_summary_memory

            # 调用 LLM 压缩
            agent = DeepSeekRecommendAgent()
            compress_prompt = (
                f"【已有长期记忆】\n{existing_summary or '无'}\n\n"
                f"【新增对话】\n{conv_text}\n\n"
                f"请将以上信息合并压缩为 80 字以内的核心兴趣与偏好画像。不要输出废话。"
            )
            messages = [
                {
                    'role': 'system',
                    'content': '你是极简记忆提取专家。请将以下用户的多轮对话，压缩总结为 80 字以内的核心兴趣与偏好画像，合并其已有的长期记忆。不要输出废话。'
                },
                {'role': 'user', 'content': compress_prompt},
            ]

            summary = agent._call_llm(messages, temperature=0.3, max_tokens=150)

            if summary and user_obj:
                summary = summary.strip()[:200]
                UserModel.objects.filter(userid=userid).update(
                    agent_summary_memory=summary
                )
                logger.info(
                    f"长期记忆已更新 | userid={userid} | "
                    f"summary_len={len(summary)} | compressed={len(records)}条"
                )
            elif user_obj:
                # LLM 不可用时用规则兜底
                topics = set()
                for r in records:
                    if r.role == 'user' and r.content:
                        for kw in ['科技', '财经', '体育', '娱乐', '国际', '军事', 'AI', '人工智能',
                                    '股票', '基金', '足球', '电影', '深度', '快讯']:
                            if kw in r.content:
                                topics.add(kw)
                fallback = f"用户关注: {', '.join(list(topics)[:5]) or '综合新闻'}。偏好: 深度阅读与多领域浏览。"
                UserModel.objects.filter(userid=userid).update(
                    agent_summary_memory=fallback[:200]
                )
                logger.info(f"长期记忆(规则降级)已更新 | userid={userid}")

            # 保留最近 2 条, 删除其余 (防止短期记忆完全丢失)
            if len(records) > 4:
                to_keep = records[-4:]  # 保留最近 2 轮 (4 条)
                to_delete_ids = [r.id for r in records if r not in to_keep]
                if to_delete_ids:
                    AgentConversation.objects.filter(id__in=to_delete_ids).delete()
                    logger.debug(
                        f"对话归档 | userid={userid} | "
                        f"deleted={len(to_delete_ids)} | kept={len(to_keep)}"
                    )

        except Exception as e:
            logger.error(f"记忆压缩失败 | userid={userid}: {e}")

    # 在独立 daemon 线程中执行, 不阻塞主请求
    t = _threading.Thread(target=_do_compress, daemon=True)
    t.start()
    logger.debug(f"记忆压缩线程已启动 | userid={userid}")


def _load_conversation_history(userid: int, max_rounds: int = 3) -> List[Dict[str, str]]:
    """
    从数据库加载用户最近的对话历史

    Args:
        userid: 用户 ID
        max_rounds: 最大加载轮数

    Returns:
        [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
    """
    try:
        from news_api.models import AgentConversation

        records = AgentConversation.objects.filter(
            userid=userid
        ).order_by('-created_at')[:max_rounds * 2]

        # 反转回时间顺序
        messages = []
        for r in reversed(list(records)):
            messages.append({'role': r.role, 'content': r.content})
        return messages
    except Exception as e:
        logger.warning(f"加载对话历史失败: {e}")
        return []


def _save_conversation_turn(
    userid: int,
    user_query: str,
    assistant_response: str,
    intent_json: Optional[Dict] = None,
):
    """
    保存一轮对话到数据库

    Args:
        userid: 用户 ID
        user_query: 用户消息
        assistant_response: Agent 回复
        intent_json: Agent 解析的意图 (可选)
    """
    try:
        from news_api.models import AgentConversation

        # 保存 user 消息
        AgentConversation.objects.create(
            userid=userid,
            role='user',
            content=user_query,
        )
        # 保存 assistant 消息
        AgentConversation.objects.create(
            userid=userid,
            role='assistant',
            content=assistant_response,
            intent_json=json.dumps(intent_json, ensure_ascii=False) if intent_json else '',
        )
        logger.debug(f"对话已保存 | userid={userid}")
    except Exception as e:
        logger.warning(f"保存对话失败: {e}")


# =============================================================================
#  核心流水线入口
# =============================================================================

def intelligent_chat_recommend(
    userid: int,
    user_query: str,
    top_k: int = 20,
) -> Dict:
    """
    混合推荐流水线主入口

    Intent → Recall → Rank → Explain 全链路

    Args:
        userid: 用户 ID
        user_query: 用户自然语言输入
        top_k: 返回 Top-K 条推荐

    Returns:
        {
            "status": "ok" | "fallback",
            "user_query": str,
            "intent": {...},
            "explanation": str,
            "total": int,
            "recommendations": [
                {
                    "newsid": int,
                    "title": str,
                    "date": str,
                    "pic_url": str,
                    "mainpage": str,
                    "category": str,
                    "category_name": str,
                    "readnum": int,
                    "comments": int,
                    "recommend_score": float,
                    "reason": str,
                },
                ...
            ],
            "pipeline_trace": {
                "intent": "ok" | "fallback",
                "recall": "ok",
                "rank": "stub" | "model",
                "explain": "ok" | "fallback",
            }
        }
    """
    logger.info(f"=== Hybrid Pipeline 启动 | userid={userid} | query={user_query[:80]} ===")

    trace = {'intent': 'fallback', 'recall': 'ok', 'rank': 'unloaded', 'explain': 'fallback'}

    # 初始化 Agent (单例复用)
    agent = DeepSeekRecommendAgent()

    # ---- Step 0: 加载对话记忆 ----
    history_messages = _load_conversation_history(userid)

    # ---- Step 1: Intent Extraction ----
    intent = _extract_intent(agent, userid, user_query, history_messages)
    trace['intent'] = 'ok' if intent.get('explanation') else 'fallback'

    # ---- Step 2: Recall ----
    candidate_ids = _recall_candidates(intent, userid)
    if not candidate_ids:
        # 意图召回无结果时, 回退到热门新闻
        from news_api.models import newshot
        candidate_ids = list(
            newshot.objects.all()
            .order_by('-news_hot')
            .values_list('news_id', flat=True)[:100]
        )
        intent['explanation'] = (intent.get('explanation', '') or '') + ' (回退至热门推荐)'

    # ---- Step 3: Rank ----
    ranked, engine_status = _rank_candidates(userid, candidate_ids, top_k)
    trace['rank'] = engine_status

    # ---- Step 4: 组装结果 ----
    from news_api.models import newsdetail

    news_map = {
        n.news_id: n
        for n in newsdetail.objects.filter(
            news_id__in=[rid for rid, _ in ranked]
        )
    }

    category_names = {
        0: '美股', 1: '国内', 2: '国际', 3: '国际',
        4: '体育', 5: '娱乐', 6: '军事', 7: '科技', 8: '财经', 9: '股市'
    }

    recommendations = []
    for nid, score in ranked:
        nd = news_map.get(nid)
        if not nd:
            continue

        # 生成推荐理由
        reasons = []
        if intent.get('primary_topic') and intent['primary_topic'] in (nd.title or ''):
            reasons.append(f"匹配'{intent['primary_topic']}'")
        if score > 0.7:
            reasons.append("高匹配度")
        if nd.readnum and nd.readnum > 500:
            reasons.append(f"{nd.readnum}次阅读")
        if not reasons:
            reasons.append("综合推荐")

        recommendations.append({
            'newsid': nd.news_id,
            'title': nd.title or '',
            'date': str(nd.date) if nd.date else '',
            'pic_url': nd.pic_url or '',
            'mainpage': (nd.mainpage or '')[:200],
            'category': nd.category,
            'category_name': category_names.get(nd.category, '其他'),
            'readnum': nd.readnum or 0,
            'comments': nd.comments or 0,
            'recommend_score': round(score, 4),
            'reason': ' | '.join(reasons),
        })

    total = len(recommendations)

    # ---- Step 5: Explain ----
    explanation = _generate_explanation(agent, userid, user_query, recommendations[:5])
    trace['explain'] = 'ok'

    # ---- 保存对话记忆 ----
    assistant_msg = (
        f"为你找到 {total} 篇相关新闻。{explanation}"
        if total > 0
        else "未找到匹配的新闻，请尝试其他关键词。"
    )
    _save_conversation_turn(userid, user_query, assistant_msg, intent)

    # === Phase 4.2: 后台异步压缩长期记忆 ===
    try:
        import threading as _threading2
        _threading2.Thread(target=compress_user_memory, args=(userid,), daemon=True).start()
    except Exception as _e2:
        logger.warning(f"启动记忆压缩线程失败: {_e2}")

    logger.info(f"=== Hybrid Pipeline 完成 | total={total} | trace={trace} ===")

    return {
        'status': 'ok' if total > 0 else 'empty',
        'user_query': user_query,
        'intent': intent,
        'explanation': explanation,
        'total': total,
        'recommendations': recommendations,
        'pipeline_trace': trace,
    }


# =============================================================================
#  Phase 4.1: SSE 流式生成器
# =============================================================================

def intelligent_chat_recommend_stream(
    userid: int,
    user_query: str,
    top_k: int = 20,
):
    """
    混合推荐流水线 — 流式版本 (SSE Generator)

    Steps 1-3 同步执行, Step 4 (Explain) 以 stream=True 调用 DeepSeek API,
    通过 Generator 逐块 yield 结构化数据和流式文本。

    yield 协议 (每行为一个 JSON 对象):
        {"type":"phase1","intent":{...},"recommendations":[...],...}
        {"type":"text","content":"chunk"}
        ...
        {"type":"done","total":N}

    Args:
        userid: 用户 ID
        user_query: 用户自然语言输入
        top_k: Top-K

    Yields:
        str: 每行一个 JSON 对象 (含换行符)
    """
    import json as _json
    import sys as _sys

    logger.info(f"=== Hybrid Pipeline [STREAM] 启动 | userid={userid} | query={user_query[:80]} ===")

    trace = {'intent': 'fallback', 'recall': 'ok', 'rank': 'unloaded', 'explain': 'streaming'}
    agent = DeepSeekRecommendAgent()

    # === 立即发送 heartbeat, 告知前端连接已建立 ===
    yield _json.dumps({'type': 'start', 'msg': '正在分析你的需求...'}, ensure_ascii=False) + '\n'
    _sys.stdout.flush()  # 强制刷新 stdout 缓冲区 (WSGI 依赖)

    # ---- Step 0: 加载对话记忆 ----
    history_messages = _load_conversation_history(userid)

    # ---- Step 1: Intent ----
    yield _json.dumps({'type': 'status', 'stage': 'intent', 'msg': '正在理解你的意图...'}, ensure_ascii=False) + '\n'
    _sys.stdout.flush()

    intent = _extract_intent(agent, userid, user_query, history_messages)
    trace['intent'] = 'ok' if intent.get('explanation') else 'fallback'

    # ---- Step 2: Recall ----
    yield _json.dumps({'type': 'status', 'stage': 'recall', 'msg': '正在检索相关新闻...'}, ensure_ascii=False) + '\n'
    _sys.stdout.flush()

    candidate_ids = _recall_candidates(intent, userid)
    if not candidate_ids:
        from news_api.models import newshot
        candidate_ids = list(
            newshot.objects.all()
            .order_by('-news_hot')
            .values_list('news_id', flat=True)[:100]
        )
        intent['explanation'] = (intent.get('explanation', '') or '') + ' (回退至热门推荐)'

    # ---- Step 3: Rank ----
    yield _json.dumps({'type': 'status', 'stage': 'rank', 'msg': '正在为你个性化排序...'}, ensure_ascii=False) + '\n'
    _sys.stdout.flush()

    ranked, engine_status = _rank_candidates(userid, candidate_ids, top_k)
    trace['rank'] = engine_status

    # ---- 组装结果 ----
    from news_api.models import newsdetail
    news_map = {
        n.news_id: n
        for n in newsdetail.objects.filter(
            news_id__in=[rid for rid, _ in ranked]
        )
    }
    category_names = {
        0: '美股', 1: '国内', 2: '国际', 3: '国际',
        4: '体育', 5: '娱乐', 6: '军事', 7: '科技', 8: '财经', 9: '股市'
    }

    recommendations = []
    for nid, score in ranked:
        nd = news_map.get(nid)
        if not nd:
            continue
        reasons = []
        if intent.get('primary_topic') and intent['primary_topic'] in (nd.title or ''):
            reasons.append(f"匹配'{intent['primary_topic']}'")
        if score > 0.7:
            reasons.append("高匹配度")
        if nd.readnum and nd.readnum > 500:
            reasons.append(f"{nd.readnum}次阅读")
        if not reasons:
            reasons.append("综合推荐")
        recommendations.append({
            'newsid': nd.news_id,
            'title': nd.title or '',
            'date': str(nd.date) if nd.date else '',
            'pic_url': nd.pic_url or '',
            'mainpage': (nd.mainpage or '')[:200],
            'category': nd.category,
            'category_name': category_names.get(nd.category, '其他'),
            'readnum': nd.readnum or 0,
            'comments': nd.comments or 0,
            'recommend_score': round(score, 4),
            'reason': ' | '.join(reasons),
        })

    total = len(recommendations)

    # === yield Phase 1: 结构化数据 (意图 + 新闻卡片 + pipeline trace) ===
    phase1 = {
        'type': 'phase1',
        'intent': intent,
        'recommendations': recommendations,
        'pipeline_trace': trace,
        'total': total,
        'user_query': user_query,
    }
    yield _json.dumps(phase1, ensure_ascii=False) + '\n'

    # === Step 4: Explain (流式) ===
    if recommendations:
        news_summary_lines = []
        for i, news in enumerate(recommendations[:5], 1):
            news_summary_lines.append(
                f"{i}. [{news.get('category_name', '综合')}] {news.get('title', '无标题')[:50]}"
            )
        news_summary = '\n'.join(news_summary_lines)

        explain_prompt = (
            f"用户输入: {user_query}\n\n"
            f"为你推荐的 Top-5 新闻:\n{news_summary}\n\n"
            f"请用 2-3 句话向用户解释: 为什么推荐这些新闻？"
            f"要求亲切自然, 中文, 80 字以内。"
        )
        messages = [
            {'role': 'system', 'content': '你是新闻推荐助手的解释引擎。用简洁亲切的中文解释推荐理由。'},
            {'role': 'user', 'content': explain_prompt},
        ]

        has_stream = False
        try:
            for chunk in agent._call_llm_stream(messages, temperature=0.5, max_tokens=200):
                if chunk:
                    has_stream = True
                    yield _json.dumps({'type': 'text', 'content': chunk}, ensure_ascii=False) + '\n'
        except Exception as e:
            logger.warning(f"流式 Explain 失败: {e}")

        # Fallback: LLM 不可用时发送降级解释
        if not has_stream:
            trace['explain'] = 'fallback'
            cats_set = set(n.get('category_name', '') for n in recommendations[:5])
            fallback_text = f"为你精选了 {total} 篇相关新闻，涵盖 {', '.join(list(cats_set)[:3])} 等领域。"
            yield _json.dumps({'type': 'text', 'content': fallback_text}, ensure_ascii=False) + '\n'
        else:
            trace['explain'] = 'ok'
    else:
        yield _json.dumps(
            {'type': 'text', 'content': '抱歉，未找到匹配的新闻。请尝试调整搜索条件。'},
            ensure_ascii=False
        ) + '\n'
        trace['explain'] = 'fallback'

    # === yield 结束信号 ===
    yield _json.dumps({'type': 'done', 'total': total}, ensure_ascii=False) + '\n'

    # ---- 保存对话记忆 (异步友好) ----
    assistant_msg = (
        f"为你找到 {total} 篇相关新闻。"
        if total > 0
        else "未找到匹配的新闻，请尝试其他关键词。"
    )
    _save_conversation_turn(userid, user_query, assistant_msg, intent)

    # === Phase 4.2: 后台异步压缩长期记忆 (不阻塞响应) ===
    try:
        import threading as _threading
        _threading.Thread(target=compress_user_memory, args=(userid,), daemon=True).start()
    except Exception as _e:
        logger.warning(f"启动记忆压缩线程失败: {_e}")

    logger.info(f"=== Hybrid Pipeline [STREAM] 完成 | total={total} | trace={trace} ===")
