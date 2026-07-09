# -*- coding: utf-8 -*-
"""
    Author: AI Architect
    Desc: DeepSeek 推荐智能体 — 基于 DeepSeek API 的对话式新闻推荐引擎

    Features:
        - 使用 openai 库调用 DeepSeek API (OpenAI 兼容协议)
        - 动态注入用户画像 (tags, history, tagsweight) 构建 System Prompt
        - chat_with_agent(): 对话式推荐交互，解析自然语言意图并返回新闻推荐
        - generate_user_profile(): 利用 LLM 生成用户偏好画像
        - API Key 从 Django settings / 环境变量读取，绝不硬编码

    API 配置:
        Base URL:  https://api.deepseek.com
        Model:     deepseek-v4-flash
"""

import os
import json
import logging
from typing import Optional, Dict, List

from django.conf import settings

logger = logging.getLogger(__name__)


# =============================================================================
#  System Prompt 模板
# =============================================================================

SYSTEM_PROMPT_TEMPLATE = """你是一个专业的新闻推荐智能助手，运行在一个多模态新闻推荐系统中。
你的职责是根据用户的自然语言输入，结合用户的兴趣画像，提供精准的新闻推荐建议。

## 用户长期记忆 (AI 自动总结)
{agent_summary_memory}

## 用户画像
- 用户ID: {userid}
- 用户名: {username}
- 兴趣标签: {tags}
- 标签权重: {tagsweight}
- 最近浏览新闻: {recent_history}
- 最近浏览类别: {recent_categories}

## 可用的新闻类别
0-美股, 1-国内, 2-国际, 3-国际, 4-体育, 5-娱乐, 6-军事, 7-科技, 8-财经, 9-股市

## 你的能力
1. **意图解析**: 理解用户想看的新闻类型、话题、时间范围
2. **推荐建议**: 根据用户输入和用户画像，给出具体的推荐方向（类别、关键词、排序偏好）
3. **用户画像生成**: 分析用户的阅读历史，总结用户的兴趣偏好和阅读习惯

## 回复格式要求
当用户请求推荐时，你必须以 JSON 格式回复（只输出 JSON，不要有其他文字）：
{{
    "intent": {{
        "keywords": ["关键词1", "关键词2"],
        "categories": ["类别名1", "类别名2"],
        "time_range_days": null,
        "query_type": "general",
        "primary_topic": "主要话题"
    }},
    "explanation": "用1-2句话解释你为什么这样推荐"
}}

当用户请求生成用户画像时，以自然语言回复，包含：
- 用户的主要兴趣领域
- 阅读偏好（时间、长度、媒体类型）
- 活跃度评估
- 个性化推荐策略建议"""


# =============================================================================
#  DeepSeekRecommendAgent 核心类
# =============================================================================

class DeepSeekRecommendAgent:
    """基于 DeepSeek API 的新闻推荐智能体"""

    def __init__(self):
        # 优先级: Django settings > 环境变量 > 空字符串
        self.api_key = (
            getattr(settings, 'DEEPSEEK_API_KEY', None)
            or os.environ.get('DEEPSEEK_API_KEY', '')
        )
        self.base_url = getattr(settings, 'DEEPSEEK_BASE_URL', None) or \
            os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        self.model = getattr(settings, 'DEEPSEEK_MODEL', None) or \
            os.environ.get('DEEPSEEK_MODEL', 'deepseek-v4-flash')

        self._client = None

        if not self.api_key:
            logger.warning(
                "DEEPSEEK_API_KEY 未配置! 请在 settings.py 中添加 "
                "DEEPSEEK_API_KEY 或设置环境变量。智能体将以降级模式运行。"
            )

    @property
    def client(self):
        """延迟初始化 OpenAI 客户端 (兼容 DeepSeek API)"""
        if self._client is None and self.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
                logger.info(
                    f"DeepSeek 客户端初始化成功 | "
                    f"base_url={self.base_url} | model={self.model}"
                )
            except ImportError:
                logger.error("未安装 openai 库, 请执行: pip install openai")
                self._client = None
            except Exception as e:
                logger.error(f"DeepSeek 客户端初始化失败: {e}")
                self._client = None
        return self._client

    # -------------------------------------------------------------------------
    #  用户上下文采集 (Django ORM)
    # -------------------------------------------------------------------------

    def _fetch_user_context(self, userid: int) -> Dict:
        """
        从数据库采集用户上下文信息，用于注入 System Prompt

        Returns:
            dict with keys: userid, username, tags, tagsweight,
                            recent_history, recent_categories
        """
        from news_api.models import user as UserModel
        from news_api.models import history as HistoryModel
        from news_api.models import newsdetail as NewsDetailModel

        ctx = {
            'userid': userid,
            'username': '未知用户',
            'tags': '综合',
            'tagsweight': '{}',
            'recent_history': '无',
            'recent_categories': '无',
            'agent_summary_memory': '暂无长期记忆 (新用户或记忆尚未压缩)',
        }

        try:
            u = UserModel.objects.filter(userid=userid).first()
            if u:
                ctx['username'] = u.username or f'用户{userid}'
                ctx['tags'] = u.tags or '综合'
                ctx['tagsweight'] = u.tagsweight or '{}'
                ctx['agent_summary_memory'] = (
                    u.agent_summary_memory
                    or '暂无长期记忆 (新用户或记忆尚未压缩)'
                )

            # 最近 10 条浏览记录的新闻标题
            history_rows = HistoryModel.objects.filter(
                userid=userid
            ).order_by('-id')[:10]

            if history_rows.exists():
                news_ids = [h.history_newsid for h in history_rows]
                news_map = {
                    n.news_id: n
                    for n in NewsDetailModel.objects.filter(news_id__in=news_ids)
                }
                titles = []
                categories = set()
                for hid in news_ids:
                    nd = news_map.get(hid)
                    if nd:
                        titles.append(nd.title[:40])
                        if nd.category is not None:
                            cat_names = {
                                0: '美股', 1: '国内', 2: '国际', 3: '国际',
                                4: '体育', 5: '娱乐', 6: '军事',
                                7: '科技', 8: '财经', 9: '股市'
                            }
                            categories.add(cat_names.get(nd.category, str(nd.category)))

                ctx['recent_history'] = ' | '.join(titles[:10]) if titles else '无'
                ctx['recent_categories'] = ', '.join(sorted(categories)) if categories else '无'

        except Exception as e:
            logger.warning(f"采集用户上下文时出错 (userid={userid}): {e}")

        return ctx

    # -------------------------------------------------------------------------
    #  System Prompt 构建
    # -------------------------------------------------------------------------

    def _build_system_prompt(self, userid: int) -> str:
        """动态构建注入用户上下文的 System Prompt"""
        ctx = self._fetch_user_context(userid)
        return SYSTEM_PROMPT_TEMPLATE.format(**ctx)

    # -------------------------------------------------------------------------
    #  LLM 调用核心
    # -------------------------------------------------------------------------

    def _call_llm(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> Optional[str]:
        """
        调用 DeepSeek API 的 Chat Completion (非流式)

        Args:
            messages: OpenAI 格式的消息列表
            temperature: 温度参数
            max_tokens: 最大生成长度

        Returns:
            生成的文本, 失败时返回 None
        """
        if not self.client:
            logger.error("DeepSeek 客户端不可用, 无法调用 LLM")
            return None

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.9,
            )
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content:
                    logger.info(
                        f"DeepSeek API 调用成功 | "
                        f"model={self.model} | tokens={response.usage}"
                    )
                    return content
            logger.warning("DeepSeek API 返回空内容")
            return None
        except Exception as e:
            logger.error(f"DeepSeek API 调用失败: {e}")
            return None

    def _call_llm_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ):
        """
        调用 DeepSeek API 的 Chat Completion (流式)

        使用 stream=True, 逐块 yield Delta 文本。

        Args:
            messages: OpenAI 格式的消息列表
            temperature: 温度参数
            max_tokens: 最大生成长度

        Yields:
            str: 逐块生成的文本片段
        """
        if not self.client:
            logger.error("DeepSeek 客户端不可用, 无法流式调用 LLM")
            return

        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.9,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        yield delta.content
        except Exception as e:
            logger.error(f"DeepSeek 流式 API 调用失败: {e}")

    # =========================================================================
    #  公开接口
    # =========================================================================

    def chat_with_agent(self, userid: int, user_query: str) -> Dict:
        """
        对话式推荐交互

        接收用户的自然语言输入，利用 DeepSeek LLM 解析意图并返回推荐指导。

        Args:
            userid: 用户ID
            user_query: 用户自然语言输入

        Returns:
            {
                "status": "ok" | "fallback",
                "user_query": str,
                "llm_response": str,       # LLM 原始回复
                "parsed_intent": dict,      # 解析后的意图 (JSON 或空)
                "system_prompt_used": str,  # 诊断用
            }
        """
        result = {
            'status': 'fallback',
            'user_query': user_query,
            'llm_response': '',
            'parsed_intent': {},
            'system_prompt_used': '',
        }

        system_prompt = self._build_system_prompt(userid)
        result['system_prompt_used'] = system_prompt

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_query},
        ]

        llm_output = self._call_llm(messages)
        if llm_output:
            result['status'] = 'ok'
            result['llm_response'] = llm_output

            # 尝试从 LLM 回复中提取 JSON
            try:
                # 处理可能的 markdown 代码块包裹
                cleaned = llm_output.strip()
                if cleaned.startswith('```'):
                    cleaned = cleaned.split('\n', 1)[-1]
                    if cleaned.endswith('```'):
                        cleaned = cleaned[:-3]
                    cleaned = cleaned.strip()
                result['parsed_intent'] = json.loads(cleaned)
            except (json.JSONDecodeError, Exception):
                logger.info("LLM 回复非 JSON 格式, 保留原文")
                result['parsed_intent'] = {
                    'explanation': llm_output[:200]
                }
        else:
            result['llm_response'] = (
                '抱歉，智能推荐服务暂时不可用。请稍后再试，或使用搜索功能查找新闻。'
            )

        return result

    def generate_user_profile(self, userid: int) -> Dict:
        """
        利用 LLM 生成用户偏好画像

        Args:
            userid: 用户ID

        Returns:
            {
                "status": "ok" | "fallback",
                "userid": int,
                "profile_text": str,        # LLM 生成的画像描述
                "raw_context": dict,        # 原始用户数据
            }
        """
        result = {
            'status': 'fallback',
            'userid': userid,
            'profile_text': '',
            'raw_context': {},
        }

        ctx = self._fetch_user_context(userid)
        result['raw_context'] = ctx

        profile_prompt = (
            f"请根据以下用户数据，生成一份简洁的用户偏好画像分析（200字以内）：\n\n"
            f"用户ID: {ctx['userid']}\n"
            f"用户名: {ctx['username']}\n"
            f"兴趣标签: {ctx['tags']}\n"
            f"标签权重: {ctx['tagsweight']}\n"
            f"最近浏览: {ctx['recent_history']}\n"
            f"浏览类别: {ctx['recent_categories']}\n\n"
            f"请分析：1)主要兴趣领域 2)阅读偏好 3)推荐策略建议"
        )

        messages = [
            {
                'role': 'system',
                'content': (
                    '你是一个用户画像分析专家。请根据用户数据生成结构化的偏好分析报告。'
                    '用中文回复，控制在200字以内，分点列出。'
                )
            },
            {'role': 'user', 'content': profile_prompt},
        ]

        llm_output = self._call_llm(messages, temperature=0.5, max_tokens=512)
        if llm_output:
            result['status'] = 'ok'
            result['profile_text'] = llm_output
        else:
            # 降级: 用规则生成画像
            tags = ctx.get('tags', '综合')
            result['profile_text'] = (
                f"【降级模式 - 规则画像】\n"
                f"用户 {ctx['username']} 的兴趣标签: {tags}\n"
                f"最近浏览类别: {ctx['recent_categories']}\n"
                f"建议: 基于标签权重和历史浏览进行协同过滤推荐。"
            )
            result['status'] = 'fallback'

        return result


# =============================================================================
#  模块级入口函数 (供 Django views 调用)
# =============================================================================

def begin_deepseek_chat(userid: int, user_query: str) -> Dict:
    """
    对话式推荐入口

    Args:
        userid: 用户ID
        user_query: 用户自然语言输入

    Returns:
        dict: 包含 LLM 响应和解析结果
    """
    agent = DeepSeekRecommendAgent()
    return agent.chat_with_agent(userid, user_query)


def begin_deepseek_profile(userid: int) -> Dict:
    """
    用户画像生成入口

    Args:
        userid: 用户ID

    Returns:
        dict: 包含 LLM 生成的用户画像
    """
    agent = DeepSeekRecommendAgent()
    return agent.generate_user_profile(userid)
