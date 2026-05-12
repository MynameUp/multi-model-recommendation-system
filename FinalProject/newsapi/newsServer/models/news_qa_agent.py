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
    新闻问答接口（支持LLM配置）
    
    功能说明：
        接收用户关于某篇新闻的问题，使用RAG技术检索相关新闻，
        并通过LLM生成智能回答，同时返回相关新闻列表。
    
    请求方法：
        POST
    
    请求参数（JSON格式）：
        {
            "userId": 1,                    # 必填：用户ID
            "newsId": 10086,                # 必填：新闻ID
            "question": "这篇新闻讲了什么？",  # 必填：用户问题
            "llmType": "dashscope",         # 可选：LLM类型，默认fallback
            "apiKey": "sk-your-key"         # 可选：API密钥（用于API类型的LLM）
        }
    
    LLM类型说明：
        - fallback: 规则-based降级方案（默认，无需配置）
        - dashscope: 阿里云通义千问API（需要apiKey）
        - zhipuai: 智谱AI API（需要apiKey）
        - chatglm: ChatGLM本地模型（需要GPU）
    
    返回结果（JSON格式）：
        成功时：
        {
            "status": "200",
            "message": "Success",
            "data": {
                "answer": "这篇新闻主要讨论了...",
                "relatedNews": [
                    {
                        "id": 10087,
                        "title": "相关新闻标题",
                        "similarity": 0.82,
                        "date": "2024-01-15",
                        "origin": "新华网"
                    }
                ]
            }
        }
        
        失败时：
        {
            "status": "400" 或 "500",
            "message": "错误信息"
        }
    
    使用示例：
        curl -X POST http://localhost:8000/api/agent/news-qa/ \
          -H "Content-Type: application/json" \
          -d '{
            "userId": 1,
            "newsId": 10086,
            "question": "这篇新闻的核心观点是什么？",
            "llmType": "fallback"
          }'
    """
    try:
        # 解析请求体中的JSON数据
        data = json.loads(request.body)
        
        # 提取必需参数
        user_id = data.get('userId')
        news_id = data.get('newsId')
        question = data.get('question', '').strip()
        
        # 提取可选参数
        llm_type = data.get('llmType', 'fallback')
        api_key = data.get('apiKey', '')
        
        # 参数验证
        if not user_id or not news_id or not question:
            logger.warning(f"缺少必要参数 - userId:{user_id}, newsId:{news_id}, question:{question[:20]}")
            return JsonResponse({
                "status": "400",
                "message": "缺少必要参数: userId, newsId, question"
            }, status=400)
        
        # 记录请求日志
        logger.info(f"收到问答请求 - 用户:{user_id}, 新闻:{news_id}, LLM:{llm_type}, 问题:{question[:50]}...")
        
        # 构建LLM配置参数
        llm_kwargs = {}
        if llm_type in ['dashscope', 'zhipuai'] and api_key:
            llm_kwargs['api_key'] = api_key
            logger.info(f"使用API密钥调用LLM: {llm_type}")
        
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
        error_details = traceback.format_exc()
        logger.error(f"详细错误信息:\n{error_details}")
        return JsonResponse({
            "status": "500",
            "message": f"服务器错误: {str(e)}",
            "debug_info": error_details if settings.DEBUG else None
        }, status=500)


@require_http_methods(["GET"])
def init_vectors(request):
    """
    初始化新闻向量接口
    
    功能说明：
        为数据库中所有未向量化的新闻生成向量表示，
        用于后续的语义检索和相似度计算。
    
    请求方法：
        GET
    
    请求参数（URL参数）：
        batch_size: 批处理大小（可选，默认100）
                   建议值：小内存机器50，大内存机器200
    
    返回结果（JSON格式）：
        成功时：
        {
            "status": "200",
            "message": "Success",
            "data": {
                "success": true,
                "message": "向量初始化完成",
                "total": 1000,
                "success_count": 980,
                "failed_count": 20
            }
        }
        
        失败时：
        {
            "status": "500",
            "message": "服务器错误: 错误详情"
        }
    
    使用示例：
        # 默认批处理大小
        curl "http://localhost:8000/api/agent/init-vectors/"
        
        # 自定义批处理大小
        curl "http://localhost:8000/api/agent/init-vectors/?batch_size=50"
    
    注意事项：
        1. 首次运行需要较长时间（取决于新闻数量）
        2. 建议在低峰期执行
        3. 可以多次调用，只会处理未向量化的新闻
        4. 进度会记录在日志中
    """
    try:
        # 获取批处理大小参数
        batch_size = int(request.GET.get('batch_size', 100))
        
        # 参数验证
        if batch_size < 1 or batch_size > 1000:
            return JsonResponse({
                "status": "400",
                "message": "batch_size必须在1-1000之间"
            }, status=400)
        
        logger.info(f"开始初始化新闻向量，批处理大小: {batch_size}")
        
        # 创建向量服务实例
        service = NewsVectorService()
        
        try:
            # 执行初始化
            result = service.initialize_all_vectors(batch_size)
            
            # 记录完成日志
            logger.info(f"向量初始化完成: {result}")
            
            # 返回响应
            return JsonResponse({
                "status": "200" if result['success'] else "500",
                "message": result['message'],
                "data": result
            })
            
        finally:
            # 确保资源被释放
            service.close()
        
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        return JsonResponse({
            "status": "400",
            "message": f"参数错误: {str(e)}"
        }, status=400)
        
    except Exception as e:
        logger.error(f"初始化向量接口错误: {e}", exc_info=True)
        return JsonResponse({
            "status": "500",
            "message": f"服务器错误: {str(e)}"
        }, status=500)


@require_http_methods(["GET"])
def vectorization_status(request):
    """
    获取向量化状态接口
    
    功能说明：
        查询当前新闻库的向量化进度，包括总新闻数、
        已向量化的新闻数、待处理的新闻数和完成率。
    
    请求方法：
        GET
    
    请求参数：
        无
    
    返回结果（JSON格式）：
        {
            "status": "200",
            "data": {
                "total_news": 5000,           # 新闻总数
                "vectorized_news": 4500,      # 已向量化的新闻数
                "pending_news": 500,          # 待处理的新闻数
                "completion_rate": 90.0       # 完成率（百分比）
            }
        }
    
    使用示例：
        curl "http://localhost:8000/api/agent/vector-status/"
    
    应用场景：
        1. 监控向量化进度
        2. 判断是否需要继续初始化
        3. 系统健康检查
    """
    try:
        logger.info("查询向量化状态")
        
        # 创建向量服务实例
        service = NewsVectorService()
        
        try:
            # 获取状态信息
            status = service.get_vectorization_status()
            
            logger.info(f"向量化状态: {status}")
            
            # 返回响应
            return JsonResponse({
                "status": "200",
                "data": status
            })
            
        finally:
            # 确保资源被释放
            service.close()
        
    except Exception as e:
        logger.error(f"获取向量化状态接口错误: {e}", exc_info=True)
        return JsonResponse({
            "status": "500",
            "message": f"服务器错误: {str(e)}"
        }, status=500)


@require_http_methods(["GET"])
def user_qa_history(request):
    """
    获取用户问答历史接口
    
    功能说明：
        查询指定用户的问答历史记录，包括问题和答案，
        同时返回用户的问答统计数据。
    
    请求方法：
        GET
    
    请求参数（URL参数）：
        userId: 用户ID（必填）
        limit: 返回记录数量限制（可选，默认50，最大200）
    
    返回结果（JSON格式）：
        {
            "status": "200",
            "data": {
                "history": [
                    {
                        "id": 1,
                        "news_id": 10086,
                        "question": "这篇新闻讲了什么？",
                        "answer": "这篇新闻主要讨论了...",
                        "time": "2024-01-15 14:30:00"
                    }
                ],
                "stats": {
                    "user_id": 1,
                    "total_questions": 150,
                    "recent_7days_questions": 20,
                    "unique_news_asked": 45
                }
            }
        }
    
    使用示例：
        # 获取最近50条记录
        curl "http://localhost:8000/api/agent/user-qa-history/?userId=1"
        
        # 获取最近100条记录
        curl "http://localhost:8000/api/agent/user-qa-history/?userId=1&limit=100"
    
    应用场景：
        1. 用户个人中心展示问答历史
        2. 分析用户兴趣和行为
        3. 优化推荐算法
    """
    try:
        # 获取请求参数
        user_id = request.GET.get('userId')
        limit = int(request.GET.get('limit', 50))
        
        # 参数验证
        if not user_id:
            return JsonResponse({
                "status": "400",
                "message": "缺少参数: userId"
            }, status=400)
        
        # 限制最大值，防止过度查询
        if limit < 1 or limit > 200:
            limit = 50
        
        logger.info(f"查询用户问答历史 - 用户:{user_id}, 限制:{limit}")
        
        # 获取问答历史
        history = QAHistoryService.get_user_history(int(user_id), limit)
        
        # 获取统计数据
        stats = QAHistoryService.get_user_qa_stats(int(user_id))
        
        logger.info(f"查询完成 - 返回{len(history)}条记录")
        
        # 返回响应
        return JsonResponse({
            "status": "200",
            "data": {
                "history": history,
                "stats": stats
            }
        })
        
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        return JsonResponse({
            "status": "400",
            "message": f"参数错误: {str(e)}"
        }, status=400)
        
    except Exception as e:
        logger.error(f"获取用户问答历史接口错误: {e}", exc_info=True)
        return JsonResponse({
            "status": "500",
            "message": f"服务器错误: {str(e)}"
        }, status=500)


@require_http_methods(["GET"])
def news_qa_stats(request):
    """
    获取新闻问答统计接口
    
    功能说明：
        查询指定新闻的问答统计数据，包括总问答次数
        和最常问的问题列表。
    
    请求方法：
        GET
    
    请求参数（URL参数）：
        newsId: 新闻ID（必填）
    
    返回结果（JSON格式）：
        {
            "status": "200",
            "data": {
                "news_id": 10086,
                "total_questions": 50,
                "frequent_questions": [
                    {
                        "question": "这篇新闻讲了什么？",
                        "count": 15
                    },
                    {
                        "question": "关键人物有哪些？",
                        "count": 10
                    }
                ]
            }
        }
    
    使用示例：
        curl "http://localhost:8000/api/agent/news-qa-stats/?newsId=10086"
    
    应用场景：
        1. 新闻详情页展示问答统计
        2. 分析用户关注的热点问题
        3. 优化新闻内容和标签
    """
    try:
        # 获取请求参数
        news_id = request.GET.get('newsId')
        
        # 参数验证
        if not news_id:
            return JsonResponse({
                "status": "400",
                "message": "缺少参数: newsId"
            }, status=400)
        
        logger.info(f"查询新闻问答统计 - 新闻:{news_id}")
        
        # 获取统计数据
        stats = QAHistoryService.get_news_qa_stats(int(news_id))
        
        logger.info(f"查询完成 - 总问答数:{stats['total_questions']}")
        
        # 返回响应
        return JsonResponse({
            "status": "200",
            "data": stats
        })
        
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        return JsonResponse({
            "status": "400",
            "message": f"参数错误: {str(e)}"
        }, status=400)
        
    except Exception as e:
        logger.error(f"获取新闻问答统计接口错误: {e}", exc_info=True)
        return JsonResponse({
            "status": "500",
            "message": f"服务器错误: {str(e)}"
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def cleanup_qa_data(request):
    """
    清理过期问答数据接口
    
    功能说明：
        删除超过指定天数的问答历史记录，释放数据库空间。
        这是一个管理员功能，应谨慎使用。
    
    请求方法：
        POST
    
    请求参数（JSON格式）：
        {
            "days": 90  # 保留最近多少天的记录（可选，默认90天）
        }
    
    返回结果（JSON格式）：
        成功时：
        {
            "status": "200",
            "data": {
                "success": true,
                "deleted_count": 1000,
                "retention_days": 90
            }
        }
        
        失败时：
        {
            "status": "500",
            "data": {
                "success": false,
                "deleted_count": 0,
                "retention_days": 90,
                "error": "错误详情"
            }
        }
    
    使用示例：
        # 保留最近90天的数据
        curl -X POST http://localhost:8000/api/agent/cleanup-qa-data/ \
          -H "Content-Type: application/json" \
          -d '{"days": 90}'
        
        # 保留最近30天的数据
        curl -X POST http://localhost:8000/api/agent/cleanup-qa-data/ \
          -H "Content-Type: application/json" \
          -d '{"days": 30}'
    
    注意事项：
        1. 此操作不可逆，删除的数据无法恢复
        2. 建议定期执行（如每月一次）
        3. 建议在低峰期执行
        4. 删除前建议备份重要数据
    """
    try:
        # 解析请求体
        data = json.loads(request.body)
        days = int(data.get('days', 90))
        
        # 参数验证
        if days < 1 or days > 365:
            return JsonResponse({
                "status": "400",
                "message": "days必须在1-365之间"
            }, status=400)
        
        logger.info(f"开始清理过期问答数据，保留{days}天内的记录")
        
        # 执行清理
        result = QAHistoryService.cleanup_old_data(days)
        
        if result['success']:
            logger.info(f"清理完成 - 删除{result['deleted_count']}条记录")
        else:
            logger.error(f"清理失败: {result.get('error')}")
        
        # 返回响应
        return JsonResponse({
            "status": "200" if result['success'] else "500",
            "data": result
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        return JsonResponse({
            "status": "400",
            "message": "无效的JSON格式"
        }, status=400)
        
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        return JsonResponse({
            "status": "400",
            "message": f"参数错误: {str(e)}"
        }, status=400)
        
    except Exception as e:
        logger.error(f"清理问答数据接口错误: {e}", exc_info=True)
        return JsonResponse({
            "status": "500",
            "message": f"服务器错误: {str(e)}"
        }, status=500)