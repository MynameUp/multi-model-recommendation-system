"""
    Author: AI Assistant
    Desc: 新闻问答智能体 - 基于RAG的新闻问答系统（LLM增强版）
    Features:
        - 新闻向量化存储
        - 语义检索
        - 上下文拼接
        - LLM智能问答生成
        - 自动降级机制
"""
import json
import logging
from typing import List, Dict
import numpy as np
from news_api.qa_dao import QAHistoryDAO
import pymysql
from sentence_transformers import SentenceTransformer
import faiss
from Spider.settings import DB_HOST, DB_USER, DB_PASSWD, DB_NAME, DB_PORT
from Recommend.LLMInterface import create_llm
import os
import ssl
logger = logging.getLogger(__name__)


class NewsQAEmbedding:
    """新闻向量化处理器"""

    def __init__(self, model_name='paraphrase-multilingual-MiniLM-L12-v2'):
        """
        初始化向量模型

        Args:
            model_name: 预训练模型名称，支持多语言
        """
        logger.info(f"加载向量模型: {model_name}")

        # 禁用SSL验证以解决证书问题（仅用于开发环境）
        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            # 设置环境变量禁用SSL验证
            os.environ['CURL_CA_BUNDLE'] = ''
            os.environ['REQUESTS_CA_BUNDLE'] = ''

            # 创建不验证SSL的上下文
            ssl._create_default_https_context = ssl._create_unverified_context

            logger.info("已禁用SSL验证以加载模型")
        except Exception as e:
            logger.warning(f"禁用SSL验证失败: {e}，将尝试正常加载")

        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"向量维度: {self.embedding_dim}")

    def encode(self, texts: List[str]) -> np.ndarray:
        """
        将文本转换为向量

        Args:
            texts: 文本列表

        Returns:
            numpy数组，形状为 (len(texts), embedding_dim)
        """
        if not texts:
            return np.array([])

        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            normalize_embeddings=True
        )
        return embeddings

    def encode_single(self, text: str) -> np.ndarray:
        """
        将单个文本转换为向量

        Args:
            text: 输入文本

        Returns:
            一维numpy数组
        """
        return self.model.encode([text], normalize_embeddings=True)[0]


class NewsVectorStore:
    """新闻向量存储管理器（基于FAISS + MySQL）"""

    def __init__(self):
        self.db = self.connect()
        self.cursor = self.db.cursor()
        self.embedding_model = NewsQAEmbedding()

        # FAISS索引（内存中）
        self.faiss_index = None
        self.news_id_mapping = []  # 映射FAISS索引到news_id

        # 初始化FAISS索引
        self._init_faiss_index()

        # 加载已有数据
        self._load_existing_vectors()

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

    def _init_faiss_index(self):
        """初始化FAISS索引"""
        try:
            # 使用内积索引（因为向量已归一化，内积等价于余弦相似度）
            dimension = self.embedding_model.embedding_dim
            self.faiss_index = faiss.IndexFlatIP(dimension)

            logger.info(f"FAISS索引初始化完成，维度: {dimension}")
        except ImportError:
            logger.error("未安装faiss库，请运行: pip install faiss-cpu")
            raise

    def _load_existing_vectors(self):
        """从数据库加载已有的向量数据"""
        try:
            sql = "SELECT news_id, vector_data FROM news_api_newsvector WHERE vector_data IS NOT NULL"
            self.cursor.execute(sql)
            results = self.cursor.fetchall()

            if results:
                vectors = []
                for news_id, vector_json in results:
                    try:
                        vector = np.array(json.loads(vector_json), dtype=np.float32)
                        vectors.append(vector)
                        self.news_id_mapping.append(news_id)
                    except Exception as e:
                        logger.warning(f"加载新闻{news_id}的向量失败: {e}")

                if vectors:
                    vectors_array = np.array(vectors, dtype=np.float32)
                    self.faiss_index.add(vectors_array)
                    logger.info(f"已加载 {len(vectors)} 个新闻向量")
            else:
                logger.info("数据库中暂无向量数据，需要初始化")

        except Exception as e:
            logger.error(f"加载向量数据失败: {e}")

    def build_vector_for_news(self, news_id: int, title: str, summary: str, content: str) -> bool:
        """
        为单篇新闻构建向量并存储

        Args:
            news_id: 新闻ID
            title: 标题
            summary: 摘要
            content: 正文

        Returns:
            是否成功
        """
        try:
            # 拼接文本：标题 + 摘要 + 正文（限制长度）
            combined_text = f"{title} {summary} {content[:2000]}"

            # 生成向量
            vector = self.embedding_model.encode_single(combined_text)

            # 存储到MySQL
            vector_json = json.dumps(vector.tolist())

            # 检查是否已存在
            check_sql = "SELECT COUNT(*) FROM news_api_newsvector WHERE news_id = %s"
            self.cursor.execute(check_sql, (news_id,))
            exists = self.cursor.fetchone()[0] > 0

            if exists:
                update_sql = """
                    UPDATE news_api_newsvector 
                    SET vector_data = %s, updated_at = NOW() 
                    WHERE news_id = %s
                """
                self.cursor.execute(update_sql, (vector_json, news_id))
            else:
                insert_sql = """
                    INSERT INTO news_api_newsvector (news_id, vector_data, created_at, updated_at) 
                    VALUES (%s, %s, NOW(), NOW())
                """
                self.cursor.execute(insert_sql, (news_id, vector_json))

            self.db.commit()

            # 添加到FAISS索引
            vector_2d = vector.reshape(1, -1).astype(np.float32)
            self.faiss_index.add(vector_2d)
            self.news_id_mapping.append(news_id)

            logger.info(f"新闻{news_id}向量构建成功")
            return True

        except Exception as e:
            logger.error(f"为新闻{news_id}构建向量失败: {e}")
            self.db.rollback()
            return False

    def search_similar_news(self, query_text: str, top_k: int = 10) -> List[Dict]:
        """
        搜索与查询文本相似的新闻

        Args:
            query_text: 查询文本
            top_k: 返回最相似的K条新闻

        Returns:
            相似新闻列表，包含news_id和相似度分数
        """
        try:
            # 生成查询向量
            query_vector = self.embedding_model.encode_single(query_text)
            query_vector_2d = query_vector.reshape(1, -1).astype(np.float32)

            # 在FAISS中搜索
            scores, indices = self.faiss_index.search(query_vector_2d, top_k)

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.news_id_mapping):
                    news_id = self.news_id_mapping[idx]
                    results.append({
                        'news_id': news_id,
                        'similarity': float(score)
                    })

            # 按相似度排序
            results.sort(key=lambda x: x['similarity'], reverse=True)

            logger.info(f"搜索查询: {query_text[:50]}... 找到 {len(results)} 条结果")
            return results

        except Exception as e:
            logger.error(f"搜索相似新闻失败: {e}")
            return []

    def get_news_detail(self, news_id: int) -> Dict:
        """
        获取新闻详细信息

        Args:
            news_id: 新闻ID

        Returns:
            新闻详情字典
        """
        try:
            sql = """
                SELECT news_id, title, date, mainpage, origin, category, 
                       readnum, comments, keywords, pic_url
                FROM news_api_newsdetail 
                WHERE news_id = %s
            """
            self.cursor.execute(sql, (news_id,))
            columns = [desc[0] for desc in self.cursor.description]
            result = self.cursor.fetchone()

            if result:
                return dict(zip(columns, result))
            return {}

        except Exception as e:
            logger.error(f"获取新闻{news_id}详情失败: {e}")
            return {}

    def close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.db:
            self.db.close()


class NewsQAAgent:
    """新闻问答智能体（LLM增强版）"""

    def __init__(self, llm_type: str = "fallback", **llm_kwargs):
        """
        初始化新闻问答智能体

        Args:
            llm_type: LLM类型（chatglm/qwen/dashscope/zhipuai/fallback）
            **llm_kwargs: LLM初始化参数
        """
        self.vector_store = NewsVectorStore()
        self.db = self.vector_store.db
        self.cursor = self.vector_store.cursor

        # 初始化LLM
        logger.info(f"初始化LLM，类型: {llm_type}")
        self.llm = create_llm(llm_type, **llm_kwargs)

    def answer_question(self, user_id: int, news_id: int, question: str) -> Dict:
        """
        回答用户关于新闻的问题

        Args:
            user_id: 用户ID
            news_id: 新闻ID
            question: 用户问题

        Returns:
            包含答案和相关新闻的字典
        """
        logger.info(f"问答请求 - 用户:{user_id}, 新闻:{news_id}, 问题:{question}")

        # 1. 获取当前新闻详情
        current_news = self.vector_store.get_news_detail(news_id)
        if not current_news:
            return {
                'answer': '抱歉，找不到这篇新闻的详细信息。',
                'relatedNews': []
            }

        # 2. 检索相关新闻（基于问题语义）
        related_news_list = self.vector_store.search_similar_news(question, top_k=5)

        # 3. 过滤掉当前新闻
        related_news_list = [n for n in related_news_list if n['news_id'] != news_id]

        # 4. 构建上下文
        context = self._build_context(current_news, related_news_list[:3])

        # 5. 使用LLM生成答案
        answer = self._generate_answer_with_llm(question, context, current_news)

        # 6. 获取相关新闻的详细信息
        related_news_details = []
        for item in related_news_list[:5]:
            news_detail = self.vector_store.get_news_detail(item['news_id'])
            if news_detail:
                related_news_details.append({
                    'id': news_detail['news_id'],
                    'title': news_detail['title'],
                    'similarity': round(item['similarity'], 2),
                    'date': news_detail['date'],
                    'origin': news_detail['origin']
                })

        # 7. 记录问答历史（可选）
        self._save_qa_history(user_id, news_id, question, answer)

        result = {
            'answer': answer,
            'relatedNews': related_news_details
        }

        logger.info(f"问答完成 - 返回 {len(related_news_details)} 条相关新闻")
        return result

    def _build_context(self, current_news: Dict, related_news: List[Dict]) -> str:
        """
        构建问答上下文

        Args:
            current_news: 当前新闻详情
            related_news: 相关新闻列表

        Returns:
            上下文字符串
        """
        context_parts = []

        # 当前新闻信息
        context_parts.append("【当前新闻】")
        context_parts.append(f"标题: {current_news.get('title', '')}\n")
        context_parts.append(f"来源: {current_news.get('origin', '未知')}\n")
        context_parts.append(f"发布时间: {current_news.get('date', '未知')}\n")

        mainpage = current_news.get('mainpage', '')
        if mainpage:
            # 限制正文长度，避免超出LLM上下文窗口
            context_parts.append(f"\n正文内容:\n{mainpage[:2000]}...\n")

        # 关键词
        keywords = current_news.get('keywords', '')
        if keywords:
            context_parts.append(f"\n关键词: {keywords}\n")

        # 相关新闻信息
        if related_news:
            context_parts.append("\n【相关新闻】")
            for i, news in enumerate(related_news, 1):
                news_detail = self.vector_store.get_news_detail(news['news_id'])
                if news_detail:
                    title = news_detail.get('title', '')
                    similarity = news.get('similarity', 0)
                    context_parts.append(f"{i}. {title} (相似度: {similarity:.2f})")

        return "\n".join(context_parts)

    def _generate_answer_with_llm(self, question: str, context: str, current_news: Dict) -> str:
        """
        使用LLM生成问题答案

        Args:
            question: 用户问题
            context: 上下文信息
            current_news: 当前新闻

        Returns:
            生成的答案
        """
        # 构建Prompt
        prompt = self._build_prompt(question, context, current_news)

        try:
            # 调用LLM生成答案
            answer = self.llm.generate(
                prompt=prompt,
                max_length=512,
                temperature=0.7
            )

            if answer and len(answer.strip()) > 10:
                return answer.strip()
            else:
                logger.warning("LLM返回答案过短，使用规则生成")
                return self._generate_answer_by_rules(question, context, current_news)

        except Exception as e:
            logger.error(f"LLM生成答案失败: {e}，降级到规则生成")
            return self._generate_answer_by_rules(question, context, current_news)

    def _build_prompt(self, question: str, context: str, current_news: Dict) -> str:
        """
        构建LLM提示词

        Args:
            question: 用户问题
            context: 上下文
            current_news: 当前新闻

        Returns:
            提示词字符串
        """
        prompt_template = """你是一个专业的新闻问答助手。请根据提供的新闻内容，准确、简洁地回答用户的问题。
                            【要求】
                            1. 答案必须基于提供的新闻内容，不要编造信息
                            2. 如果新闻中没有相关信息，请明确说明
                            3. 答案要简洁明了，控制在200字以内
                            4. 使用中文回答
                            5. 保持客观中立的态度
                            【新闻内容】
                            {context}
                            【用户问题】
                            {question}
                            【你的回答】
                            """
        prompt = prompt_template.format(
            context=context,
            question=question
        )

        return prompt

    def _generate_answer_by_rules(self, question: str, context: str, current_news: Dict) -> str:
        """
        基于规则生成答案（降级方案）

        Args:
            question: 用户问题
            context: 上下文
            current_news: 当前新闻

        Returns:
            生成的答案
        """
        question_lower = question.lower()

        # 问题类型识别
        if any(keyword in question for keyword in ['讲了什么', '主要内容', '核心观点', '说什么']):
            return self._generate_summary_answer(current_news)

        elif any(keyword in question for keyword in ['关键人物', '重要人物', '提到谁']):
            return self._extract_key_persons(current_news)

        elif any(keyword in question for keyword in ['背景', '原因', '为什么发生']):
            return self._generate_background_answer(current_news, context)

        elif any(keyword in question for keyword in ['重要', '意义', '影响', '价值']):
            return self._generate_importance_answer(current_news, context)

        elif any(keyword in question for keyword in ['类似', '相关', '对比']):
            return self._generate_comparison_answer(context, current_news)

        else:
            # 通用答案
            return self._generate_general_answer(question, context, current_news)

    def _generate_summary_answer(self, news: Dict) -> str:
        """生成新闻摘要答案"""
        title = news.get('title', '')
        mainpage = news.get('mainpage', '')

        # 提取前200字作为摘要
        summary = mainpage[:200] if mainpage else ''

        answer = f"这篇新闻的标题是《{title}》。\n\n"
        if summary:
            answer += f"主要内容：{summary}...\n"

        answer += f"\n这条新闻来自{news.get('origin', '未知来源')}，发布于{news.get('date', '未知时间')}。"

        return answer

    def _extract_key_persons(self, news: Dict) -> str:
        """提取关键人物"""
        mainpage = news.get('mainpage', '')
        title = news.get('title', '')

        # 简单的人名提取（可以改进为使用NER模型）
        import re
        persons = []

        # 常见的称谓模式
        patterns = [
            r'([\u4e00-\u9fa5]{2,4})(?:先生|女士|教授|博士|主席|总理|部长|局长)',
            r'([\u4e00-\u9fa5·]{2,5})(?:表示|指出|认为|说|强调)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, title + mainpage[:500])
            persons.extend([m[0] if isinstance(m, tuple) else m for m in matches])

        # 去重
        persons = list(set(persons))[:5]

        if persons:
            answer = f"这篇新闻中提到的关键人物包括：\n"
            for i, person in enumerate(persons, 1):
                answer += f"{i}. {person}\n"
        else:
            answer = "根据新闻内容，没有明确提及具体的人物姓名。建议您阅读完整新闻以获取更多信息。"

        return answer

    def _generate_background_answer(self, news: Dict, context: str) -> str:
        """生成背景信息答案"""
        title = news.get('title', '')
        mainpage = news.get('mainpage', '')

        answer = f"关于《{title}》的背景信息：\n\n"

        # 尝试从正文中提取背景信息（通常在开头或结尾）
        paragraphs = mainpage.split('\n')
        background_info = ""

        # 取前两段作为背景
        for para in paragraphs[:2]:
            if len(para) > 50:
                background_info = para
                break

        if background_info:
            answer += f"{background_info}\n\n"

        answer += "这条新闻反映了当前社会的相关动态，建议您结合相关新闻一起了解更全面的信息。"

        return answer

    def _generate_importance_answer(self, news: Dict, context: str) -> str:
        """生成重要性分析答案"""
        title = news.get('title', '')
        category = news.get('category', 0)
        readnum = news.get('readnum', 0)
        comments = news.get('comments', 0)

        category_map = {
            0: "美股", 1: "国内", 2: "国际", 3: "国际",
            4: "体育", 5: "娱乐", 6: "军事",
            7: "科技", 8: "财经", 9: "股市"
        }

        category_name = category_map.get(category, "其他")

        answer = f"《{title}》这条新闻的重要性体现在以下几个方面：\n\n"

        # 1. 热度指标
        if readnum > 5000 or comments > 100:
            answer += f"1. **关注度高**：该新闻已获得{readnum}次阅读和{comments}条评论，说明公众对此话题高度关注。\n\n"
        else:
            answer += f"1. **专业价值**：虽然关注度不是特别高，但在{category_name}领域具有专业价值。\n\n"

        # 2. 类别重要性
        if category in [1, 2, 7, 8]:  # 国内、国际、科技、财经
            answer += f"2. **领域重要性**：作为{category_name}类新闻，这类信息对于了解当前社会/经济发展趋势具有重要意义。\n\n"
        else:
            answer += f"2. **领域价值**：属于{category_name}领域，对关注该领域的读者具有参考价值。\n\n"

        answer += "3. **时效性**：新闻报道的是最新发生的事件，及时了解有助于把握当前动态。\n"

        return answer

    def _generate_comparison_answer(self, context: str, current_news: Dict) -> str:
        """生成对比分析答案"""
        title = current_news.get('title', '')

        answer = f"关于《{title}》的相关新闻对比：\n\n"

        # 从上下文中提取相关新闻
        if "【相关新闻】" in context:
            related_section = context.split("【相关新闻】")[1]
            answer += f"我们找到了以下几条相关新闻：\n\n{related_section.strip()}\n\n"
            answer += "这些新闻从不同角度报道了类似事件，您可以对比阅读以获得更全面的理解。"
        else:
            answer += "目前没有找到太多直接相关的新闻进行对比。建议您关注后续的相关报道。"

        return answer

    def _generate_general_answer(self, question: str, context: str, current_news: Dict) -> str:
        """生成通用答案"""
        title = current_news.get('title', '')
        mainpage = current_news.get('mainpage', '')

        answer = f"针对您的问题，我基于新闻《{title}》的内容为您提供以下信息：\n\n"

        # 提取相关内容（简单关键词匹配）
        question_words = question.replace('？', '').replace('?', '').split()

        relevant_sentences = []
        sentences = mainpage.split('。')

        for sentence in sentences:
            if any(word in sentence for word in question_words if len(word) > 1):
                relevant_sentences.append(sentence)

        if relevant_sentences:
            answer += "新闻中提到：\n"
            for sent in relevant_sentences[:3]:
                answer += f"- {sent}。\n"
        else:
            # 如果没有找到直接相关的内容，返回新闻摘要
            summary = mainpage[:300] if mainpage else ""
            if summary:
                answer += f"新闻的主要内容是：{summary}...\n"
            else:
                answer += "抱歉，我无法从当前新闻中找到与您问题直接相关的信息。"

        answer += "\n如果您需要更深入的分析，建议查阅更多相关资料。"

        return answer

    def _save_qa_history(self, user_id: int, news_id: int, question: str, answer: str):
        """保存问答历史记录"""
        try:
            QAHistoryDAO.save_qa_record(user_id, news_id, question, answer)
            logger.info(f"问答历史已保存 - 用户:{user_id}, 新闻:{news_id}")
        except Exception as e:
            logger.error(f"保存问答历史失败: {e}")

    def close(self):
        """关闭连接"""
        self.vector_store.close()


def beginNewsQA(user_id: int, news_id: int, question: str, llm_type: str = "fallback", **llm_kwargs) -> Dict:
    """
    新闻问答入口函数

    Args:
        user_id: 用户ID
        news_id: 新闻ID
        question: 用户问题
        llm_type: LLM类型（chatglm/qwen/dashscope/zhipuai/fallback）
        **llm_kwargs: LLM初始化参数

    Returns:
        问答结果字典
    """
    agent = NewsQAAgent(llm_type=llm_type, **llm_kwargs)
    try:
        result = agent.answer_question(user_id, news_id, question)
        return result
    finally:
        agent.close()


def initNewsVectors(batch_size: int = 100) -> int:
    """
    初始化新闻向量（批量处理）

    Args:
        batch_size: 批处理大小

    Returns:
        成功处理的新闻数量
    """
    vector_store = NewsVectorStore()
    success_count = 0

    try:
        # 获取所有新闻
        sql = """
            SELECT news_id, title, mainpage, origin 
            FROM news_api_newsdetail 
            ORDER BY news_id DESC
            LIMIT 1000
        """
        vector_store.cursor.execute(sql)
        news_list = vector_store.cursor.fetchall()

        logger.info(f"开始初始化新闻向量，共 {len(news_list)} 篇新闻")

        for i, (news_id, title, mainpage, origin) in enumerate(news_list):
            if not title or not mainpage:
                continue

            # 摘要取前200字
            summary = mainpage[:200] if mainpage else ""

            success = vector_store.build_vector_for_news(
                news_id=news_id,
                title=title,
                summary=summary,
                content=mainpage
            )

            if success:
                success_count += 1

            if (i + 1) % batch_size == 0:
                logger.info(f"已处理 {i + 1}/{len(news_list)} 篇新闻")

        logger.info(f"向量初始化完成，成功处理 {success_count} 篇新闻")
        return success_count

    except Exception as e:
        logger.error(f"初始化向量失败: {e}")
        return success_count
    finally:
        vector_store.close()
