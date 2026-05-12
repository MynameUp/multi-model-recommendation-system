# -*- coding: utf-8 -*-
"""
    Author: AI Assistant
    Desc: 新闻推荐智能体 - Django视图接口
"""
import json
from django.http import JsonResponse
from Recommend.NewsRecommendAgent import beginIntelligentRecommend


def intelligent_recommend(request):
    """
    智能推荐接口

    GET参数:
        user_input: 用户输入的自然语言
        userid: 用户ID
        top_n: 返回数量（可选，默认20）

    返回:
        JSON格式的推荐结果
    """
    if request.method == "GET":
        try:
            user_input = request.GET.get('user_input', '')
            userid = request.GET.get('userid', '')
            top_n = int(request.GET.get('top_n', 20))

            if not user_input or not userid:
                return JsonResponse({
                    "status": "400",
                    "message": "缺少必要参数: user_input 和 userid"
                })

            # 调用智能推荐引擎
            recommendations = beginIntelligentRecommend(user_input, userid, top_n)

            # 格式化返回数据
            formatted_results = []
            for item in recommendations:
                news = item['news']
                formatted_results.append({
                    'newsid': news['news_id'],
                    'title': news['title'],
                    'date': news['date'],
                    'pic_url': news['pic_url'],
                    'mainpage': news['mainpage'][:200] if news['mainpage'] else '',
                    'origin': news['origin'],
                    'category': news['category'],
                    'readnum': news['readnum'],
                    'comments': news['comments'],
                    'keywords': news['keywords'],
                    'hot_value': news['news_hot'],
                    'recommend_score': round(item['score'], 3),
                    'score_breakdown': {
                        'similarity': round(item['score_breakdown']['similarity'], 3),
                        'heat': round(item['score_breakdown']['heat'], 3),
                        'freshness': round(item['score_breakdown']['freshness'], 3),
                        'user_interest': round(item['score_breakdown']['user_interest'], 3),
                        'quality': round(item['score_breakdown']['quality'], 3),
                        'repetition_penalty': round(item['score_breakdown']['repetition_penalty'], 3)
                    },
                    'reason': item['reason']
                })

            return JsonResponse({
                "status": "200",
                "message": "Success",
                "data": {
                    'user_input': user_input,
                    'total': len(formatted_results),
                    'recommendations': formatted_results
                }
            })

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"智能推荐接口错误: {e}")
            return JsonResponse({
                "status": "500",
                "message": f"服务器错误: {str(e)}"
            })

    return JsonResponse({
        "status": "405",
        "message": "仅支持GET请求"
    })
