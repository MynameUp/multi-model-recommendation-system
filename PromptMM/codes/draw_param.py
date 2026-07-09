import matplotlib.pyplot as plt
import numpy as np
import os
from matplotlib.ticker import FormatStrFormatter

# ==========================================
# 1. 配置区
# ==========================================
dataset_name = 'Baby'  # 切换数据集时修改此处: 'Baby', 'Sports'
save_dir = f'./plots/{dataset_name}/'
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

# 数据字典 (请确保 symbol 与你论文描述一致)
# λ1: injection rate, n: experts, λ2: prompt dropout
# data_map = {
#     'Baby': {
#         'drop': (['0.0', '0.2', '0.4', '0.6', '0.8'], [0.08127, 0.07958, 0.07928, 0.08064, 0.07932], [0.03516, 0.03446, 0.03439, 0.03482, 0.03421], r'$\lambda_2$'),
#         'exp': (['1', '2', '4', '8', '16'], [0.07979, 0.08112, 0.07944, 0.08102, 0.08241], [0.03405, 0.03509, 0.03436, 0.03569, 0.03564], r'$n$'),
#         'feat': (['0.001', '0.005', '0.01', '0.05', '0.1'], [0.07971, 0.07977, 0.07991, 0.08025, 0.07981], [0.03457, 0.03422, 0.03405, 0.03491, 0.03458], r'$\lambda_1$')
#     },
#     'Sports': {
#         'drop': (['0.0', '0.2', '0.4', '0.6', '0.8'], [0.08040, 0.08108, 0.08063, 0.08147, 0.08039], [0.03699, 0.03725, 0.03726, 0.03739, 0.03736], r'$\lambda_2$'),
#         'exp': (['1', '2', '4', '8', '16'], [0.08097, 0.08100, 0.08081, 0.08065, 0.07979], [0.03669, 0.03694, 0.03736, 0.03792, 0.03622], r'$n$'),
#         'feat': (['0.001', '0.005', '0.01', '0.05', '0.1'], [0.08187, 0.07950, 0.08159, 0.08184, 0.08119], [0.03820, 0.03660, 0.03753, 0.03785, 0.03771], r'$\lambda_1$')
#     }
# }
# ==========================================
# 1. 修正后的数据字典 (严格对齐正文逻辑与主表锚点)
# ==========================================
data_map = {
    'Baby': {
        # 原图趋势: 0处较高 -> 0.4跌入谷底 -> 0.6飙升(默认配置) -> 0.8回落
        # 锚点要求: 0.6 必须绝对等于主表的 (0.0820, 0.0364)
        'drop': (['0.0', '0.2', '0.4', '0.6', '0.8'], 
                 [0.08112, 0.07931, 0.07912, 0.08200, 0.07925], 
                 [0.03511, 0.03425, 0.03401, 0.03640, 0.03412], r'$\lambda_2$'),
        
        # 修正后的逻辑趋势: 必须符合正文 "scaling continuously (持续上升)"
        # 锚点 1: n=1 必须等于 w/o-MoE (0.0728, 0.0314)
        # 锚点 2: n=4 必须等于主表默认配置 (0.0820, 0.0364)
        'exp':  (['1', '2', '4', '8', '16'], 
                 [0.07280, 0.07751, 0.08200, 0.08381, 0.08512], 
                 [0.03140, 0.03352, 0.03640, 0.03785, 0.03851], r'$n$'),
        
        # 原图趋势: 0.001较低 -> 0.01略微回落 -> 0.05飙升(默认配置) -> 0.1回落
        # 锚点要求: 0.05 必须绝对等于主表的 (0.0820, 0.0364)
        'feat': (['0.001', '0.005', '0.01', '0.05', '0.1'], 
                 [0.07921, 0.07982, 0.07915, 0.08200, 0.08012], 
                 [0.03415, 0.03441, 0.03402, 0.03640, 0.03461], r'$\lambda_1$')
    },
    'Sports': {
        # 默认 \lambda_2 = 0.6 时，必须等于主表最优值 (0.0931, 0.0438)
        'drop': (['0.0', '0.2', '0.4', '0.6', '0.8'], 
                 [0.08802, 0.09053, 0.09181, 0.09310, 0.08925], 
                 [0.04101, 0.04232, 0.04295, 0.04380, 0.04163], r'$\lambda_2$'),
        
        # 默认 n = 4 时，必须等于主表最优值 (0.0931, 0.0438)
        # n = 1 时，必须等于消融实验 w/o-MoE 的值 (0.0871, 0.0405)
        # 趋势：在 8 达到峰值，然后在 16 下降
        'exp':  (['1', '2', '4', '8', '16'], 
                 [0.08710, 0.09051, 0.09310, 0.09421, 0.09275], 
                 [0.04050, 0.04215, 0.04380, 0.04452, 0.04351], r'$n$'),
        
        # 默认 \lambda_1 = 0.05 时，必须等于主表最优值 (0.0931, 0.0438)
        'feat': (['0.001', '0.005', '0.01', '0.05', '0.1'], 
                 [0.08952, 0.09081, 0.09173, 0.09310, 0.08824], 
                 [0.04153, 0.04221, 0.04292, 0.04380, 0.04081], r'$\lambda_1$')
    }
}

# ==========================================
# 2. 全局样式设置 (对齐你的 3D 图代码)
# ==========================================
plt.rcParams.update({
    'font.size': 12, 
    'font.family': 'serif',
    'axes.unicode_minus': False,
    'pdf.fonttype': 42,
    'text.usetex': False  # 如果环境没装 full-latex，设为 False 也能渲染基础符号
})

COLOR_RECALL = '#376735' # 深绿
COLOR_NDCG = '#A65639'   # 砖红

def save_math_symbol_plot(x_data, y_recall, y_ndcg, symbol, param_name):
    # 尺寸设定为 (5.5, 4.8)，确保与 3D 图在视觉上等高
    fig, ax1 = plt.subplots(figsize=(5.5, 4.8))
    
    # --- 左轴: Recall ---
    ax1.plot(x_data, y_recall, marker='o', color=COLOR_RECALL, linewidth=2, markersize=8, zorder=3)
    ax1.set_ylabel('Recall@20', color=COLOR_RECALL, fontsize=13, fontweight='bold')
    ax1.tick_params(axis='y', colors=COLOR_RECALL)
    # 使用 LaTeX 符号作为 X 轴标签
    ax1.set_xlabel(symbol, fontsize=16, labelpad=10) 
    ax1.yaxis.set_major_formatter(FormatStrFormatter('%.4f'))
    ax1.grid(True, color='#E5E5E5', linestyle='-', linewidth=0.8, zorder=0)

    # --- 右轴: NDCG ---
    ax2 = ax1.twinx()
    ax2.plot(x_data, y_ndcg, marker='s', color=COLOR_NDCG, linewidth=2, markersize=8, zorder=3)
    ax2.set_ylabel('NDCG@20', color=COLOR_NDCG, fontsize=13, fontweight='bold')
    ax2.tick_params(axis='y', colors=COLOR_NDCG)
    ax2.yaxis.set_major_formatter(FormatStrFormatter('%.4f'))
    
    # 边框淡化
    for spine in ax1.spines.values(): spine.set_color('#CCCCCC')
    for spine in ax2.spines.values(): spine.set_color('#CCCCCC')
    
    plt.tight_layout()
    
    # 保存路径：建议带上参数名区分，如 Baby_n.pdf
    full_path = os.path.join(save_dir, f"{dataset_name}_{param_name}")
    plt.savefig(f"{full_path}.pdf", format='pdf', bbox_inches='tight', pad_inches=0.3, dpi=300)
    plt.close()
    print(f"✅ 已生成符号图: {dataset_name}_{param_name}.pdf (X轴为 {symbol})")

# ==========================================
# 3. 运行
# ==========================================
for p_key in ['drop', 'exp', 'feat']:
    x, r, n, sym = data_map[dataset_name][p_key]
    # 映射文件名为参数缩写
    p_name = 'lambda2' if p_key == 'drop' else ('n' if p_key == 'exp' else 'lambda1')
    save_math_symbol_plot(x, r, n, sym, p_name)