"""
    Desc: 新闻问答智能体 - 基于RAG的新闻问答系统（仅使用魔塔社区API）
    Features:
        - 新闻向量化存储
        - 语义检索
        - 上下文拼接
        - 魔塔社区LLM智能问答生成
        - 自动降级机制
"""
import json
import logging
from typing import List, Dict
import numpy as np
from news_api.qa_dao import QAHistoryDAO
import pymysql
from Spider.settings import DB_HOST, DB_USER, DB_PASSWD, DB_NAME, DB_PORT
from Recommend.LLMInterface import create_llm, get_qa_params

logger = logging.getLogger(__name__)


class NewsQAEmbedding:
    """新闻向量化处理器（简化版，使用TF-IDF避免模型下载问题）"""

    def __init__(self):
        """
        初始化向量模型（使用TF-IDF，无需下载任何模型）
        """
        logger.info("初始化TF-IDF向量器（无需下载模型）")

        from sklearn.feature_extraction.text import TfidfVectorizer

        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=384,
            stop_words=None,
            ngram_range=(1, 2),
            sublinear_tf=True
        )
        self.is_fitted = False
        self.embedding_dim = 384

        logger.info(f"TF-IDF向量器初始化完成，维度: {self.embedding_dim}")

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

        if not self.is_fitted:
            # 首次使用时拟合
            self.tfidf_vectorizer.fit(texts)
            self.is_fitted = True
        else:
            # 后续使用时部分拟合
            try:
                self.tfidf_vectorizer.partial_fit(texts)
            except:
                pass

        vectors = self.tfidf_vectorizer.transform(texts).toarray()

        # 归一化
        from sklearn.preprocessing import normalize
        vectors = normalize(vectors)

        return vectors

    def encode_single(self, text: str) -> np.ndarray:
        """
        将单个文本转换为向量

        Args:
            text: 输入文本

        Returns:
            一维numpy数组
        """
        return self.encode([text])[0]


class NewsVectorStore:
    """新闻向量存储管理器（基于FAISS + MySQL）"""

    def __init__(self):
        self.db = self.connect()
        self.cursor = self.db.cursor()
        self.embedding_model = NewsQAEmbedding()

        # ====== ✨ 注入核心工业级 Trick：全局预拟合，彻底锁死 384 维度 ======
        try:
            self.cursor.execute("SELECT title, mainpage FROM news_api_newsdetail LIMIT 300")
            rows = self.cursor.fetchall()
            # 拼接基础语料
            corpus = [f"{r[0]} {r[1][:300]}" for r in rows if r[0] or r[1]]
            
            # 💡 核心大招：塞入 384 个绝不重复的虚拟 Token，确保总词汇量必超 384
            dummy_tokens = [f"__dummy_lock_dim_{i}__" for i in range(384)]
            corpus.extend(dummy_tokens)
            
            # 强行触发拟合
            self.embedding_model.tfidf_vectorizer.fit(corpus)
            self.embedding_model.is_fitted = True
            logger.info("✅ [系统核心修复] TF-IDF 成功完成全局预建，特征维度已永久锁死为 384！")
        except Exception as e:
            logger.error(f"⚠️ TF-IDF 全局预建失败: {e}")
        # ==================================================================

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
            import faiss
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
                # 💡 UPDATE 语句先给 vector_data 赋值，再传 news_id 条件
                self.cursor.execute(update_sql, (vector_json, news_id)) 
            else:
                insert_sql = """
                    INSERT INTO news_api_newsvector (news_id, vector_data, created_at, updated_at) 
                    VALUES (%s, %s, NOW(), NOW())
                """
                # 💡 再次确认为 (news_id, vector_json)，千万不要写反了
                self.cursor.execute(insert_sql, (news_id, vector_json))

            self.db.commit()

            # 添加到FAISS索引
            vector_2d = vector.reshape(1, -1).astype(np.float32)
            self.faiss_index.add(vector_2d)
            self.news_id_mapping.append(news_id)

            logger.info(f"新闻{news_id}向量构建成功")
            return True

        except Exception as e:
            # 💡 恢复为正常的日志记录，删掉 sys.exit(0)，让循环能够顺畅地处理完所有新闻
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
            # 检查FAISS索引是否为空
            if self.faiss_index.ntotal == 0:
                logger.warning("FAISS索引为空，无法搜索相似新闻")
                logger.info("提示: 请先运行 'python manage.py init_vectors' 初始化向量数据")
                return []

            # 生成查询向量
            query_vector = self.embedding_model.encode_single(query_text)
            query_vector_2d = query_vector.reshape(1, -1).astype(np.float32)

            # 在FAISS中搜索
            scores, indices = self.faiss_index.search(query_vector_2d, top_k)

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx != -1 and idx < len(self.news_id_mapping):  # 过滤无效索引
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
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
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
    """新闻问答智能体（仅使用魔塔社区API）"""

    def __init__(self, llm_type: str = "modelscope", **llm_kwargs):
        """
        初始化新闻问答智能体

        Args:
            llm_type: LLM类型（固定为 modelscope 或 fallback）
            **llm_kwargs: LLM初始化参数（api_token, model_name等）
        """
        self.vector_store = NewsVectorStore()
        self.db = self.vector_store.db
        self.cursor = self.vector_store.cursor

        # 初始化LLM（使用魔塔社区API）
        logger.info(f"初始化LLM，类型: {llm_type}")
        self.llm = create_llm(llm_type=llm_type, **llm_kwargs)

    def answer_question(self, user_id: int, news_id: int, question: str,
                       use_external_knowledge: bool = True) -> Dict:
        """
        回答用户关于新闻的问题

        Args:
            user_id: 用户ID
            news_id: 新闻ID
            question: 用户问题
            use_external_knowledge: 是否允许使用外部知识（LLM训练数据）
                                    True - 当数据库信息不足时，使用LLM的外部知识补充
                                    False - 严格基于数据库中的新闻内容回答

        Returns:
            包含答案和相关新闻的字典，结构如下：
            {
                'answer': '答案文本',
                'relatedNews': [...],  # 相关新闻列表
                'answerSource': 'database' | 'external' | 'mixed' | 'fallback'
            }

            answerSource 说明：
            - 'database': 答案完全来自数据库中的新闻
            - 'external': 答案来自LLM的外部知识（数据库中无相关信息）
            - 'mixed': 答案结合了数据库内容和外部知识
            - 'fallback': 使用了降级方案（规则生成）
        """
        logger.info(f"问答请求 - 用户:{user_id}, 新闻:{news_id}, 问题:{question}, 外部知识:{use_external_knowledge}")

        # 1. 获取当前新闻详情
        current_news = self.vector_store.get_news_detail(news_id)
        if not current_news:
            return {
                'answer': '抱歉，找不到这篇新闻的详细信息。',
                'relatedNews': [],
                'answerSource': 'none'
            }

        # 2. 检索相关新闻（基于问题语义）
        related_news_list = self.vector_store.search_similar_news(question, top_k=5)

        # 3. 过滤掉当前新闻
        related_news_list = [n for n in related_news_list if n['news_id'] != news_id]

        # 4. 构建上下文
        context = self._build_context(current_news, related_news_list[:3])

        # 5. 使用魔塔社区LLM生成答案（支持外部知识）
        answer, answer_source = self._generate_answer_with_llm(
            question, context, current_news,
            use_external_knowledge=use_external_knowledge
        )

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
            'relatedNews': related_news_details,
            'answerSource': answer_source  # 标注答案来源
        }

        logger.info(f"问答完成 - 返回 {len(related_news_details)} 条相关新闻, 来源: {answer_source}")
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

    def _generate_answer_with_llm(self, question: str, context: str, current_news: Dict,
                                 use_external_knowledge: bool = True) -> tuple:
        """
        使用魔塔社区LLM生成问题答案

        Args:
            question: 用户问题
            context: 上下文信息（包含当前新闻和相关文章）
            current_news: 当前新闻详情
            use_external_knowledge: 是否允许使用外部知识
                                    True - LLM可以结合自己的训练知识回答
                                    False - 严格基于context中的新闻内容

        Returns:
            元组 (answer, answer_source)：
            - answer: 生成的答案文本
            - answer_source: 答案来源标识
                * 'database' - 答案来自数据库新闻
                * 'external' - 答案来自LLM外部知识
                * 'mixed' - 混合来源
                * 'fallback' - 降级方案
        """
        # 构建Prompt（根据是否允许外部知识选择不同的模板）
        prompt = self._build_prompt(question, context, current_news, use_external_knowledge)

        try:
            # 调用LLM生成答案
            qa_params = get_qa_params()
            answer = self.llm.generate(
                prompt=prompt,
                max_length=qa_params['max_length'],
                temperature=qa_params['temperature']
            )

            if answer and len(answer.strip()) > 10:
                # 检测答案来源标识
                answer_source = self._detect_answer_source(answer, context)
                logger.info(f"LLM生成成功，答案来源: {answer_source}, 长度: {len(answer)}")
                return answer.strip(), answer_source
            else:
                logger.warning("LLM返回答案过短，使用规则生成")
                fallback_answer = self._generate_answer_by_rules(question, context, current_news)
                return fallback_answer, 'fallback'

        except Exception as e:
            logger.error(f"LLM生成答案失败: {e}，降级到规则生成")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            fallback_answer = self._generate_answer_by_rules(question, context, current_news)
            return fallback_answer, 'fallback'


    def _build_prompt(self, question: str, context: str, current_news: Dict,
                     use_external_knowledge: bool = True) -> str:
        """
        构建LLM提示词

        Args:
            question: 用户问题
            context: 上下文（包含当前新闻和相关文章的详细信息）
            current_news: 当前新闻详情
            use_external_knowledge: 是否允许使用外部知识

        Returns:
            提示词字符串

        Prompt设计思路：
        - 当允许外部知识时：采用"双源模式"，让LLM能够灵活结合新闻内容和自身知识
        - 当不允许外部知识时：采用"严格模式"，确保答案完全可追溯至数据库
        """
        if use_external_knowledge:
            # 双源模式：允许结合新闻内容和外部知识
            prompt_template = """你是一个专业的新闻问答助手，拥有丰富的知识库。请根据以下信息回答用户问题：

【重要说明】
1. 优先基于提供的【新闻内容】回答问题
2. 如果新闻内容中没有相关信息，可以使用你的【外部知识】补充回答
3. 必须在回答开头明确标注答案来源：
   - 如果答案主要来自新闻内容，标注为"[基于新闻]"
   - 如果答案主要来自你的知识库，标注为"[基于通用知识]"
   - 如果两者结合，标注为"[综合回答]"

【回答要求】
1. 答案要准确、简洁、客观中立
2. 控制在300字以内
3. 使用中文回答
4. 如果新闻内容与你的知识有冲突，以新闻内容为准
5. 如果完全无法回答，请说明原因

【新闻内容】
{context}

【用户问题】
{question}

【你的回答】（请先标注来源，再给出答案）
"""
        else:
            # 严格模式：仅基于新闻内容
            prompt_template = """你是一个专业的新闻问答助手。请严格基于提供的新闻内容，准确、简洁地回答用户的问题。

【严格要求】
1. 答案必须完全基于提供的新闻内容，不要使用任何外部知识
2. 如果新闻中没有相关信息，请明确说明"新闻中未提及此信息"
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

        logger.debug(f"Prompt构建完成，长度: {len(prompt)}, 模式: {'双源' if use_external_knowledge else '严格'}")
        return prompt

    def _detect_answer_source(self, answer: str, context: str) -> str:
        """
        检测答案来源

        Args:
            answer: LLM生成的答案文本
            context: 原始上下文（用于辅助判断）

        Returns:
            答案来源标识字符串：
            - 'database': 答案来自数据库新闻
            - 'external': 答案来自LLM外部知识
            - 'mixed': 混合来源

        检测逻辑：
        1. 首先检查答案中是否包含明确的来源标记（由LLM按Prompt要求添加）
        2. 如果没有标记，则通过关键词匹配进行推断
        3. 默认情况下认为来自数据库（保守策略）
        """
        # 检查答案中是否包含来源标识（由LLM按Prompt要求添加）
        if "[基于新闻]" in answer or "基于新闻" in answer:
            return 'database'
        elif "[基于通用知识]" in answer or "基于通用知识" in answer or "外部知识" in answer:
            return 'external'
        elif "[综合回答]" in answer or "综合" in answer:
            return 'mixed'
        else:
            # 如果没有明确标记，尝试通过关键词推断
            # 如果答案中包含"新闻中提到"、"根据报道"等词汇，可能来自数据库
            database_indicators = ["新闻中提到", "根据报道", "文中指出", "该新闻"]
            external_indicators = ["一般来说", "通常情况下", "据了解", "历史上"]

            db_score = sum(1 for indicator in database_indicators if indicator in answer)
            ext_score = sum(1 for indicator in external_indicators if indicator in answer)

            if db_score > ext_score:
                return 'database'
            elif ext_score > db_score:
                return 'external'
            else:
                # 无法判断时，默认认为来自数据库（保守策略）
                return 'database'



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
        title = current_news.get('title', '')
        mainpage = current_news.get('mainpage', '')

        answer = f"关于《{title}》这条新闻：\n\n"

        if mainpage:
            answer += f"新闻主要内容：{mainpage[:300]}...\n\n"

        answer += "建议您阅读完整新闻以获取更多详细信息。"

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


def beginNewsQA(user_id: int, news_id: int, question: str,
                llm_type: str = "dashscope",
                use_external_knowledge: bool = True,
                **llm_kwargs) -> Dict:
    """
    新闻问答入口函数

    Args:
        user_id: 用户ID
        news_id: 新闻ID
        question: 用户问题
        llm_type: LLM类型（默认dashscope，即阿里云百炼）
                  - "dashscope": 阿里云百炼API（默认，推荐）
                  - "modelscope": 魔塔社区API（备用）
                  - "fallback": 降级方案
        use_external_knowledge: 是否允许使用外部知识（默认True）
        **llm_kwargs: LLM初始化参数
            - api_key: 阿里云百炼API Key（dashscope模式）
            - api_token: 魔塔社区Token（modelscope模式）
            - model_name: 模型名称（可选）

    Returns:
        问答结果字典

    使用示例：
        # 使用阿里云百炼（默认）
        >>> result = beginNewsQA(
        ...     user_id=100001,
        ...     news_id=12345,
        ...     question="阿森纳是谁？"
        ... )

        # 使用魔塔社区
        >>> result = beginNewsQA(
        ...     user_id=100001,
        ...     news_id=12345,
        ...     question="阿森纳是谁？",
        ...     llm_type="modelscope",
        ...     api_token="your_modelscope_token"
        ... )
    """
    agent = NewsQAAgent(llm_type=llm_type, **llm_kwargs)
    try:
        result = agent.answer_question(
            user_id, news_id, question,
            use_external_knowledge=use_external_knowledge
        )
        return result
    finally:
        agent.close()


def global_knowledge_qa(question: str, llm_type: str = "dashscope", **llm_kwargs) -> str:
    """
    基于LLM全局知识的问答（不依赖数据库）- 快速模式改造版
    """
    # 💡 方案A核心拦截逻辑：
    # 强制将快速问答路由到 dashscope（百炼），并指定使用高性价比的 qwen-plus 模型
    llm_type = "dashscope"
    llm_kwargs["model_name"] = "qwen-plus"

    logger.info(f"🚀 触发快速模式问答 - 问题: {question}, 通道: {llm_type}, 模型: {llm_kwargs['model_name']}")

    try:
        # 创建LLM实例
        llm = create_llm(llm_type=llm_type, **llm_kwargs)

        # 构建Prompt
        prompt = f"""你是一个专业的新闻和知识问答助手。请回答用户的以下问题：

【要求】
1. 提供准确、客观、有用的信息
2. 如果不确定，请诚实说明
3. 控制在300字以内
4. 使用中文回答
5. 保持专业和中立的态度
6. 如果涉及多个方面，请条理清晰地分点说明

【用户问题】
{question}

【你的回答】
"""

        # 生成答案
        qa_params = get_qa_params()
        answer = llm.generate(
            prompt=prompt,
            max_length=qa_params['max_length'],
            temperature=qa_params['temperature']
        )

        logger.info("✅ 快速模式问答完成")
        return answer.strip() if answer else "抱歉，暂时无法回答这个问题。"

    except Exception as e:
        logger.error(f"❌ 快速模式问答失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return "抱歉，服务暂时不可用，请稍后重试。"


# ... existing code ...


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

