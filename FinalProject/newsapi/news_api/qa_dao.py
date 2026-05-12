"""
    Author: AI Assistant
    Desc: 新闻问答数据访问层 - 提供数据库操作的封装
"""
import logging
import json
from typing import List, Dict, Optional

from django.utils import timezone
from news_api.qa_models import NewsVector, QAHistory

logger = logging.getLogger(__name__)


class NewsVectorDAO:
    """新闻向量数据访问对象"""

    @staticmethod
    def save_or_update_vector(news_id: int, vector_data: list) -> bool:
        """
        保存或更新新闻向量

        Args:
            news_id: 新闻ID
            vector_data: 向量数据列表

        Returns:
            bool: 是否成功保存
        """
        try:
            vector_json = json.dumps(vector_data)

            # 使用update_or_create避免重复
            obj, created = NewsVector.objects.update_or_create(
                news_id=news_id,
                defaults={
                    'vector_data': vector_json,
                    'updated_at': timezone.now()
                }
            )

            action = "创建" if created else "更新"
            logger.info(f"{action}新闻向量成功: news_id={news_id}")
            return True

        except Exception as e:
            logger.error(f"保存新闻向量失败: news_id={news_id}, error={e}")
            return False

    @staticmethod
    def get_vector(news_id: int) -> Optional[list]:
        """
        获取新闻向量

        Args:
            news_id: 新闻ID

        Returns:
            list: 向量数据列表，不存在则返回None
        """
        try:
            obj = NewsVector.objects.get(news_id=news_id)
            return obj.get_vector()
        except NewsVector.DoesNotExist:
            logger.warning(f"新闻向量不存在: news_id={news_id}")
            return None
        except Exception as e:
            logger.error(f"获取新闻向量失败: news_id={news_id}, error={e}")
            return None

    @staticmethod
    def batch_save_vectors(vectors_dict: Dict[int, list]) -> int:
        """
        批量保存新闻向量

        Args:
            vectors_dict: {news_id: vector_data} 字典

        Returns:
            int: 成功保存的数量
        """
        success_count = 0

        for news_id, vector_data in vectors_dict.items():
            if NewsVectorDAO.save_or_update_vector(news_id, vector_data):
                success_count += 1

        logger.info(f"批量保存向量完成: 成功{success_count}/{len(vectors_dict)}")
        return success_count

    @staticmethod
    def get_all_vectors(limit: int = None) -> List[Dict]:
        """
        获取所有新闻向量

        Args:
            limit: 限制返回数量

        Returns:
            list: 包含news_id和vector_data的字典列表
        """
        try:
            queryset = NewsVector.objects.all().order_by('-created_at')

            if limit:
                queryset = queryset[:limit]

            result = []
            for obj in queryset:
                vector = obj.get_vector()
                if vector:
                    result.append({
                        'news_id': obj.news_id,
                        'vector_data': vector,
                        'created_at': obj.created_at
                    })

            return result

        except Exception as e:
            logger.error(f"获取所有向量失败: error={e}")
            return []

    @staticmethod
    def delete_vector(news_id: int) -> bool:
        """
        删除新闻向量

        Args:
            news_id: 新闻ID

        Returns:
            bool: 是否成功删除
        """
        try:
            deleted_count, _ = NewsVector.objects.filter(news_id=news_id).delete()
            if deleted_count > 0:
                logger.info(f"删除新闻向量成功: news_id={news_id}")
                return True
            else:
                logger.warning(f"新闻向量不存在，无需删除: news_id={news_id}")
                return False
        except Exception as e:
            logger.error(f"删除新闻向量失败: news_id={news_id}, error={e}")
            return False

    @staticmethod
    def get_vector_count() -> int:
        """
        获取向量总数

        Returns:
            int: 向量总数
        """
        try:
            return NewsVector.objects.count()
        except Exception as e:
            logger.error(f"获取向量总数失败: error={e}")
            return 0


class QAHistoryDAO:
    """问答历史数据访问对象"""

    @staticmethod
    def save_qa_record(user_id: int, news_id: int, question: str, answer: str) -> bool:
        """
        保存问答记录

        Args:
            user_id: 用户ID
            news_id: 新闻ID
            question: 用户问题
            answer: 系统回答

        Returns:
            bool: 是否成功保存
        """
        try:
            QAHistory.objects.create(
                userid=user_id,
                newsid=news_id,
                question=question,
                answer=answer,
                time=timezone.now()
            )
            logger.debug(f"保存问答记录成功: user={user_id}, news={news_id}")
            return True

        except Exception as e:
            logger.error(f"保存问答记录失败: user={user_id}, news={news_id}, error={e}")
            return False

    @staticmethod
    def get_user_history(user_id: int, limit: int = 50) -> List[Dict]:
        """
        获取用户的问答历史

        Args:
            user_id: 用户ID
            limit: 返回记录数量限制

        Returns:
            list: 问答历史记录列表
        """
        try:
            queryset = QAHistory.objects.filter(
                userid=user_id
            ).order_by('-time')[:limit]

            result = []
            for record in queryset:
                result.append({
                    'id': record.id,
                    'news_id': record.newsid,
                    'question': record.question,
                    'answer': record.answer,
                    'time': record.time.strftime('%Y-%m-%d %H:%M:%S')
                })

            return result

        except Exception as e:
            logger.error(f"获取用户问答历史失败: user={user_id}, error={e}")
            return []

    @staticmethod
    def get_news_qa_history(news_id: int, limit: int = 100) -> List[Dict]:
        """
        获取某篇新闻的问答历史

        Args:
            news_id: 新闻ID
            limit: 返回记录数量限制

        Returns:
            list: 问答历史记录列表
        """
        try:
            queryset = QAHistory.objects.filter(
                newsid=news_id
            ).order_by('-time')[:limit]

            result = []
            for record in queryset:
                result.append({
                    'id': record.id,
                    'user_id': record.userid,
                    'question': record.question,
                    'answer': record.answer,
                    'time': record.time.strftime('%Y-%m-%d %H:%M:%S')
                })

            return result

        except Exception as e:
            logger.error(f"获取新闻问答历史失败: news={news_id}, error={e}")
            return []

    @staticmethod
    def get_news_qa_stats(news_id: int) -> Dict:
        """
        获取某篇新闻的问答统计信息

        Args:
            news_id: 新闻ID

        Returns:
            dict: 统计信息
        """
        try:
            # 使用Django ORM的聚合功能
            from django.db.models import Count

            # 总问答数
            total_count = QAHistory.objects.filter(newsid=news_id).count()

            # 最常问的问题（简化版：按问题文本分组统计）
            frequent_questions = QAHistory.objects.filter(
                newsid=news_id
            ).values('question').annotate(
                count=Count('id')
            ).order_by('-count')[:5]

            return {
                'news_id': news_id,
                'total_questions': total_count,
                'frequent_questions': [
                    {
                        'question': item['question'],
                        'count': item['count']
                    }
                    for item in frequent_questions
                ]
            }

        except Exception as e:
            logger.error(f"获取新闻问答统计失败: news={news_id}, error={e}")
            return {
                'news_id': news_id,
                'total_questions': 0,
                'frequent_questions': []
            }

    @staticmethod
    def get_user_qa_stats(user_id: int) -> Dict:
        """
        获取用户的问答统计信息

        Args:
            user_id: 用户ID

        Returns:
            dict: 统计信息
        """
        try:
            from django.db.models import Count, Q

            # 总问答数
            total_count = QAHistory.objects.filter(userid=user_id).count()

            # 最近7天问答数
            seven_days_ago = timezone.now() - timezone.timedelta(days=7)
            recent_count = QAHistory.objects.filter(
                userid=user_id,
                time__gte=seven_days_ago
            ).count()

            # 询问过的不同新闻数量
            unique_news_count = QAHistory.objects.filter(
                userid=user_id
            ).values('newsid').distinct().count()

            return {
                'user_id': user_id,
                'total_questions': total_count,
                'recent_7days_questions': recent_count,
                'unique_news_asked': unique_news_count
            }

        except Exception as e:
            logger.error(f"获取用户问答统计失败: user={user_id}, error={e}")
            return {
                'user_id': user_id,
                'total_questions': 0,
                'recent_7days_questions': 0,
                'unique_news_asked': 0
            }

    @staticmethod
    def delete_old_records(days: int = 90) -> int:
        """
        删除过期的问答记录（数据清理）

        Args:
            days: 保留最近多少天的记录

        Returns:
            int: 删除的记录数
        """
        try:
            cutoff_date = timezone.now() - timezone.timedelta(days=days)

            deleted_count, _ = QAHistory.objects.filter(
                time__lt=cutoff_date
            ).delete()

            logger.info(f"清理过期问答记录: 删除{deleted_count}条记录（保留{days}天内）")
            return deleted_count

        except Exception as e:
            logger.error(f"清理过期问答记录失败: error={e}")
            return 0
