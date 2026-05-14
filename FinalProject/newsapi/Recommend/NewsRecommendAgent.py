# -*- coding: utf-8 -*-
"""
    Author: AI Assistant
    Desc: 新闻推荐智能体 - 基于自然语言理解的综合推荐引擎
    Features:
        - 自然语言意图识别
        - 关键词提取
        - 多维度综合评分
        - 推荐理由生成
"""
import math
import re
from datetime import datetime, timedelta
import jieba
import logging
from logging.handlers import TimedRotatingFileHandler
import pymysql

from Spider.settings import DB_HOST, DB_USER, DB_PASSWD, DB_NAME, DB_PORT

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)-7s - %(message)s')

log_file_handler = TimedRotatingFileHandler(filename="Recommend/intelligent_agent.log",
                                            when="D", interval=1,
                                            backupCount=30)
log_file_handler.setFormatter(formatter)
logger.addHandler(log_file_handler)


class NewsRecommendAgent:
    """新闻推荐智能体"""

    def __init__(self):
        self.db = self.connect()
        self.cursor = self.db.cursor()

        # 评分权重配置
        self.weights = {
            'similarity': 0.30,      # α: 相似度权重
            'heat': 0.20,            # β: 热度权重
            'freshness': 0.25,       # γ: 新鲜度权重
            'user_interest': 0.15,   # δ: 用户兴趣权重
            'quality': 0.10,         # ε: 质量权重
            'repetition_penalty': 0.15  # λ: 重复惩罚系数
        }

        # 时间衰减系数 k (FreshnessScore = exp(-k * Δt))
        self.freshness_decay_k = 0.1

        # 类别映射 - 已将所有值转换为字符串
        self.category_map = {
            '美股': ['0', '美股', '美国股票', '美股市场', 'US stock', 'NASDAQ', 'NYSE'],
            '国内': ['1', '国内', '社会', '中国', '国内新闻', 'domestic'],
            '国际': ['2', '3', '国际', '全球', '世界', '海外', 'international', 'world'],
            '体育': ['4', '体育', '运动', '足球', '篮球', '奥运会', 'sports'],
            '娱乐': ['5', '娱乐', '明星', '电影', '音乐', '电视剧', 'entertainment'],
            '军事': ['6', '军事', '国防', '军队', '武器', 'military'],
            '科技': ['7', '科技', 'technology', '人工智能', 'AI', '芯片', '互联网', '数码'],
            '财经': ['8', '财经', 'finance', 'economic', '基金', '投资', '经济', '金融'],
            '股市': ['9', '股市', '股票', 'A股', '股市行情', 'stock market', 'trading'],

        }

        # 停用词表（扩展版）- 包含常见助词、介词、连词、代词、副词、语气词等
        self.stop_words = {
            # 助词
            '的', '了', '着', '过', '之', '者', '所', '而', '之',
            # 介词
            '在', '于', '从', '向', '到', '往', '自', '由', '向', '对', '对于', '关于', '至于', '按照', '依照', '本着', '通过', '经过', '随着',
            # 连词
            '和', '跟', '同', '与', '及', '以及', '或', '或者', '及', '而', '而且', '并', '并且', '但', '但是', '然而', '却', '虽然', '尽管', '不管', '不论', '因为', '由于', '所以', '因此', '因而', '于是', '从而', '进而',
            # 代词
            '我', '你', '他', '她', '它', '我们', '你们', '他们', '她们', '它们', '这', '那', '这些', '那些', '此', '该', '哪个', '哪些', '什么', '怎么', '怎样', '如何', '谁', '哪个', '哪里', '哪儿',
            # 副词
            '很', '非常', '太', '最', '极', '相当', '十分', '特别', '格外', '更加', '更', '越', '越来越', '稍', '稍微', '略', '略微', '比较', '较为', '都', '全', '总', '总共', '共', '一起', '一同', '一起', '已经', '曾经', '刚才', '刚', '方才', '才', '就', '便', '于是', '然后', '接着', '跟着', '于是', '从而', '进而', '终于', '总算', '毕竟', '到底', '究竟', '竟然', '居然', '果然', '果真', '确实', '的确', '实在', '真的', '真', '一定', '必定', '必然', '必须', '得', '能', '能够', '会', '可以', '可能', '也许', '或许', '大概', '大约', '差不多', '似乎', '好像', '仿佛', '宛如', '犹如', '如同', '像', '如',
            # 语气词
            '吗', '呢', '啊', '呀', '哇', '吧', '嘛', '啦', '哦', '喔', '哎', '唉', '哼', '嗯', '嗯嗯',
            # 数量词
            '一', '二', '两', '三', '四', '五', '六', '七', '八', '九', '十', '百', '千', '万', '亿', '第', '初', '几', '多', '少', '些', '点', '一些', '一点', '一些些', '有些', '多少', '若干', '许多', '很多', '好多', '太多',
            # 时间词
            '现在', '当前', '目前', '今天', '今日', '明天', '明日', '后天', '昨天', '昨日', '前天', '刚才', '刚刚', '刚才', '刚', '方才', '才', '就', '便', '于是', '然后', '接着', '跟着', '于是', '从而', '进而', '终于', '总算', '毕竟', '到底', '究竟', '已经', '曾经', '早已', '早就', '早就', '早就', '早就', '早就', '早就',
            # 方位词
            '上', '下', '左', '右', '前', '后', '里', '外', '内', '中', '间', '旁', '边', '侧', '面', '东', '南', '西', '北', '东南', '东北', '西南', '西北',
            # 常用短语
            '没有', '不是', '不要', '不用', '不能', '不会', '不可以', '不应该', '不应该', '不应该', '不应该', '不应该',
            # 其他高频词
            '是', '有', '要', '能', '会', '可以', '可能', '应该', '需要', '想要', '希望', '想要', '打算', '准备', '开始', '结束', '完成', '进行', '发展', '变化', '提高', '增加', '减少', '降低', '改善', '改进', '改变', '转变', '转换', '转移', '移动', '运行', '工作', '学习', '研究', '讨论', '分析', '说明', '解释', '表示', '表达', '描述', '介绍', '报道', '新闻', '报道', '消息', '信息', '数据', '资料', '内容', '文章', '文本', '文字', '语言', '词汇', '词语', '句子', '段落', '章节', '部分', '方面', '领域', '范围', '程度', '水平', '标准', '要求', '条件', '因素', '原因', '结果', '效果', '影响', '作用', '意义', '价值', '重要性', '必要性', '可能性', '可行性', '合理性', '正确性', '准确性', '完整性', '全面性', '系统性', '科学性', '技术性', '专业性', '实用性', '适用性', '有效性', '高效性', '先进性', '创新性', '创造性', '独特性', '特色性', '代表性', '典型性', '普遍性', '一般性', '特殊性', '个别性', '具体性', '抽象性', '理论性', '实践性', '现实性', '历史性', '时代性', '现代性', '当代性', '前瞻性', '预见性', '预见性', '预见性',
            # 英文停用词
            'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'shall', 'should', 'can', 'could', 'may', 'might', 'must', 'need', 'dare', 'ought', 'used', 'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'we', 'they', 'what', 'which', 'who', 'whom', 'whose', 'where', 'when', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'many', 'much', 'some', 'any', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'because', 'as', 'until', 'while', 'about', 'against', 'between', 'through', 'during', 'before', 'after', 'above', 'below', 'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'also', 'such', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
        }


    def connect(self):
        """连接数据库"""
        db = pymysql.Connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWD,
            database=DB_NAME,
            port=DB_PORT,
            charset='utf8'
        )
        return db

    def parse_user_intent(self, user_input, userid=None):
        """
        解析用户意图，提取关键词、类别、时间范围等

        Args:
            user_input: 用户输入的自然语言
            userid: 用户ID（可选）

        Returns:
            dict: 包含解析结果的字典
        """
        intent = {
            'keywords': [],  # 关键词列表
            'categories': [],  # 新闻类别
            'time_range': None,  # 时间范围（天数）
            'exclude_categories': [],  # 排除的类别
            'require_fresh': False,  # 是否要求最新
            'query_type': 'general',  # 查询类型：general/similar/history
            'original_input': user_input,
            'topic_keywords': [],  # 用户明确提到的主题关键词（如"人工智能"）
            'category_request': False,  # 是否明确要求某类别
            'primary_topic': None  # 主要搜索主题（用于推荐理由）
        }

        # 转换为小写（处理英文）
        text_lower = user_input.lower()

        # 1. 识别时间范围（在过滤停用词之前执行）
        time_patterns = {
            r'今天|今日': 1,
            r'最近.*?[一两2]天|近.*?[一两2]天': 2,
            r'最近.*?三天|近.*?三天': 3,
            r'最近.*?一周|近.*?一周|这周': 7,
            r'最近.*?一个月|近.*?一个月': 30,
        }

        for pattern, days in time_patterns.items():
            if re.search(pattern, user_input):
                intent['time_range'] = days
                intent['require_fresh'] = True
                break

        # 2. 识别新闻类别和主题关键词
        # 定义明确的类别指示词（只有包含这些词才认为是类别请求）
        explicit_category_indicators = ['类别', '分类', '栏目', '板块']
        category_type_keywords = {
            '科技': ['科技新闻', '科技类', '科技方面'],
            '财经': ['财经新闻', '财经类', '经济方面'],
            '国际': ['国际新闻', '国际类', '国际方面'],
            '国内': ['国内新闻', '国内类', '国内方面'],
            '娱乐': ['娱乐新闻', '娱乐类', '娱乐方面'],
            '体育': ['体育新闻', '体育类', '体育方面'],
            '军事': ['军事新闻', '军事类', '军事方面'],
            '股市': ['股市行情', '股市类'],
            '美股': ['美股行情', '美股类'],
        }

        # 先检查是否是明确的类别请求
        for category, indicators in category_type_keywords.items():
            for indicator in indicators:
                if indicator in user_input:
                    if category not in intent['categories']:
                        intent['categories'].append(category)
                        intent['category_request'] = True
                    break

        # 如果没有明确类别指示，再检查类别映射中的词
        # 但要区分是类别请求还是主题关键词
        topic_to_category = {}  # 记录主题词到类别的映射

        for category, keywords in self.category_map.items():
            for keyword in keywords:
                # 跳过数字ID
                if keyword.isdigit():
                    continue

                # 检查是否在用户输入中
                if keyword in user_input or keyword.lower() in text_lower:
                    # 特殊处理：像"人工智能"、"AI"、"芯片"这些是主题关键词，不是类别
                    # 只有"科技"、"财经"等明确的类别词才算类别请求
                    if keyword in ['科技', '财经', '国际', '国内', '娱乐', '体育', '军事', '股市', '美股']:
                        # 这是类别词
                        if category not in intent['categories']:
                            intent['categories'].append(category)
                            intent['category_request'] = True
                    else:
                        # 这是主题关键词（如"人工智能"、"AI"、"芯片"）
                        if keyword not in intent['topic_keywords']:
                            intent['topic_keywords'].append(keyword)
                        # 同时添加到关键词列表
                        if keyword not in intent['keywords']:
                            intent['keywords'].append(keyword)
                        # 记录主题词到类别的映射
                        topic_to_category[keyword] = category
                    break

        # 设置主要搜索主题（第一个主题关键词或类别）
        if intent['topic_keywords']:
            intent['primary_topic'] = intent['topic_keywords'][0]
        elif intent['categories']:
            intent['primary_topic'] = intent['categories'][0]

        # 3. 识别排除类别（"不要XXX"）
        exclude_pattern = r'不要(.+?)(?:新闻|内容|文章)?(?:，|,|。|$)'
        exclude_matches = re.findall(exclude_pattern, user_input)
        for exclude_text in exclude_matches:
            for category, keywords in self.category_map.items():
                for keyword in keywords:
                    if keyword in exclude_text:
                        if category not in intent['exclude_categories']:
                            intent['exclude_categories'].append(category)

        # 4. 提取关键词（使用jieba分词）
        # 临时停用词表 - 移除时间词，避免过滤掉"今天"等关键词
        temp_stop_words = self.stop_words - {'今天', '今日', '明天', '昨天'}

        words = jieba.cut(user_input)
        meaningful_words = [w for w in words if w not in temp_stop_words and len(w.strip()) > 0]

        # 过滤掉已经识别为类别的词
        category_words = set()
        for keywords in self.category_map.values():
            for kw in keywords:
                if isinstance(kw, str) and len(kw) <= 4:
                    category_words.add(kw)

        # 额外过滤掉无意义的动词和助词，但保留主题关键词
        for kw in intent['topic_keywords']:
            if kw in meaningful_words and kw not in intent['keywords']:
                intent['keywords'].append(kw)

        # 清理关键词列表
        intent['keywords'] = [w for w in meaningful_words
                              if w not in ['新闻', '推荐', '看', '想', '给我', '要', '希望', '有关', '相关']]

        # 5. 识别特殊查询类型
        if '换一批' in user_input or '换一些' in user_input:
            intent['query_type'] = 'refresh'
        elif '根据我最近' in user_input or '根据历史' in user_input:
            intent['query_type'] = 'history'
        elif '相似' in user_input or '相关' in user_input:
            intent['query_type'] = 'similar'

        logger.info(f"用户意图解析结果: {intent}")
        return intent

    def calculate_similarity_score(self, news_keywords, query_keywords, user_tags, intent=None):
        """
        计算新闻与查询/用户兴趣的相似度（优化版）

        Args:
            news_keywords: 新闻关键词列表
            query_keywords: 查询关键词列表
            user_tags: 用户标签列表
            intent: 用户意图信息（可选）

        Returns:
            float: 相似度分数 (0-1)
        """
        if not news_keywords and not query_keywords and not user_tags:
            return 0.0

        news_set = set(news_keywords) if news_keywords else set()
        query_set = set(query_keywords) if query_keywords else set()
        user_set = set(user_tags) if user_tags else set()

        # 扩展查询关键词：添加相关词汇
        expanded_query_set = set(query_set)
        if intent:
            expanded_query_set.update(self.expand_keywords_with_related(query_set, intent))

        # 1. 计算与查询关键词的相似度（优化版）
        query_sim = 0.0
        if expanded_query_set and news_set:
            # 精确匹配得分
            exact_match = len(news_set & expanded_query_set)

            # 部分匹配得分（检查新闻标题中是否包含查询词）
            partial_match_score = 0.0
            if intent and 'original_input' in intent:
                for query_word in expanded_query_set:
                    if query_word in intent['original_input']:
                        # 检查是否在新闻标题中出现
                        # 这个需要在调用时传入新闻标题，这里暂时跳过
                        pass

            # 使用改进的Jaccard相似度
            if exact_match > 0:
                # 如果有关键词匹配，给予基础分
                base_score = exact_match / len(expanded_query_set)
                # 归一化
                query_sim = min(base_score * 1.5, 1.0)  # 乘以1.5提高匹配词的权重

        # 2. 计算与用户标签的相似度
        user_sim = 0.0
        if user_set and news_set:
            intersection = len(news_set & user_set)
            union = len(news_set | user_set)
            if union > 0:
                user_sim = intersection / union

        # 3. 综合相似度（查询关键词权重更高）
        if query_keywords and user_tags:
            similarity = 0.7 * query_sim + 0.3 * user_sim
        elif query_keywords:
            similarity = query_sim
        elif user_tags:
            similarity = user_sim
        else:
            similarity = 0.0

        return min(similarity, 1.0)

    def expand_keywords_with_related(self, query_keywords, intent):
        """
        扩展查询关键词：添加相关词汇

        Args:
            query_keywords: 原始查询关键词
            intent: 用户意图

        Returns:
            set: 扩展后的关键词集合
        """
        related_keywords = set()

        # 定义常见主题的相关词汇
        topic_relations = {
            '财经': ['股票', '基金', '投资', '期货', '黄金', '银行', '经济', '金融', '股市', '理财'],
            '科技': ['人工智能', 'AI', '芯片', '互联网', '数码', '软件', '技术', '创新', '5G', '区块链'],
            '国际': ['外交', '联合国', '世界', '全球', '国际关系', '条约', '国际组织'],
            '国内': ['中国', '社会', '民生', '政策', '改革', '发展'],
            '娱乐': ['明星', '电影', '音乐', '电视剧', '综艺', '演员', '歌手'],
            '体育': ['足球', '篮球', '运动', '比赛', '奥运会', '运动员', '赛事'],
            '军事': ['国防', '军队', '武器', '军事演习', '军事装备', '军事战略'],
            '股市': ['A股', '港股', '美股', '股票', '股市行情', '交易', '涨跌'],
            '美股': ['NASDAQ', 'NYSE', '美国股市', '华尔街', '美股行情'],
        }

        # 根据查询词添加相关词汇
        for query_word in query_keywords:
            # 如果查询词是某个主题，添加该主题的相关词汇
            for topic, related_list in topic_relations.items():
                if query_word == topic or query_word in self.category_map.get(topic, []):
                    related_keywords.update(related_list)
                    break

        return related_keywords

    def generate_recommendation_reason(self, news_data, intent, user_id, score_breakdown):
        """
        生成推荐理由

        Args:
            news_data: 新闻数据
            intent: 用户意图
            user_id: 用户ID
            score_breakdown: 各维度得分详情

        Returns:
            str: 推荐理由文本
        """
        reasons = []

        # 1. 基于用户主要搜索意图（主题词或类别）
        if intent['primary_topic']:
            topic = intent['primary_topic']

            # 如果是类别请求（如"财经"、"科技"）
            if intent['category_request'] and topic in self.category_map:
                # 检查新闻类别是否匹配用户请求的类别
                news_category_id = news_data.get('category')
                # 获取用户请求类别对应的ID
                requested_category_ids = []
                if topic in self.category_map:
                    requested_category_ids.append(self.category_map[topic][0])

                # 检查新闻的类别ID是否匹配
                if str(news_category_id) in requested_category_ids:
                    reasons.append(f"符合你要求的「{topic}」新闻")
                else:
                    # 类别不匹配但被推荐，说明有其他高分因素
                    reasons.append(f"与「{topic}」相关的新闻")

            # 如果是主题关键词（如"人工智能"、"芯片"）
            elif topic in news_data.get('title', '') or topic in news_data.get('keywords', '') or topic in news_data.get('mainpage', ''):
                reasons.append(f"符合你要求的「{topic}」新闻")
            else:
                # 主题词不在新闻中，但相似度较高
                reasons.append(f"与「{topic}」相关的新闻")

        # 2. 基于查询关键词匹配（如果没有主题词）
        elif intent['keywords'] and score_breakdown['similarity'] > 0.2:
            matched_keywords = [kw for kw in intent['keywords'] if kw in news_data.get('title', '') or kw in news_data.get('keywords', '')]
            if matched_keywords:
                reasons.append(f"包含你搜索的关键词「{', '.join(matched_keywords[:2])}」")

        # 3. 基于用户历史行为和兴趣标签（只有当用户兴趣得分较高时才显示）
        if score_breakdown['user_interest'] > 0.6:
            try:
                sql = "SELECT tags FROM news_api_user WHERE userid = %s"
                self.cursor.execute(sql, (user_id,))
                result = self.cursor.fetchone()
                if result and result[0]:
                    user_tags = set(result[0].split(','))
                    news_keywords = set(news_data.get('keywords', '').split(',')) if news_data.get('keywords') else set()
                    matched_tags = user_tags & news_keywords
                    if matched_tags and not any('主题相关' in r or '关键词' in r or '新闻' in r for r in reasons):
                        # 只显示真正匹配的用户关注标签
                        reasons.append(f"与你关注的「{', '.join(list(matched_tags)[:2])}」话题相关")
            except:
                pass

        # 4. 基于内容质量（只有高质量内容才显示，调整阈值）
        if score_breakdown['quality'] > 0.85:
            content_length = len(news_data.get('mainpage', ''))
            if content_length > 1000:  # 更长文才称为深度内容
                reasons.append("优质深度长文")
            elif content_length > 600:
                reasons.append("内容详实")

        # 5. 基于热度（只有真正热门时才显示）
        if score_breakdown['heat'] > 0.8:
            reasons.append(f"热门文章（{news_data.get('readnum', 0)}阅读）")

        # 6. 基于新鲜度
        if score_breakdown['freshness'] > 0.85:
            reasons.append("最新发布")
        elif score_breakdown['freshness'] > 0.7:
            reasons.append("近期更新")

        # 组合推荐理由，最多显示2个理由，避免信息过载
        if reasons:
            return "；".join(reasons[:2])
        else:
            return "综合推荐"

    def calculate_heat_score(self, readnum, comments):
        """
        计算新闻热度分数

        Args:
            readnum: 阅读量
            comments: 评论数

        Returns:
            float: 热度分数 (0-1)
        """
        # 归一化处理：假设最大阅读量为10000，最大评论数为1000
        normalized_read = min(readnum / 10000.0, 1.0)
        normalized_comment = min(comments / 1000.0, 1.0)

        # 热度 = 0.4 * 阅读量 + 0.5 * 评论数（与原有系统保持一致）
        heat = 0.4 * normalized_read + 0.5 * normalized_comment
        return min(heat, 1.0)

    def calculate_freshness_score(self, publish_date_str):
        """
        计算新闻新鲜度分数
        FreshnessScore = exp(-k * Δt)

        Args:
            publish_date_str: 发布日期字符串

        Returns:
            float: 新鲜度分数 (0-1)
        """
        try:
            # 解析日期格式（支持多种格式）
            publish_date_str = publish_date_str.replace("年", "-").replace("月", "-").replace("日", " ")

            # 尝试不同格式
            for fmt in ['%Y-%m-%d %H:%M', '%Y-%m-%d', '%Y/%m/%d %H:%M', '%Y/%m/%d']:
                try:
                    publish_date = datetime.strptime(publish_date_str.strip(), fmt)
                    break
                except ValueError:
                    continue
            else:
                # 如果所有格式都失败，返回默认值
                return 0.5

            # 计算时间差（天）
            now = datetime.now()
            delta_t = (now - publish_date).total_seconds() / 86400.0  # 转换为天

            # 应用指数衰减公式
            freshness = math.exp(-self.freshness_decay_k * delta_t)

            return max(freshness, 0.0)  # 确保非负

        except Exception as e:
            logger.error(f"计算新鲜度失败: {e}")
            return 0.5  # 默认中等新鲜度

    def calculate_user_interest_score(self, news_category, user_id, news_keywords):
        """
        计算用户兴趣匹配度

        Args:
            news_category: 新闻类别
            user_id: 用户ID
            news_keywords: 新闻关键词

        Returns:
            float: 兴趣分数 (0-1)
        """
        try:
            # 获取用户标签和权重
            sql = "SELECT tags, tagsweight FROM news_api_user WHERE userid = %s"
            self.cursor.execute(sql, (user_id,))
            result = self.cursor.fetchone()

            if not result:
                return 0.5  # 新用户默认中等兴趣

            tags_str = result[0]
            tagsweight_str = result[1]

            if not tags_str:
                return 0.5

            user_tags = set(tags_str.split(','))

            # 解析标签权重
            try:
                import ast
                tagsweight = ast.literal_eval(tagsweight_str) if tagsweight_str else {}
            except:
                tagsweight = {}

            # 计算关键词匹配度
            news_keyword_set = set(news_keywords) if news_keywords else set()
            matched_tags = user_tags & news_keyword_set

            if not matched_tags:
                return 0.3  # 无匹配时给基础分

            # 累加匹配标签的权重
            interest_score = sum(tagsweight.get(tag, 0.5) for tag in matched_tags)

            # 归一化到0-1
            return min(interest_score / len(matched_tags), 1.0)

        except Exception as e:
            logger.error(f"计算用户兴趣失败: {e}")
            return 0.5

    def calculate_quality_score(self, content_length, has_image, has_video):
        """
        计算新闻内容质量分数

        Args:
            content_length: 内容长度
            has_image: 是否有图片
            has_video: 是否有视频

        Returns:
            float: 质量分数 (0-1)
        """
        # 内容长度得分（理想长度500-2000字）
        if content_length < 100:
            length_score = 0.3
        elif content_length < 500:
            length_score = 0.6
        elif content_length < 2000:
            length_score = 1.0
        else:
            length_score = 0.8

        # 多媒体加分
        media_bonus = 0.0
        if has_image:
            media_bonus += 0.1
        if has_video:
            media_bonus += 0.1

        quality = min(length_score + media_bonus, 1.0)
        return quality

    def calculate_repetition_penalty(self, user_id, news_id, history_news_ids):
        """
        计算重复推荐惩罚

        Args:
            user_id: 用户ID
            news_id: 新闻ID
            history_news_ids: 用户历史浏览的新闻ID列表

        Returns:
            float: 惩罚值 (0-1)，越大表示惩罚越重
        """
        # 如果已经浏览过，给予较大惩罚
        if news_id in history_news_ids:
            return 0.8

        # 检查是否与最近浏览的新闻相似度高
        if not history_news_ids:
            return 0.0

        try:
            # 查询最近浏览的5篇新闻的相似度
            recent_ids = history_news_ids[:5]

            # 修复SQL格式化问题 - 使用参数化查询
            placeholders = ','.join(['%s'] * len(recent_ids))
            sql = f"""
                SELECT AVG(new_correlation) 
                FROM news_api_newssimilar 
                WHERE new_id_base IN ({placeholders}) AND new_id_sim = %s
            """

            params = recent_ids + [news_id]
            self.cursor.execute(sql, params)
            result = self.cursor.fetchone()

            if result and result[0]:
                avg_similarity = result[0]
                # 相似度越高，惩罚越大
                return avg_similarity * 0.5

            return 0.0

        except Exception as e:
            logger.error(f"计算重复惩罚失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 0.0


    def get_user_history(self, user_id, limit=50):
        """获取用户历史浏览记录"""
        try:
            sql = """
                SELECT history_newsid 
                FROM news_api_history 
                WHERE userid = %s 
                ORDER BY time DESC 
                LIMIT %s
            """
            self.cursor.execute(sql, (user_id, limit))
            results = self.cursor.fetchall()
            return [row[0] for row in results]
        except Exception as e:
            logger.error(f"获取用户历史失败: {e}")
            return []

    def generate_recommendation_reason(self, news_data, intent, user_id, score_breakdown):
        """
        生成推荐理由

        Args:
            news_data: 新闻数据
            intent: 用户意图
            user_id: 用户ID
            score_breakdown: 各维度得分详情

        Returns:
            str: 推荐理由文本
        """
        reasons = []

        # 1. 基于用户主要搜索意图（主题词或类别）
        if intent['primary_topic']:
            topic = intent['primary_topic']

            # 如果是类别请求（如"财经"、"科技"）
            if intent['category_request'] and topic in self.category_map:
                # 检查新闻类别是否匹配用户请求的类别
                news_category_id = news_data.get('category')
                # 获取用户请求类别对应的ID
                requested_category_ids = []
                if topic in self.category_map:
                    requested_category_ids.append(self.category_map[topic][0])

                # 检查新闻的类别ID是否匹配
                if str(news_category_id) in requested_category_ids:
                    reasons.append(f"符合你要求的「{topic}」新闻")
                else:
                    # 类别不匹配但被推荐，说明有其他高分因素
                    reasons.append(f"与「{topic}」相关的新闻")

            # 如果是主题关键词（如"人工智能"、"芯片"）
            elif topic in news_data.get('title', '') or topic in news_data.get('keywords', '') or topic in news_data.get('mainpage', ''):
                reasons.append(f"符合你要求的「{topic}」新闻")
            else:
                # 主题词不在新闻中，但相似度较高
                reasons.append(f"与「{topic}」相关的新闻")

        # 2. 基于查询关键词匹配（如果没有主题词）
        elif intent['keywords'] and score_breakdown['similarity'] > 0.3:
            matched_keywords = [kw for kw in intent['keywords'] if kw in news_data.get('title', '') or kw in news_data.get('keywords', '')]
            if matched_keywords:
                reasons.append(f"包含你搜索的关键词「{', '.join(matched_keywords[:2])}」")

        # 3. 基于用户历史行为和兴趣标签（只有当用户兴趣得分较高时才显示）
        if score_breakdown['user_interest'] > 0.7:
            try:
                sql = "SELECT tags FROM news_api_user WHERE userid = %s"
                self.cursor.execute(sql, (user_id,))
                result = self.cursor.fetchone()
                if result and result[0]:
                    user_tags = set(result[0].split(','))
                    news_keywords = set(news_data.get('keywords', '').split(',')) if news_data.get('keywords') else set()
                    matched_tags = user_tags & news_keywords
                    if matched_tags and not any('主题相关' in r or '关键词' in r or '新闻' in r for r in reasons):
                        # 只显示真正匹配的用户关注标签
                        reasons.append(f"与你关注的「{', '.join(list(matched_tags)[:2])}」话题相关")
            except:
                pass

        # 4. 基于内容质量（只有高质量内容才显示，调整阈值）
        if score_breakdown['quality'] > 0.9:
            content_length = len(news_data.get('mainpage', ''))
            if content_length > 1000:  # 更长文才称为深度内容
                reasons.append("优质深度长文")
            elif content_length > 600:
                reasons.append("内容详实")

        # 5. 基于热度（只有真正热门时才显示）
        if score_breakdown['heat'] > 0.85:
            reasons.append(f"热门文章（{news_data.get('readnum', 0)}阅读）")

        # 6. 基于新鲜度
        if score_breakdown['freshness'] > 0.9:
            reasons.append("最新发布")
        elif score_breakdown['freshness'] > 0.75:
            reasons.append("近期更新")

        # 组合推荐理由，最多显示2个理由，避免信息过载
        if reasons:
            return "；".join(reasons[:2])
        else:
            return "综合推荐"

    def get_category_name(self, category_id):
        """根据类别ID获取类别名称"""
        category_names = {
            0: "美股",
            1: "国内",
            2: "国际",
            3: "国际",
            4: "体育",
            5: "娱乐",
            6: "军事",
            7: "科技",
            8: "财经",
            9: "股市"
        }
        return category_names.get(category_id, '其他')

    def intelligent_recommend(self, user_input, user_id, top_n=20):
        """
        智能推荐主函数

        Args:
            user_input: 用户输入的自然语言
            user_id: 用户ID
            top_n: 返回推荐数量

        Returns:
            list: 推荐新闻列表（含推荐理由和评分详情）
        """
        logger.info(f"开始智能推荐 - 用户ID: {user_id}, 输入: {user_input}")

        # 1. 解析用户意图
        intent = self.parse_user_intent(user_input, user_id)

        # 2. 获取用户历史记录
        history_ids = self.get_user_history(user_id)

        # 3. 构建查询SQL
        base_sql = """
            SELECT 
                nd.news_id, nd.title, nd.date, nd.pic_url, nd.mainpage,
                nd.origin, nd.category, nd.readnum, nd.comments, nd.keywords,
                nh.news_hot
            FROM news_api_newsdetail nd
            LEFT JOIN news_api_newshot nh ON nd.news_id = nh.news_id
            WHERE 1=1
        """
        params = []

        # 添加类别过滤
        if intent['categories']:
            category_ids = []
            for cat in intent['categories']:
                # cat 是类别名称（如'财经'、'国际'）
                # 直接从 category_map 中查找对应的 ID
                if cat in self.category_map:
                    # category_map[cat][0] 是类别 ID（字符串形式）
                    category_id = self.category_map[cat][0]
                    try:
                        category_ids.append(int(category_id))
                    except ValueError:
                        logger.warning(f"类别ID转换失败: {cat} -> {category_id}")

            if category_ids:
                placeholders = ','.join(['%s'] * len(category_ids))
                base_sql += f" AND nd.category IN ({placeholders})"
                params.extend(category_ids)


               # 排除类别
        if intent['exclude_categories']:
            exclude_ids = []
            for cat in intent['exclude_categories']:
                # cat 是类别名称（如'娱乐'）
                if cat in self.category_map:
                    exclude_id = self.category_map[cat][0]
                    try:
                        exclude_ids.append(int(exclude_id))
                    except ValueError:
                        logger.warning(f"排除类别ID转换失败: {cat} -> {exclude_id}")

            if exclude_ids:
                placeholders = ','.join(['%s'] * len(exclude_ids))
                base_sql += f" AND nd.category NOT IN ({placeholders})"
                params.extend(exclude_ids)

                # 时间范围过滤 - 修复日期格式问题
        if intent['time_range']:
            # 由于数据库中date字段是字符串格式（如"2024年01月15日 10:30"）
            # 我们不能直接使用MySQL的日期函数，需要在Python中计算日期阈值
            threshold_date = datetime.now() - timedelta(days=intent['time_range'])
            threshold_str = threshold_date.strftime('%Y{y}%m{m}%d{d} %H:%M')

            # 使用字符串比较（假设日期格式一致）
            base_sql += " AND STR_TO_DATE(REPLACE(REPLACE(REPLACE(nd.date, '年', '-'), '月', '-'), '日', ''), '%%Y-%%m-%%d %%H:%%i') >= DATE_SUB(NOW(), INTERVAL %s DAY)"
            params.append(intent['time_range'])

        # 排除已读新闻（如果是刷新请求则不排除）
        if intent['query_type'] != 'refresh' and history_ids:
            placeholders = ','.join(['%s'] * min(len(history_ids), 100))
            base_sql += f" AND nd.news_id NOT IN ({placeholders})"
            params.extend(history_ids[:100])

        # 按时间排序
        base_sql += " ORDER BY nd.date DESC LIMIT 300"  # 增加查询数量，后续用评分筛选

        # 4. 执行查询
        try:
            self.cursor.execute(base_sql, params)
            columns = [desc[0] for desc in self.cursor.description]
            news_list = [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"查询新闻失败: {e}")
            return []

        # 5. 计算每篇新闻的综合得分
        scored_news = []
        for news in news_list:
            # 计算各维度得分
            keywords = news.get('keywords', '').split(',') if news.get('keywords') else []
            title_keywords = jieba.lcut(news.get('title', ''))
            all_keywords = list(set(keywords + title_keywords))

            # 获取用户标签
            try:
                sql = "SELECT tags FROM news_api_user WHERE userid = %s"
                self.cursor.execute(sql, (user_id,))
                result = self.cursor.fetchone()
                user_tags = result[0].split(',') if result and result[0] else []
            except:
                user_tags = []

            # 计算相似度时传入intent参数
            similarity_score = self.calculate_similarity_score(all_keywords, intent['keywords'], user_tags, intent)
            heat_score = self.calculate_heat_score(news.get('readnum', 0), news.get('comments', 0))
            freshness_score = self.calculate_freshness_score(news.get('date', ''))
            user_interest_score = self.calculate_user_interest_score(news.get('category'), user_id, all_keywords)
            quality_score = self.calculate_quality_score(
                len(news.get('mainpage', '')),
                bool(news.get('pic_url')),
                bool(news.get('videourl'))
            )
            repetition_penalty = self.calculate_repetition_penalty(user_id, news['news_id'], history_ids)

            # 根据用户意图动态调整权重
            dynamic_weights = self.calculate_dynamic_weights(intent)

            # 综合评分公式（使用动态权重）
            final_score = (
                dynamic_weights['similarity'] * similarity_score +
                dynamic_weights['heat'] * heat_score +
                dynamic_weights['freshness'] * freshness_score +
                dynamic_weights['user_interest'] * user_interest_score +
                dynamic_weights['quality'] * quality_score -
                dynamic_weights['repetition_penalty'] * repetition_penalty
            )

            # 确保分数在0-1之间
            final_score = max(min(final_score, 1.0), 0.0)

            score_breakdown = {
                'similarity': similarity_score,
                'heat': heat_score,
                'freshness': freshness_score,
                'user_interest': user_interest_score,
                'quality': quality_score,
                'repetition_penalty': repetition_penalty,
                'final_score': final_score
            }

            # 生成推荐理由
            reason = self.generate_recommendation_reason(news, intent, user_id, score_breakdown)

            scored_news.append({
                'news': news,
                'score': final_score,
                'score_breakdown': score_breakdown,
                'reason': reason
            })

        # 6. 按综合得分排序
        scored_news.sort(key=lambda x: x['score'], reverse=True)

        # 7. 过滤掉分数过低的结果
        min_score_threshold = 0.1  # 最低分数阈值
        filtered_news = [item for item in scored_news if item['score'] >= min_score_threshold]

        # 8. 返回Top-N推荐
        recommendations = filtered_news[:top_n]

        logger.info(f"智能推荐完成 - 返回 {len(recommendations)} 条结果")

        return recommendations

    def calculate_dynamic_weights(self, intent):
        """
        根据用户意图动态调整评分权重

        Args:
            intent: 用户意图

        Returns:
            dict: 动态权重配置
        """
        # 默认权重
        weights = {
            'similarity': 0.30,
            'heat': 0.20,
            'freshness': 0.25,
            'user_interest': 0.15,
            'quality': 0.10,
            'repetition_penalty': 0.15
        }

        # 如果用户明确要求某类别，增加相似度权重
        if intent['category_request']:
            weights['similarity'] = 0.40
            weights['heat'] = 0.15
            weights['freshness'] = 0.20

        # 如果用户要求最新新闻，增加新鲜度权重
        if intent['require_fresh']:
            weights['freshness'] = 0.40
            weights['similarity'] = 0.25
            weights['heat'] = 0.15

        # 如果用户根据历史推荐，增加用户兴趣权重
        if intent['query_type'] == 'history':
            weights['user_interest'] = 0.35
            weights['similarity'] = 0.25
            weights['freshness'] = 0.20

        # 确保权重总和为1.0
        total = sum(weights.values())
        for key in weights:
            weights[key] /= total

        return weights

    def close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.db:
            self.db.close()


def beginIntelligentRecommend(user_input, user_id, top_n=20):
    """
    智能推荐入口函数

    Args:
        user_input: 用户输入
        user_id: 用户ID
        top_n: 返回数量

    Returns:
        list: 推荐结果
    """
    agent = NewsRecommendAgent()
    try:
        result = agent.intelligent_recommend(user_input, user_id, top_n)
        return result
    finally:
        agent.close()
