# -*- coding: utf-8 -*-
"""
    Author: AI Architect
    Desc: PromptMM 在线极速推理引擎

    从 .npy 文件加载 Student_LightGCN 导出的 User/Item Embedding,
    利用 NumPy 矩阵点积实现毫秒级精排打分:

        score_u,i = UserEmbedding[u] · ItemEmbedding[i]^T

    特性:
        - 启动时一次性加载 .npy 到内存 (常驻)
        - 纯 NumPy 计算, 无 PyTorch 依赖, 无 GPU 依赖
        - 批量候选查询 (O(N_candidates · dim) 复杂度)
        - Cold Start 安全: 越界/加载失败时自动回退启发式打分
"""

import os
import logging
import random
from typing import List, Tuple, Optional

import numpy as np

from django.conf import settings

logger = logging.getLogger(__name__)


class PromptMMEngine:
    """
    PromptMM 精排引擎单例

    加载预导出的 User/Item Embedding .npy 矩阵,
    对外提供 rank() 方法进行个性化打分排序。

    Phase 3.2: 真实 .npy 加载 (取代 Phase 3.1 的桩代码)
    """

    def __init__(self):
        self._user_emb: Optional[np.ndarray] = None
        self._item_emb: Optional[np.ndarray] = None
        self._loaded = False
        self._load_error = None

        # 权重文件路径 (可通过 Django settings 覆盖)
        self.weights_dir = getattr(
            settings, 'PROMPTMM_WEIGHTS_DIR',
            os.path.join(os.path.dirname(__file__), 'weights')
        )

        self._load_embeddings()

    # -----------------------------------------------------------------
    #  加载逻辑
    # -----------------------------------------------------------------

    def _load_embeddings(self) -> bool:
        """从 .npy 文件加载 Embedding 矩阵"""
        user_path = os.path.join(self.weights_dir, 'user_embeddings.npy')
        item_path = os.path.join(self.weights_dir, 'item_embeddings.npy')

        if not os.path.exists(user_path) or not os.path.exists(item_path):
            self._load_error = (
                f"权重文件缺失: {user_path} / {item_path}。"
                f"请先运行: cd PromptMM/codes && python export_for_online.py"
            )
            logger.warning(f"PromptMMEngine: {self._load_error}")
            return False

        try:
            self._user_emb = np.load(user_path).astype(np.float32)
            self._item_emb = np.load(item_path).astype(np.float32)

            # 确保是 2D 矩阵
            if self._user_emb.ndim == 1:
                self._user_emb = self._user_emb.reshape(1, -1)
            if self._item_emb.ndim == 1:
                self._item_emb = self._item_emb.reshape(1, -1)

            self._loaded = True
            logger.info(
                f"PromptMMEngine 加载成功 | "
                f"user={self._user_emb.shape} | item={self._item_emb.shape} | "
                f"dim={self._user_emb.shape[1]} | "
                f"内存={(self._user_emb.nbytes + self._item_emb.nbytes) / 1024 / 1024:.1f}MB"
            )
            return True

        except Exception as e:
            self._load_error = str(e)
            logger.error(f"PromptMMEngine 加载失败: {e}")
            self._user_emb = None
            self._item_emb = None
            self._loaded = False
            return False

    def is_loaded(self) -> bool:
        return self._loaded

    def reload(self) -> bool:
        """热重载权重 (模型更新后调用)"""
        logger.info("PromptMMEngine 热重载...")
        return self._load_embeddings()

    # -----------------------------------------------------------------
    #  推理接口
    # -----------------------------------------------------------------

    def rank(
        self,
        userid: int,
        candidate_ids: List[int],
        top_k: int = 20,
    ) -> List[Tuple[int, float]]:
        """
        对候选新闻列表进行个性化精排

        核心公式:
            score[i] = UserEmbedding[userid] · ItemEmbedding[candidate_ids]^T

        Args:
            userid: 用户 ID (整数, 用作 Embedding 行索引)
            candidate_ids: 候选新闻 ID 列表
            top_k: 返回 Top-K

        Returns:
            [(news_id, score), ...]  按分数降序排列
        """
        if not candidate_ids:
            return []

        # ---- 尝试模型推理 ----
        if self._loaded and self._user_emb is not None and self._item_emb is not None:
            try:
                return self._model_rank(userid, candidate_ids, top_k)
            except Exception as e:
                logger.warning(f"模型推理异常, 回退启发式: {e}")

        # ---- Fallback: 启发式排序 ----
        return self._fallback_rank(userid, candidate_ids, top_k)

    # -----------------------------------------------------------------
    #  模型推理核心
    # -----------------------------------------------------------------

    def _model_rank(
        self,
        userid: int,
        candidate_ids: List[int],
        top_k: int,
    ) -> List[Tuple[int, float]]:
        """
        NumPy 批量点积打分
        score = UserEmbedding[user_idx] @ ItemEmbedding[candidate_indices]^T

        时间复杂度: O(|candidates| · dim)  ← 纯矩阵乘法, 毫秒级
        """
        u_dim = self._user_emb.shape[0]
        i_dim = self._item_emb.shape[0]
        emb_dim = self._user_emb.shape[1]

        # ---- Cold Start 处理: userid 越界 ----
        if userid < 0 or userid >= u_dim:
            logger.debug(
                f"User {userid} 超出 Embedding 范围 [0, {u_dim}), 使用零向量"
            )
            user_vec = np.zeros(emb_dim, dtype=np.float32)
        else:
            user_vec = self._user_emb[userid]

        # ---- 过滤越界的 candidate_ids ----
        valid_candidates = []
        valid_indices = []
        for nid in candidate_ids:
            if 0 <= nid < i_dim:
                valid_candidates.append(nid)
                valid_indices.append(nid)

        if not valid_candidates:
            logger.debug(f"所有候选 ID 越界 [{candidate_ids[0]}...], 回退启发式")
            return self._fallback_rank(userid, candidate_ids, top_k)

        # ---- 批量点积 ----
        item_vectors = self._item_emb[valid_indices]    # [N, dim]
        scores = np.dot(user_vec, item_vectors.T)        # [N]
        # 将点积映射到 [0, 1] 区间 (sigmoid 平滑)
        scores = 1.0 / (1.0 + np.exp(-scores))

        # ---- 排序 ----
        scored = list(zip(valid_candidates, scores.astype(np.float64)))
        scored.sort(key=lambda x: x[1], reverse=True)

        # ---- Cold Start: 越界的候选补到末尾 (低分) ----
        for nid in candidate_ids:
            if nid < 0 or nid >= i_dim:
                scored.append((nid, 0.01))

        return scored[:top_k]

    # -----------------------------------------------------------------
    #  Fallback 启发式打分 (当模型不可用时)
    # -----------------------------------------------------------------

    def _fallback_rank(
        self,
        userid: int,
        candidate_ids: List[int],
        top_k: int,
    ) -> List[Tuple[int, float]]:
        """
        综合热度 + 新鲜度 + 用户标签匹配的启发式排序
        """
        from news_api.models import newsdetail, newshot, user as UserModel

        news_map = {
            n.news_id: n
            for n in newsdetail.objects.filter(news_id__in=candidate_ids)
        }
        hot_map = {
            h.news_id: h.news_hot
            for h in newshot.objects.filter(news_id__in=candidate_ids)
        }

        user_tags = set()
        try:
            u = UserModel.objects.filter(userid=userid).first()
            if u and u.tags:
                user_tags = set(u.tags.split(','))
        except Exception:
            pass

        scored = []
        for nid in candidate_ids:
            news = news_map.get(nid)
            if not news:
                scored.append((nid, 0.0))
                continue

            hot = float(hot_map.get(nid, 0))
            hot_score = min(hot / 100.0, 1.0) if hot > 0 else 0.3

            freshness_score = 0.5
            try:
                from datetime import datetime
                date_str = str(news.date).replace('年', '-').replace('月', '-').replace('日', '')
                pub_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
                days_ago = (datetime.now() - pub_date).days
                freshness_score = max(0.0, 1.0 - days_ago / 30.0)
            except Exception:
                pass

            tag_score = 0.0
            if user_tags and news.keywords:
                news_kw = set(str(news.keywords).split(','))
                overlap = user_tags & news_kw
                if overlap:
                    tag_score = min(len(overlap) / max(len(user_tags), 1), 1.0)

            score = (
                0.35 * hot_score +
                0.25 * freshness_score +
                0.30 * tag_score +
                0.10 * random.uniform(0, 1)
            )
            scored.append((nid, round(score, 4)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


# =============================================================================
#  全局单例 + 便捷函数
# =============================================================================

_engine: Optional[PromptMMEngine] = None


def get_engine() -> PromptMMEngine:
    """获取 PromptMM 推理引擎单例 (线程安全: Django 单进程内共享)"""
    global _engine
    if _engine is None:
        _engine = PromptMMEngine()
    return _engine


def rank_candidates(
    userid: int,
    candidate_ids: List[int],
    top_k: int = 20,
) -> List[Tuple[int, float]]:
    """便捷函数: 对候选列表精排"""
    return get_engine().rank(userid, candidate_ids, top_k)


def reload_weights() -> bool:
    """便捷函数: 热重载权重"""
    return get_engine().reload()
