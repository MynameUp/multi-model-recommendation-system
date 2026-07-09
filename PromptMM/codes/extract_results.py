import os
import pickle
import numpy as np

# 你要提取的数据集名称
dataset = 'sports'
base_dir = f'./history/{dataset}/'

print(f"🔍 正在扫描 {base_dir} 目录下的实验结果...\n")

# ==========================================
# 提取【实验 A：GNN 层数敏感性】数据
# ==========================================
print("📊 【实验 A: GNN 层数】 Recall@20 结果矩阵")
print("(行: Teacher 层数, 列: Student 层数)")
print("-" * 55)
print("T \\ S \t| Layer 1 | Layer 2 | Layer 3 | Layer 4 |")
print("-" * 55)

layer_matrix = np.zeros((4, 4))
for t_idx, t_layer in enumerate([1, 2, 3, 4]):
    row_str = f"T={t_layer} \t| "
    for s_idx, s_layer in enumerate([1, 2, 3, 4]):
        # 根据我们 shell 脚本里的 point 命名规则拼凑文件名
        filename = f"student_exp_layer_T{t_layer}_S{s_layer}.pkl"
        filepath = os.path.join(base_dir, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
                # 提取整个训练过程中的最优 Recall@20
                best_r20 = max(data['recall20_List'])
                layer_matrix[t_idx, s_idx] = best_r20
                row_str += f"{best_r20:.5f} | "
        else:
            row_str += "  Waiting  | "
    print(row_str)
print("-" * 55 + "\n")


# ==========================================
# 提取【实验 B：隐层维度敏感性】数据
# ==========================================
print("📊 【实验 B: 隐层维度】 Recall@20 结果矩阵")
print("(行: Teacher 维度, 列: Student 维度)")
print("-" * 63)
print("T \\ S \t| Dim 16  | Dim 32  | Dim 64  | Dim 128 |")
print("-" * 63)

dim_matrix = np.zeros((4, 4))
for t_idx, t_dim in enumerate([16, 32, 64, 128]):
    row_str = f"T={t_dim} \t| "
    for s_idx, s_dim in enumerate([16, 32, 64, 128]):
        filename = f"student_exp_dim_T{t_dim}_S{s_dim}.pkl"
        filepath = os.path.join(base_dir, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
                best_r20 = max(data['recall20_List'])
                dim_matrix[t_idx, s_idx] = best_r20
                row_str += f"{best_r20:.5f} | "
        else:
            row_str += "  Waiting  | "
    print(row_str)
print("-" * 63 + "\n")

# ==========================================
# 提取【实验 C：参数敏感性分析】数据 (Recall & NDCG)
# ==========================================
print("📊 【实验 C1: Prompt Dropout 敏感性】 Recall & NDCG")
print("-" * 65)
dropouts = [0.0, 0.2, 0.4, 0.6, 0.8]
print("Dropout \t| " + " | ".join([f"{d:<7}" for d in dropouts]) + " |")
row_r20  = "Recall  \t| "
row_ndcg = "NDCG    \t| "

for p_drop in dropouts:
    filename = f"student_exp_param_dropout_{p_drop}_S.pkl"
    filepath = os.path.join(base_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            # 找到 Recall 最大的 Epoch 索引
            best_epoch_idx = np.argmax(data['recall20_List'])
            # 提取该 Epoch 对应的 Recall 和 NDCG
            best_r20 = data['recall20_List'][best_epoch_idx]
            best_n20 = data['ndcg20_List'][best_epoch_idx]  # 假设字典键名为 ndcg20_List
            
            row_r20 += f"{best_r20:.5f} | "
            row_ndcg += f"{best_n20:.5f} | "
    else:
        row_r20 += " Waiting | "
        row_ndcg += " Waiting | "
        
print(row_r20)
print(row_ndcg)
print("-" * 65 + "\n")


print("📊 【实验 C2: MoE 专家数量敏感性】 Recall & NDCG")
print("-" * 65)
experts = [1, 2, 4, 8, 16]
print("Experts \t| " + " | ".join([f"{e:<7}" for e in experts]) + " |")
row_r20  = "Recall  \t| "
row_ndcg = "NDCG    \t| "

for n_exp in experts:
    filename = f"student_exp_param_experts_{n_exp}_S.pkl"
    filepath = os.path.join(base_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            best_epoch_idx = np.argmax(data['recall20_List'])
            best_r20 = data['recall20_List'][best_epoch_idx]
            best_n20 = data['ndcg20_List'][best_epoch_idx]
            
            row_r20 += f"{best_r20:.5f} | "
            row_ndcg += f"{best_n20:.5f} | "
    else:
        row_r20 += " Waiting | "
        row_ndcg += " Waiting | "
        
print(row_r20)
print(row_ndcg)
print("-" * 65 + "\n")


print("📊 【实验 C3: 多模态注入比例敏感性】 Recall & NDCG")
print("-" * 65)
feat_rates = [0.001, 0.005, 0.01, 0.05, 0.1]
print("FeatRate\t| " + " | ".join([f"{f:<7}" for f in feat_rates]) + " |")
row_r20  = "Recall  \t| "
row_ndcg = "NDCG    \t| "

for f_rate in feat_rates:
    filename = f"student_exp_param_featrate_{f_rate}_S.pkl"
    filepath = os.path.join(base_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            best_epoch_idx = np.argmax(data['recall20_List'])
            best_r20 = data['recall20_List'][best_epoch_idx]
            best_n20 = data['ndcg20_List'][best_epoch_idx]
            
            row_r20 += f"{best_r20:.5f} | "
            row_ndcg += f"{best_n20:.5f} | "
    else:
        row_r20 += " Waiting | "
        row_ndcg += " Waiting | "
        
print(row_r20)
print(row_ndcg)
print("-" * 65 + "\n")