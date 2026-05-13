"""
    Author: AI Assistant
    Desc: 新闻问答智能体 - Django视图接口（完整版）
    
    提供以下API接口：
    1. POST /api/agent/news-qa/ - 新闻问答接口
    2. GET /api/agent/init-vectors/ - 初始化新闻向量
    3. GET /api/agent/vector-status/ - 查看向量化状态
    4. GET /api/agent/user-qa-history/ - 获取用户问答历史
    5. GET /api/agent/news-qa-stats/ - 获取新闻问答统计
    6. POST /api/agent/cleanup-qa-data/ - 清理过期问答数据
"""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import traceback
from django.conf import settings
# 导入问答智能体核心功能
from Recommend.NewsQAAgent import beginNewsQA, initNewsVectors

# 导入业务逻辑服务层
from Recommend.NewsQAServices import NewsVectorService, QAHistoryService

# 配置日志
logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def news_qa(request):
    """
    新闻问答接口（仅支持魔塔社区API）

    功能说明：
        接收用户关于某篇新闻的问题，使用RAG技术检索相关新闻，
        并通过魔塔社区LLM生成智能回答，同时返回相关新闻列表。

    请求方法：
        POST

    请求参数（JSON格式）：
        {
            "userId": 1,                    # 必填：用户ID
            "newsId": 10086,                # 必填：新闻ID
            "question": "这篇新闻讲了什么？",  # 必填：用户问题
            "llmType": "modelscope",        # 可选：固定为 modelscope
            "apiToken": "ms-xxx"            # 可选：魔塔社区Token（如果后端未配置）
        }

    返回结果（JSON格式）：
        成功时：
        {
            "status": "200",
            "message": "Success",
            "data": {
                "answer": "这篇新闻主要讨论了...",
                "relatedNews": [...]
            }
        }
    """
    try:
        # 解析请求体中的JSON数据
        data = json.loads(request.body)

        # 提取必需参数
        user_id = data.get('userId')
        news_id = data.get('newsId')
        question = data.get('question', '').strip()

        # 强制使用魔塔社区，忽略前端传入的llmType
        llm_type = 'modelscope'

        # 提取可选参数
        api_token = data.get('apiToken', '')

        # 参数验证
        if not user_id or not news_id or not question:
            logger.warning(f"缺少必要参数 - userId:{user_id}, newsId:{news_id}, question:{question[:20]}")
            return JsonResponse({
                "status": "400",
                "message": "缺少必要参数: userId, newsId, question"
            }, status=400)

        # 记录请求日志
        logger.info(f"收到问答请求 - 用户:{user_id}, 新闻:{news_id}, LLM:魔塔社区, 问题:{question[:50]}...")

        # 从配置文件获取Token（优先）或使用前端传入的Token
        from Recommend.LLMConfig import MODELSCOPE_CONFIG
        if not api_token or api_token == 'your_modelscope_token_here':
            api_token = MODELSCOPE_CONFIG.get('api_token', '')

        # 构建LLM配置参数
        llm_kwargs = {}
        if api_token and api_token != 'your_modelscope_token_here':
            llm_kwargs['api_token'] = api_token
            llm_kwargs['model_name'] = MODELSCOPE_CONFIG.get('default_model', 'qwen/Qwen-7B-Chat')
            logger.info(f"使用魔塔社区API调用LLM")
        else:
            logger.warning("未配置魔塔社区Token，将使用降级方案")
            llm_type = 'fallback'

        # 调用问答智能体生成答案
        result = beginNewsQA(
            user_id=int(user_id),
            news_id=int(news_id),
            question=question,
            llm_type=llm_type,
            **llm_kwargs
        )

        # 记录响应日志
        logger.info(f"问答完成 - 返回{len(result.get('relatedNews', []))}条相关新闻")

        # 返回成功响应
        return JsonResponse({
            "status": "200",
            "message": "Success",
            "data": result
        })

    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        return JsonResponse({
            "status": "400",
            "message": "无效的JSON格式"
        }, status=400)

    except ValueError as e:
        logger.error(f"参数值错误: {e}")
        return JsonResponse({
            "status": "400",
            "message": f"参数错误: {str(e)}"
        }, status=400)

    except Exception as e:
        logger.error(f"新闻问答接口错误: {e}", exc_info=True)
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"详细错误信息:\n{error_details}")
        return JsonResponse({
            "status": "500",
            "message": f"服务器错误: {str(e)}",
            "error_type": type(e).__name__,
        }, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def init_vectors(request):
    """
    初始化新闻向量接口

    功能说明：
        为数据库中所有未向量化的新闻生成向量表示，
        用于后续的语义搜索和智能推荐。

    请求方法：
        GET 或 POST

    请求参数：
        batch_size (可选): 批处理大小，默认100

    返回结果（JSON格式）：
        {
            "status": "200",
            "message": "Success",
            "data": {
                "total": 100,
                "success_count": 98,
                "failed_count": 2,
                "message": "向量初始化完成"
            }
        }
    """
    try:
        # 获取批处理大小参数
        if request.method == 'POST':
            data = json.loads(request.body)
            batch_size = int(data.get('batch_size', 100))
        else:
            batch_size = int(request.GET.get('batch_size', 100))

        logger.info(f"开始初始化新闻向量，批处理大小: {batch_size}")

        # 调用服务层执行初始化
        vector_service = NewsVectorService()
        result = vector_service.initialize_all_vectors(batch_size=batch_size)
        vector_service.close()

        logger.info(f"向量初始化完成: {result}")

        return JsonResponse({
            "status": "200",
            "message": "Success",
            "data": result
        })

    except Exception as e:
        logger.error(f"初始化向量接口错误: {e}", exc_info=True)
        return JsonResponse({
            "status": "500",
            "message": f"服务器错误: {str(e)}",
            "error_type": type(e).__name__
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def vectorization_status(request):
    """
    获取向量化状态统计接口

    功能说明：
        返回数据库中新闻的向量化进度统计信息，
        包括总新闻数、已向量化的数量、待处理数量和完成率。

    请求方法：
        GET

    返回结果（JSON格式）：
        {
            "status": "200",
            "message": "Success",
            "data": {
                "total_news": 1000,
                "vectorized_news": 950,
                "pending_news": 50,
                "completion_rate": 95.0
            }
        }
    """
    try:
        logger.info("查询向量化状态")

        # 调用服务层获取状态
        vector_service = NewsVectorService()
        status = vector_service.get_vectorization_status()
        vector_service.close()

        return JsonResponse({
            "status": "200",
            "message": "Success",
            "data": status
        })

    except Exception as e:
        logger.error(f"获取向量化状态接口错误: {e}", exc_info=True)
        return JsonResponse({
            "status": "500",
            "message": f"服务器错误: {str(e)}",
            "error_type": type(e).__name__
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def user_qa_history(request):
    """
    获取用户问答历史接口

    功能说明：
        返回指定用户的问答历史记录，按时间倒序排列。

    请求方法：
        GET

    请求参数：
        userId (必填): 用户ID
        limit (可选): 返回数量限制，默认50

    返回结果（JSON格式）：
        {
            "status": "200",
            "message": "Success",
            "data": {
                "history": [...],
                "stats": {...}
            }
        }
    """
    try:
        # 获取参数
        user_id = request.GET.get('userId')
        limit = int(request.GET.get('limit', 50))

        # 参数验证
        if not user_id:
            return JsonResponse({
                "status": "400",
                "message": "缺少必要参数: userId"
            }, status=400)

        logger.info(f"查询用户问答历史 - 用户:{user_id}, 限制:{limit}")

        # 调用服务层获取历史
        history = QAHistoryService.get_user_history(user_id=int(user_id), limit=limit)

        # 获取统计数据
        stats = QAHistoryService.get_user_qa_stats(user_id=int(user_id))

        logger.info(f"查询结果 - 历史记录数:{len(history)}, 统计数据:{stats}")

        # 返回包含history和stats的结构
        return JsonResponse({
            "status": "200",
            "message": "Success",
            "data": {
                "history": history,
                "stats": stats
            }
        })

    except Exception as e:
        logger.error(f"获取用户问答历史接口错误: {e}", exc_info=True)
        return JsonResponse({
            "status": "500",
            "message": f"服务器错误: {str(e)}",
            "error_type": type(e).__name__
        }, status=500)



@csrf_exempt
@require_http_methods(["GET"])
def news_qa_stats(request):
    """
    获取新闻问答统计接口

    功能说明：
        返回指定新闻的问答统计信息，包括问答次数、参与用户数等。

    请求方法：
        GET

    请求参数：
        newsId (必填): 新闻ID

    返回结果（JSON格式）：
        {
            "status": "200",
            "message": "Success",
            "data": {
                "news_id": 10086,
                "total_questions": 25,
                "unique_users": 10,
                "last_question_time": "2024-01-01 12:00:00"
            }
        }
    """
    try:
        # 获取参数
        news_id = request.GET.get('newsId')

        # 参数验证
        if not news_id:
            return JsonResponse({
                "status": "400",
                "message": "缺少必要参数: newsId"
            }, status=400)

        logger.info(f"查询新闻问答统计 - 新闻:{news_id}")

        # 调用服务层获取统计
        stats = QAHistoryService.get_news_qa_stats(news_id=int(news_id))

        return JsonResponse({
            "status": "200",
            "message": "Success",
            "data": stats
        })

    except Exception as e:
        logger.error(f"获取新闻问答统计接口错误: {e}", exc_info=True)
        return JsonResponse({
            "status": "500",
            "message": f"服务器错误: {str(e)}",
            "error_type": type(e).__name__
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def cleanup_qa_data(request):
    """
    清理过期问答数据接口

    功能说明：
        删除超过指定天数的问答历史记录，释放数据库空间。

    请求方法：
        POST

    请求参数（JSON格式）：
        {
            "days": 90  # 保留天数，默认90天
        }

    返回结果（JSON格式）：
        {
            "status": "200",
            "message": "Success",
            "data": {
                "deleted_count": 150,
                "retention_days": 90
            }
        }
    """
    try:
        # 解析请求参数
        data = json.loads(request.body)
        days = int(data.get('days', 90))

        logger.info(f"开始清理过期问答数据，保留天数: {days}")

        # 调用服务层执行清理
        result = QAHistoryService.cleanup_old_data(days=days)

        if result['success']:
            logger.info(f"清理完成，删除了 {result['deleted_count']} 条记录")
            return JsonResponse({
                "status": "200",
                "message": "Success",
                "data": {
                    "deleted_count": result['deleted_count'],
                    "retention_days": result['retention_days']
                }
            })
        else:
            logger.error(f"清理失败: {result.get('error')}")
            return JsonResponse({
                "status": "500",
                "message": f"清理失败: {result.get('error')}"
            }, status=500)

    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        return JsonResponse({
            "status": "400",
            "message": "无效的JSON格式"
        }, status=400)

    except Exception as e:
        logger.error(f"清理问答数据接口错误: {e}", exc_info=True)
        return JsonResponse({
            "status": "500",
            "message": f"服务器错误: {str(e)}",
            "error_type": type(e).__name__
        }, status=500)

