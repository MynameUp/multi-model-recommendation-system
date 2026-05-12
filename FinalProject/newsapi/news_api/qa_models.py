"""
    Author: AI Assistant
    Desc: 新闻问答相关的数据模型
"""
from django.db import models


class NewsVector(models.Model):
    """
    新闻向量存储模型

    用于存储新闻的向量表示，支持语义检索和相似度计算
    """
    id = models.AutoField(primary_key=True, verbose_name='主键ID')
    news_id = models.IntegerField(unique=True, verbose_name='新闻ID', db_index=True)
    vector_data = models.TextField(null=True, blank=True, verbose_name='向量数据(JSON格式)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'news_api_newsvector'
        verbose_name = '新闻向量'
        verbose_name_plural = '新闻向量'
        ordering = ['-created_at']

    def __str__(self):
        return f"NewsVector(news_id={self.news_id})"

    def get_vector(self):
        """
        获取向量数据（从JSON字符串转换为列表）

        Returns:
            list: 向量数据列表，如果解析失败返回None
        """
        import json
        try:
            if self.vector_data:
                return json.loads(self.vector_data)
            return None
        except (json.JSONDecodeError, TypeError):
            return None

    def set_vector(self, vector_list):
        """
        设置向量数据（将列表转换为JSON字符串）

        Args:
            vector_list: 向量数据列表
        """
        import json
        self.vector_data = json.dumps(vector_list)


class QAHistory(models.Model):
    """
    新闻问答历史记录模型

    记录用户的问答历史，用于分析和优化推荐算法
    """
    id = models.AutoField(primary_key=True, verbose_name='主键ID')
    userid = models.IntegerField(verbose_name='用户ID', db_index=True)
    newsid = models.IntegerField(verbose_name='新闻ID', db_index=True)
    question = models.TextField(verbose_name='用户问题')
    answer = models.TextField(verbose_name='系统回答')
    time = models.DateTimeField(auto_now_add=True, verbose_name='问答时间')

    class Meta:
        db_table = 'news_api_qahistory'
        verbose_name = '问答历史'
        verbose_name_plural = '问答历史'
        ordering = ['-time']
        indexes = [
            models.Index(fields=['userid'], name='idx_userid'),
            models.Index(fields=['newsid'], name='idx_newsid'),
            models.Index(fields=['time'], name='idx_time'),
        ]

    def __str__(self):
        return f"QAHistory(user={self.userid}, news={self.newsid}, time={self.time})"

    @classmethod
    def get_user_history(cls, user_id, limit=50):
        """
        获取用户的问答历史

        Args:
            user_id: 用户ID
            limit: 返回记录数量限制

        Returns:
            QuerySet: 问答历史记录查询集
        """
        return cls.objects.filter(userid=user_id).order_by('-time')[:limit]

    @classmethod
    def get_news_qa_stats(cls, news_id):
        """
        获取某篇新闻的问答统计信息

        Args:
            news_id: 新闻ID

        Returns:
            dict: 包含问答次数、常见问题等统计信息
        """
        from django.db.models import Count

        stats = cls.objects.filter(newsid=news_id).aggregate(
            total_questions=Count('id'),
        )

        # 获取最常问的问题（出现频率最高的前5个）
        frequent_questions = cls.objects.filter(
            newsid=news_id
        ).values('question').annotate(
            count=Count('id')
        ).order_by('-count')[:5]

        return {
            'total_questions': stats['total_questions'] or 0,
            'frequent_questions': list(frequent_questions)
        }
