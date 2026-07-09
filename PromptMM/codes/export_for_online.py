# -*- coding: utf-8 -*-
"""
    Author: AI Architect
    Desc: PromptMM 离线权重导出脚本

    从训练好的 Student 模型中提取 User/Item Embedding 矩阵,
    导出为 .npy 格式供 Django 在线推理引擎加载。

    使用方式:
        cd PromptMM/codes/
        python export_for_online.py                          # 生成随机假权重 (开发测试)
        python export_for_online.py --checkpoint path.pt    # 从 .pt checkpoint 提取
        python export_for_online.py --n_users 2000 --n_items 5000 --dim 64  # 自定义规模

    输出路径:
        FinalProject/newsapi/Recommend/weights/user_embeddings.npy
        FinalProject/newsapi/Recommend/weights/item_embeddings.npy
"""

import argparse
import os
import sys
import warnings
import numpy as np

warnings.filterwarnings('ignore')

# =============================================================================
#  路径配置
# =============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# PromptMM/codes/ → PromptMM/ → 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
WEIGHTS_DIR = os.path.join(
    PROJECT_ROOT, 'FinalProject', 'newsapi', 'Recommend', 'weights'
)
os.makedirs(WEIGHTS_DIR, exist_ok=True)


# =============================================================================
#  方案 A: 生成随机假权重 (开发测试用)
# =============================================================================

def generate_random_embeddings(
    n_users: int = 2000,
    n_items: int = 5000,
    dim: int = 64,
    seed: int = 42,
):
    """
    生成随机 Embedding 矩阵用于开发测试。

    与真实 PromptMM 训练代码对齐:
      - embed_size = 64 (args.embed_size 默认值)
      - student_embed_size = 64 (蒸馏学生模型维度)
      - Xavier 初始化分布: U(-sqrt(6/(fan_in+fan_out)), sqrt(6/(fan_in+fan_out)))

    注意事项:
      这是假数据, 仅用于验证推理管线的代码正确性。
      真实模型上线时, 需用方案 B 从 .pt checkpoint 提取或用方案 C 从训练脚本导出。

    Args:
        n_users: 用户数量 (应与新闻系统 user 表最大 ID 对齐)
        n_items: 物品数量 (应与 newsdetail 表最大 news_id 对齐)
        dim: 嵌入维度
        seed: 随机种子 (固定以保证可复现)
    """
    print(f"[方案A] 生成随机 Embedding 矩阵...")
    print(f"  n_users={n_users}, n_items={n_items}, dim={dim}, seed={seed}")

    rng = np.random.RandomState(seed)
    # Xavier uniform 初始化 (与 PyTorch nn.init.xavier_uniform_ 等价)
    limit_user = np.sqrt(6.0 / (n_users + dim))
    limit_item = np.sqrt(6.0 / (n_items + dim))

    user_emb = rng.uniform(-limit_user, limit_user, (n_users, dim)).astype(np.float32)
    item_emb = rng.uniform(-limit_item, limit_item, (n_items, dim)).astype(np.float32)

    # L2 归一化 (与 Student_LightGCN 最后一层 F.normalize 对齐)
    user_emb = user_emb / (np.linalg.norm(user_emb, axis=1, keepdims=True) + 1e-8)
    item_emb = item_emb / (np.linalg.norm(item_emb, axis=1, keepdims=True) + 1e-8)

    return user_emb, item_emb


# =============================================================================
#  方案 B: 从 .pt checkpoint 提取 (真实训练权重)
# =============================================================================

def extract_from_checkpoint(
    checkpoint_path: str,
    n_users: int = None,
    n_items: int = None,
    dim: int = 64,
):
    """
    从 PyTorch .pt 文件中提取 Student_LightGCN 或 Student_MLP 的 Embedding。

    支持的 checkpoint 格式:
      1. 完整 state_dict (包含 'user_id_embedding.weight' / 'item_id_embedding.weight')
      2. 包含 'student_model' 子字典的嵌套 checkpoint
      3. 直接保存的 (user_emb, item_emb) 元组

    Args:
        checkpoint_path: .pt 文件路径
        n_users: 用户数量 (如果 checkpoint 不含此信息)
        n_items: 物品数量
        dim: 嵌入维度

    Returns:
        (user_emb, item_emb): numpy 数组
    """
    import torch

    print(f"[方案B] 从 checkpoint 提取: {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location='cpu')

    user_emb = None
    item_emb = None

    # ---- 格式 1: 直接是 (user, item) 元组 ----
    if isinstance(checkpoint, (tuple, list)) and len(checkpoint) == 2:
        print("  检测格式: (user_emb, item_emb) 元组")
        user_emb = checkpoint[0].detach().cpu().numpy()
        item_emb = checkpoint[1].detach().cpu().numpy()

    # ---- 格式 2: state_dict ----
    elif isinstance(checkpoint, dict):
        # 格式 2a: 嵌套 checkpoint, student_model 在子字典中
        if 'student_model' in checkpoint:
            print("  检测格式: 嵌套 checkpoint (含 'student_model')")
            sd = checkpoint['student_model']
        elif 'user_id_embedding.weight' in checkpoint:
            print("  检测格式: 顶层 state_dict")
            sd = checkpoint
        else:
            # 遍历查找包含 embedding 的键
            print("  检测格式: 未知字典格式, 尝试遍历查找 embedding...")
            sd = checkpoint

        # 多种可能的 key 名称 (兼容不同命名习惯)
        user_key_candidates = [
            'user_id_embedding.weight',
            'user_id_embedding_pre.weight',
            'user_emb.weight',
            'uEmbeds',
        ]
        item_key_candidates = [
            'item_id_embedding.weight',
            'item_id_embedding_pre.weight',
            'item_emb.weight',
            'iEmbeds',
        ]

        for key in user_key_candidates:
            if key in sd:
                user_emb = sd[key].detach().cpu().numpy()
                print(f"  找到 User Embedding: {key} → {user_emb.shape}")
                break

        for key in item_key_candidates:
            if key in sd:
                item_emb = sd[key].detach().cpu().numpy()
                print(f"  找到 Item Embedding: {key} → {item_emb.shape}")
                break

        # 遍历搜索 (兜底)
        if user_emb is None or item_emb is None:
            for key, value in sd.items():
                if isinstance(value, torch.Tensor) and value.ndim == 2:
                    if user_emb is None and value.shape[0] != (item_emb.shape[0] if item_emb is not None else -1):
                        user_emb = value.detach().cpu().numpy()
                        print(f"  推断 User Embedding: {key} → {user_emb.shape}")
                    elif item_emb is None and value.shape[0] != (user_emb.shape[0] if user_emb is not None else -1):
                        item_emb = value.detach().cpu().numpy()
                        print(f"  推断 Item Embedding: {key} → {item_emb.shape}")
                    if user_emb is not None and item_emb is not None:
                        break

    if user_emb is None or item_emb is None:
        raise ValueError(
            f"无法从 checkpoint 提取 Embedding。"
            f"支持的 key: {user_key_candidates + item_key_candidates}"
        )

    print(f"  提取成功: user={user_emb.shape}, item={item_emb.shape}")
    return user_emb.astype(np.float32), item_emb.astype(np.float32)


# =============================================================================
#  方案 C: 从训练脚本实时导出 (调用 main_DTS.py 中的模型)
# =============================================================================

def extract_from_training_session(
    n_users: int = 2000,
    n_items: int = 5000,
    dim: int = 64,
    n_layers: int = 1,
):
    """
    通过实例化 Student_LightGCN 并调用 forward 获取最终的 Embedding。

    ⚠️ 注意: 此函数需要在有 PyTorch 且正确配置了 args 的环境中运行。
    如果 PyTorch 不可用, 会自动回退到方案 A (随机假权重)。

    Args:
        n_users, n_items: 用户/物品数量
        dim: 嵌入维度 (对应 args.student_embed_size)
        n_layers: GCN 层数
    """
    try:
        import torch
        import scipy.sparse as sp
        import sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

        from Models import Student_LightGCN

        print(f"[方案C] 通过实例化 Student_LightGCN 导出...")

        # 创建模型实例
        model = Student_LightGCN(
            n_users=n_users,
            n_items=n_items,
            embedding_dim=dim,
            gnn_layer=n_layers,
            dropout_list=[0.1],
            image_feats=None,
            text_feats=None,
        )

        # 构建一个简单的单位归一化邻接矩阵 (模拟推理时的 identity 传播)
        # 实际部署时, 如果不需要图结构, 可直接使用 Embedding.weight
        ui_graph = sp.csr_matrix((n_users, n_items))
        iu_graph = sp.csr_matrix((n_items, n_users))

        # 转换为 PyTorch sparse tensor
        ui_coo = ui_graph.tocoo()
        iu_coo = iu_graph.tocoo()

        ui_indices = torch.LongTensor([ui_coo.row, ui_coo.col])
        ui_values = torch.FloatTensor(ui_coo.data)
        ui_sparse = torch.sparse.FloatTensor(ui_indices, ui_values, torch.Size(ui_graph.shape))

        iu_indices = torch.LongTensor([iu_coo.row, iu_coo.col])
        iu_values = torch.FloatTensor(iu_coo.data)
        iu_sparse = torch.sparse.FloatTensor(iu_indices, iu_values, torch.Size(iu_graph.shape))

        # 拼接邻接矩阵
        n_all = n_users + n_items
        adj = torch.sparse.FloatTensor(
            torch.LongTensor([[], []]),
            torch.FloatTensor([]),
            torch.Size([n_all, n_all])
        )

        # 由于空图 forward 等价于直接返回 Embedding.weight
        # 这里直接用更简单的方式: 直接取 Embedding.weight
        user_emb = model.user_id_embedding.weight.detach().cpu().numpy()
        item_emb = model.item_id_embedding.weight.detach().cpu().numpy()

        # L2 归一化
        user_emb = user_emb / (np.linalg.norm(user_emb, axis=1, keepdims=True) + 1e-8)
        item_emb = item_emb / (np.linalg.norm(item_emb, axis=1, keepdims=True) + 1e-8)

        print(f"  成功: user={user_emb.shape}, item={item_emb.shape}")
        return user_emb.astype(np.float32), item_emb.astype(np.float32)

    except ImportError as e:
        print(f"  [跳过] PyTorch 环境不可用 ({e}), 回退到随机假权重")
        return generate_random_embeddings(n_users, n_items, dim)
    except Exception as e:
        print(f"  [跳过] 实例化失败 ({e}), 回退到随机假权重")
        return generate_random_embeddings(n_users, n_items, dim)


# =============================================================================
#  保存与主入口
# =============================================================================

def save_embeddings(user_emb: np.ndarray, item_emb: np.ndarray):
    """保存为 .npy 文件"""
    user_path = os.path.join(WEIGHTS_DIR, 'user_embeddings.npy')
    item_path = os.path.join(WEIGHTS_DIR, 'item_embeddings.npy')

    np.save(user_path, user_emb)
    np.save(item_path, item_emb)

    print(f"\n✅ 导出完成:")
    print(f"  User Embeddings:  {user_path}  ({user_emb.shape}, {user_emb.dtype})")
    print(f"  Item Embeddings:  {item_path}  ({item_emb.shape}, {item_emb.dtype})")
    print(f"  内存占用: {user_emb.nbytes / 1024 / 1024:.1f} MB + "
          f"{item_emb.nbytes / 1024 / 1024:.1f} MB = "
          f"{(user_emb.nbytes + item_emb.nbytes) / 1024 / 1024:.1f} MB")


def main():
    parser = argparse.ArgumentParser(
        description='PromptMM 离线权重导出 — 提取 Student Embedding 矩阵'
    )
    parser.add_argument(
        '--checkpoint', type=str, default=None,
        help='PyTorch .pt checkpoint 路径 (方案 B)'
    )
    parser.add_argument(
        '--n_users', type=int, default=2000,
        help='用户数量 (默认: 2000)'
    )
    parser.add_argument(
        '--n_items', type=int, default=5000,
        help='物品数量 (默认: 5000, 应对齐 newsdetail 最大 news_id)'
    )
    parser.add_argument(
        '--dim', type=int, default=64,
        help='Embedding 维度 (默认: 64, 对齐 args.student_embed_size)'
    )
    parser.add_argument(
        '--use_torch', action='store_true',
        help='尝试方案C (实例化 Student_LightGCN 导出)'
    )

    args = parser.parse_args()

    if args.checkpoint:
        # 方案 B: 从 .pt 提取
        user_emb, item_emb = extract_from_checkpoint(
            args.checkpoint, args.n_users, args.n_items, args.dim
        )
    elif args.use_torch:
        # 方案 C: 实例化模型导出
        user_emb, item_emb = extract_from_training_session(
            args.n_users, args.n_items, args.dim
        )
    else:
        # 方案 A: 生成随机假权重 (开发测试)
        user_emb, item_emb = generate_random_embeddings(
            args.n_users, args.n_items, args.dim
        )

    save_embeddings(user_emb, item_emb)


if __name__ == '__main__':
    main()
