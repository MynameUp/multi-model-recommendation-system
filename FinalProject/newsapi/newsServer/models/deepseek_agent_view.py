# -*- coding: utf-8 -*-
"""
    Author: AI Architect
    Desc: DeepSeek 推荐智能体 — Django 视图接口

    提供以下 API 端点:
        1. POST /api/agent/deepseek/chat/       — 对话式推荐 (单轮意图解析)
        2. GET  /api/agent/deepseek/profile/    — 生成用户偏好画像
        3. POST /api/agent/deepseek/hybrid/     — 混合流水线推荐 (Intent→Recall→Rank→Explain)
        4. POST /api/agent/deepseek/clear/      — 一键清空对话记忆
"""

import json
import logging
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from Recommend.DeepSeekAgent import begin_deepseek_chat, begin_deepseek_profile
from Recommend.HybridPipeline import intelligent_chat_recommend, intelligent_chat_recommend_stream

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def deepseek_chat(request):
    """
    对话式推荐接口

    功能说明:
        接收用户自然语言输入, 利用 DeepSeek LLM 解析意图,
        返回推荐指导 (解析后的意图 + LLM 解释)。

    请求方法:
        POST

    请求参数 (JSON):
        {
            "userid": 123456,              // 必填: 用户ID
            "user_query": "推荐科技新闻",    // 必填: 用户自然语言输入
        }

    返回结果 (JSON):
        成功:
        {
            "status": "200",
            "message": "Success",
            "data": {
                "agent_status": "ok" | "fallback",
                "user_query": "...",
                "llm_response": "...",
                "parsed_intent": {
                    "keywords": [...],
                    "categories": [...],
                    "time_range_days": null,
                    "query_type": "general",
                    "primary_topic": "..."
                },
                "explanation": "..."
            }
        }
    """
    try:
        data = json.loads(request.body)
        userid = data.get('userid')
        user_query = data.get('user_query', '').strip()

        if not userid or not user_query:
            return JsonResponse({
                "status": "400",
                "message": "缺少必要参数: userid 和 user_query"
            }, status=400)

        # 安全转换 userid
        try:
            userid = int(userid)
        except (ValueError, TypeError):
            return JsonResponse({
                "status": "400",
                "message": "userid 必须为数字"
            }, status=400)

        logger.info(
            f"DeepSeek 对话请求 | userid={userid} | "
            f"query={user_query[:80]}"
        )

        result = begin_deepseek_chat(userid, user_query)

        # 构建前端友好的响应
        parsed = result.get('parsed_intent', {})
        return JsonResponse({
            "status": "200",
            "message": "Success",
            "data": {
                "agent_status": result['status'],
                "user_query": result['user_query'],
                "llm_response": result['llm_response'],
                "parsed_intent": parsed,
                "explanation": parsed.get('explanation', ''),
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            "status": "400",
            "message": "无效的 JSON 格式"
        }, status=400)
    except Exception as e:
        logger.error(f"DeepSeek 对话接口错误: {e}", exc_info=True)
        return JsonResponse({
            "status": "500",
            "message": f"服务器错误: {str(e)}"
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def deepseek_profile(request):
    """
    用户偏好画像生成接口

    功能说明:
        利用 DeepSeek LLM 分析用户历史阅读记录和兴趣标签,
        生成结构化的用户偏好画像报告。

    请求方法:
        GET

    请求参数:
        userid (必填): 用户ID

    返回结果 (JSON):
        成功:
        {
            "status": "200",
            "message": "Success",
            "data": {
                "agent_status": "ok" | "fallback",
                "userid": 123456,
                "profile_text": "用户画像分析报告...",
                "raw_context": {
                    "username": "...",
                    "tags": "...",
                    "recent_history": "...",
                    "recent_categories": "..."
                }
            }
        }
    """
    try:
        userid_raw = request.GET.get('userid', '')

        if not userid_raw:
            return JsonResponse({
                "status": "400",
                "message": "缺少必要参数: userid"
            }, status=400)

        try:
            userid = int(userid_raw)
        except (ValueError, TypeError):
            return JsonResponse({
                "status": "400",
                "message": "userid 必须为数字"
            }, status=400)

        logger.info(f"DeepSeek 画像请求 | userid={userid}")

        result = begin_deepseek_profile(userid)

        return JsonResponse({
            "status": "200",
            "message": "Success",
            "data": {
                "agent_status": result['status'],
                "userid": result['userid'],
                "profile_text": result['profile_text'],
                "raw_context": result['raw_context'],
            }
        })

    except Exception as e:
        logger.error(f"DeepSeek 画像接口错误: {e}", exc_info=True)
        return JsonResponse({
            "status": "500",
            "message": f"服务器错误: {str(e)}"
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def deepseek_hybrid_recommend(request):
    """
    混合流水线推荐接口 — Intent → Recall → Rank → Explain 全链路

    功能说明:
        1. DeepSeek LLM 解析用户意图 (带对话记忆)
        2. 数据库粗排召回候选新闻 (关键词+类别+时间)
        3. PromptMMInference 精排打分 (当前: 启发式桩)
        4. DeepSeek LLM 生成自然语言推荐解释
        5. 自动保存本轮对话到记忆库

    请求方法:
        POST

    请求参数 (JSON):
        {
            "userid": 123456,                   // 必填: 用户ID
            "user_query": "推荐今天的科技新闻",   // 必填: 用户自然语言输入
            "top_k": 20                         // 可选: 返回数量 (默认20)
        }

    返回结果 (JSON):
        {
            "status": "200",
            "data": {
                "agent_status": "ok" | "empty",
                "user_query": "...",
                "intent": {
                    "keywords": [...],
                    "categories": [...],
                    "primary_topic": "..."
                },
                "explanation": "为你找到15篇科技新闻...",
                "total": 15,
                "recommendations": [
                    {
                        "newsid": ..., "title": ..., "category_name": "科技",
                        "recommend_score": 0.85, "reason": "匹配'人工智能' | 高匹配度",
                        ...
                    }
                ],
                "pipeline_trace": {
                    "intent": "ok", "recall": "ok", "rank": "stub", "explain": "ok"
                }
            }
        }
    """
    try:
        data = json.loads(request.body)
        userid = data.get('userid')
        user_query = data.get('user_query', '').strip()
        top_k = int(data.get('top_k', 20))

        if not userid or not user_query:
            return JsonResponse({
                "status": "400",
                "message": "缺少必要参数: userid 和 user_query"
            }, status=400)

        try:
            userid = int(userid)
        except (ValueError, TypeError):
            return JsonResponse({
                "status": "400",
                "message": "userid 必须为数字"
            }, status=400)

        logger.info(
            f"Hybrid Pipeline 请求 | userid={userid} | "
            f"query={user_query[:80]} | top_k={top_k}"
        )

        result = intelligent_chat_recommend(userid, user_query, top_k)

        return JsonResponse({
            "status": "200",
            "message": "Success",
            "data": {
                "agent_status": result['status'],
                "user_query": result['user_query'],
                "intent": result['intent'],
                "explanation": result['explanation'],
                "total": result['total'],
                "recommendations": result['recommendations'],
                "pipeline_trace": result['pipeline_trace'],
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            "status": "400",
            "message": "无效的 JSON 格式"
        }, status=400)
    except Exception as e:
        logger.error(f"Hybrid Pipeline 接口错误: {e}", exc_info=True)
        return JsonResponse({
            "status": "500",
            "message": f"服务器错误: {str(e)}"
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def deepseek_clear_memory(request):
    """
    清空用户对话记忆接口

    功能说明:
        删除指定用户在 AgentConversation 表中的所有历史对话记录,
        实现"一键清空记忆"功能, 让用户开启全新话题。

    请求方法:
        POST

    请求参数 (JSON):
        {
            "userid": 123456  // 必填: 用户ID
        }

    返回结果 (JSON):
        {
            "status": "200",
            "message": "记忆已清空",
            "data": {"deleted_count": 15}
        }
    """
    try:
        data = json.loads(request.body)
        userid = data.get('userid')

        if not userid:
            return JsonResponse({
                "status": "400",
                "message": "缺少必要参数: userid"
            }, status=400)

        try:
            userid = int(userid)
        except (ValueError, TypeError):
            return JsonResponse({
                "status": "400",
                "message": "userid 必须为数字"
            }, status=400)

        from news_api.models import AgentConversation
        deleted_count, _ = AgentConversation.objects.filter(
            userid=userid
        ).delete()

        logger.info(f"清空对话记忆 | userid={userid} | deleted={deleted_count}")

        return JsonResponse({
            "status": "200",
            "message": "记忆已清空，我们可以开启全新的话题啦！",
            "data": {"deleted_count": deleted_count}
        })

    except json.JSONDecodeError:
        return JsonResponse({
            "status": "400",
            "message": "无效的 JSON 格式"
        }, status=400)
    except Exception as e:
        logger.error(f"清空记忆接口错误: {e}", exc_info=True)
        return JsonResponse({
            "status": "500",
            "message": f"服务器错误: {str(e)}"
        }, status=500)


# =============================================================================
#  Phase 4.1: SSE 流式推荐端点
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def deepseek_hybrid_recommend_stream(request):
    """
    混合流水线推荐 — SSE 流式版本

    使用 StreamingHttpResponse 逐块返回数据:
      第1块: {"type":"phase1","intent":{...},"recommendations":[...],...}
      后续块: {"type":"text","content":"chunk..."}
      结束块: {"type":"done","total":N}

    前端使用 fetch + ReadableStream 逐行解析, 实现:
      - 新闻卡片即时渲染 (收到 phase1 后)
      - 解释文本打字机效果 (收到 text 块后逐字追加)

    请求参数 (JSON):
        {"userid": 123456, "user_query": "推荐科技新闻", "top_k": 20}
    """
    try:
        data = json.loads(request.body)
        userid = data.get('userid')
        user_query = data.get('user_query', '').strip()
        top_k = int(data.get('top_k', 20))

        if not userid or not user_query:
            return JsonResponse({
                "status": "400", "message": "缺少必要参数: userid 和 user_query"
            }, status=400)

        try:
            userid = int(userid)
        except (ValueError, TypeError):
            return JsonResponse({
                "status": "400", "message": "userid 必须为数字"
            }, status=400)

        logger.info(
            f"SSE Stream 请求 | userid={userid} | query={user_query[:80]}"
        )

        # 创建流式生成器
        stream_gen = intelligent_chat_recommend_stream(userid, user_query, top_k)

        response = StreamingHttpResponse(
            stream_gen,
            content_type='text/event-stream; charset=utf-8',
        )
        response['Cache-Control'] = 'no-cache, no-transform'
        response['X-Accel-Buffering'] = 'no'
        response['Access-Control-Allow-Origin'] = '*'
        return response

    except json.JSONDecodeError:
        return JsonResponse({
            "status": "400", "message": "无效的 JSON 格式"
        }, status=400)
    except Exception as e:
        logger.error(f"SSE Stream 接口错误: {e}", exc_info=True)
        return JsonResponse({
            "status": "500",
            "message": f"服务器错误: {str(e)}"
        }, status=500)
