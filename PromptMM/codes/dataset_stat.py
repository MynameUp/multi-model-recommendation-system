import os
import json
import numpy as np

# ========== 路径修正区 ==========
dataset = 'clothing'
# 基础路径
base_dir = f'/root/autodl-tmp/PromptMM/data/{dataset}/'
# 核心文件夹路径
core_dir = os.path.join(base_dir, '5-core')

# 映射文件路径 (根据你的反馈已修正)
user_list_path = os.path.join(core_dir, 'user_list.txt')
item_list_path = os.path.join(core_dir, 'item_list.txt')

# 交互文件列表
split_files = ['train.json', 'test.json', 'val.json']
# ===============================

def count_txt_lines(path):
    if not os.path.exists(path):
        print(f"❌ 错误: 找不到文件 {path}")
        return 0
    with open(path, 'r', encoding='utf-8') as f:
        # 统计非空行
        return sum(1 for line in f if line.strip())

def count_json_interactions(path):
    if not os.path.exists(path):
        return 0
    with open(path, 'r', encoding='utf-8') as f:
        try:
            # 尝试整体加载 (适配 [{}, {}, ...] 格式)
            data = json.load(f)
            if isinstance(data, list):
                return len(data)
            elif isinstance(data, dict):
                # 适配 {"user1": [i1, i2], ...} 格式
                return sum(len(v) if isinstance(v, list) else 1 for v in data.values())
        except json.JSONDecodeError:
            # 适配 JSON Lines (每行一个 {}) 格式
            f.seek(0)
            return sum(1 for line in f if line.strip() and not line.strip() in ['[', ']', ','])
    return 0

print(f"🔍 正在对 [{dataset.upper()}] 进行最终数据审计...")

# 1. 统计节点总数
num_users = count_txt_lines(user_list_path)
num_items = count_txt_lines(item_list_path)

# 2. 统计交互总数
total_inter = 0
for f_name in split_files:
    p = os.path.join(core_dir, f_name)
    c = count_json_interactions(p)
    print(f"   - {f_name} 交互数: {c:,}")
    total_inter += c

# 3. 统计特征维度 (特征文件通常在 data/baby/ 下)
v_dim, t_dim = "N/A", "N/A"
v_p = os.path.join(base_dir, 'image_feat.npy')
t_p = os.path.join(base_dir, 'text_feat.npy')

if os.path.exists(v_p):
    v_dim = np.load(v_p, mmap_mode='r').shape[1]
if os.path.exists(t_p):
    t_dim = np.load(t_p, mmap_mode='r').shape[1]

# 4. 计算指标
sparsity = (1.0 - (total_inter / (num_users * num_items))) * 100 if num_users * num_items > 0 else 0

# ==========================================
# 打印最终论文 Table 格式
# ==========================================
print("\n" + "—"*45)
print(f"📊 论文 Dataset Statistics 表格数据")
print("—"*45)
print(f"Dataset      | {dataset.capitalize()}")
print(f"User         | {num_users:,}")
print(f"Item         | {num_items:,}")
print(f"Interaction  | {total_inter:,}")
print(f"Sparsity     | {sparsity:.4f}%")
print(f"Feat. Dim.   | V:{v_dim}, T:{t_dim}")
print("—"*45 + "\n")