"""
    Author: AI Assistant
    Desc: 新闻问答业务逻辑层 - 处理向量管理和问答历史的业务逻辑
"""
import logging
from typing import List, Dict

from Recommend.NewsQAAgent import NewsVectorStore
from news_api.qa_dao import NewsVectorDAO, QAHistoryDAO

logger = logging.getLogger(__name__)


class NewsVectorService:
    """新闻向量服务"""

    def __init__(self):
        self.vector_store = NewsVectorStore()

    def initialize_all_vectors(self, batch_size: int = 100) -> Dict:
        """
        初始化所有新闻的向量

        Args:
            batch_size: 批处理大小

        Returns:
            dict: 包含处理结果的统计信息
        """
        try:
            logger.info("开始初始化所有新闻向量...")

            # 获取所有未向量化的新闻
            from news_api.models import newsdetail

            # 获取已向量化的新闻ID列表
            existing_vectors = NewsVectorDAO.get_all_vectors(limit=None)
            existing_ids = set(item['news_id'] for item in existing_vectors)

            # 查询所有新闻
            all_news = newsdetail.objects.all()
            to_process = []

            for news in all_news:
                if news.news_id not in existing_ids:
                    to_process.append(news)

            total = len(to_process)
            logger.info(f"需要处理 {total} 篇新闻")

            if total == 0:
                return {
                    'success': True,
                    'message': '所有新闻已完成向量化',
                    'total': 0,
                    'success_count': 0,
                    'failed_count': 0
                }

            # 分批处理
            success_count = 0
            failed_count = 0

            for i in range(0, total, batch_size):
                batch = to_process[i:i + batch_size]

                for news in batch:
                    try:
                        title = news.title or ''
                        summary = news.mainpage[:200] if news.mainpage else ''
                        content = news.mainpage or ''

                        success = self.vector_store.build_vector_for_news(
                            news_id=news.news_id,
                            title=title,
                            summary=summary,
                            content=content
                        )

                        if success:
                            success_count += 1
                        else:
                            failed_count += 1

                    except Exception as e:
                        logger.error(f"处理新闻{news.news_id}失败: {e}")
                        failed_count += 1

                # 每批处理后记录进度
                processed = min(i + batch_size, total)
                logger.info(f"进度: {processed}/{total}")

            result = {
                'success': True,
                'message': f'向量初始化完成',
                'total': total,
                'success_count': success_count,
                'failed_count': failed_count
            }

            logger.info(f"向量初始化完成: {result}")
            return result

        except Exception as e:
            logger.error(f"初始化向量失败: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'初始化失败: {str(e)}',
                'total': 0,
                'success_count': 0,
                'failed_count': 0
            }

    def get_vectorization_status(self) -> Dict:
        """
        获取向量化状态统计

        Returns:
            dict: 向量化状态信息
        """
        try:
            from news_api.models import newsdetail

            total_news = newsdetail.objects.count()
            vectorized_count = NewsVectorDAO.get_vector_count()

            return {
                'total_news': total_news,
                'vectorized_news': vectorized_count,
                'pending_news': total_news - vectorized_count,
                'completion_rate': round(
                    (vectorized_count / total_news * 100) if total_news > 0 else 0,
                    2
                )
            }

        except Exception as e:
            logger.error(f"获取向量化状态失败: {e}")
            return {
                'total_news': 0,
                'vectorized_news': 0,
                'pending_news': 0,
                'completion_rate': 0
            }

    def reindex_news(self, news_id: int) -> bool:
        """
        重新索引单篇新闻的向量

        Args:
            news_id: 新闻ID

        Returns:
            bool: 是否成功
        """
        try:
            from news_api.models import newsdetail

            news = newsdetail.objects.get(news_id=news_id)

            title = news.title or ''
            summary = news.mainpage[:200] if news.mainpage else ''
            content = news.mainpage or ''

            success = self.vector_store.build_vector_for_news(
                news_id=news_id,
                title=title,
                summary=summary,
                content=content
            )

            return success

        except newsdetail.DoesNotExist:
            logger.error(f"新闻不存在: news_id={news_id}")
            return False
        except Exception as e:
            logger.error(f"重新索引新闻失败: news_id={news_id}, error={e}")
            return False

    def close(self):
        """关闭资源"""
        self.vector_store.close()


class QAHistoryService:
    """问答历史服务"""

    @staticmethod
    def save_question_answer(user_id: int, news_id: int, question: str, answer: str) -> bool:
        """
        保存问答记录

        Args:
            user_id: 用户ID
            news_id: 新闻ID
            question: 问题
            answer: 答案

        Returns:
            bool: 是否成功保存
        """
        return QAHistoryDAO.save_qa_record(user_id, news_id, question, answer)

    @staticmethod
    def get_user_history(user_id: int, limit: int = 50) -> List[Dict]:
        """
        获取用户问答历史

        Args:
            user_id: 用户ID
            limit: 返回数量限制

        Returns:
            list: 问答历史列表
        """
        return QAHistoryDAO.get_user_history(user_id, limit)

    @staticmethod
    def get_news_qa_history(news_id: int, limit: int = 100) -> List[Dict]:
        """
        获取新闻的问答历史

        Args:
            news_id: 新闻ID
            limit: 返回数量限制

        Returns:
            list: 问答历史列表
        """
        return QAHistoryDAO.get_news_qa_history(news_id, limit)

    @staticmethod
    def get_news_qa_stats(news_id: int) -> Dict:
        """
        获取新闻的问答统计

        Args:
            news_id: 新闻ID

        Returns:
            dict: 统计信息
        """
        return QAHistoryDAO.get_news_qa_stats(news_id)

    @staticmethod
    def get_user_qa_stats(user_id: int) -> Dict:
        """
        获取用户的问答统计

        Args:
            user_id: 用户ID

        Returns:
            dict: 统计信息
        """
        return QAHistoryDAO.get_user_qa_stats(user_id)

    @staticmethod
    def cleanup_old_data(days: int = 90) -> Dict:
        """
        清理过期数据

        Args:
            days: 保留天数

        Returns:
            dict: 清理结果
        """
        try:
            deleted_count = QAHistoryDAO.delete_old_records(days)

            return {
                'success': True,
                'deleted_count': deleted_count,
                'retention_days': days
            }
        except Exception as e:
            logger.error(f"清理过期数据失败: {e}")
            return {
                'success': False,
                'deleted_count': 0,
                'retention_days': days,
                'error': str(e)
            }
