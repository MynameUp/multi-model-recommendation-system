import numpy as np
import matplotlib.pyplot as plt

# 1. 准备维度实验数据
Z_recall = np.array([
    [0.07316, 0.07333, 0.07309, 0.07327],
    [0.07928, 0.07929, 0.07863, 0.07835],
    [0.08000, 0.08055, 0.07955, 0.07967],
    [0.08122, 0.08177, 0.08099, 0.08174]
])

# 为了让 3D 表面图的网格均匀，我们在底层用 1,2,3,4 画图，然后在刻度上贴上真实的维度值
indices = np.array([1, 2, 3, 4])
labels = ['16', '32', '64', '128']

# X 绑定 Teacher，Y 绑定 Student
X, Y = np.meshgrid(indices, indices)
Z = Z_recall.T 

# 2. 设置学术风格
plt.rcParams.update({'font.size': 12, 'font.family': 'serif'})
fig = plt.figure(figsize=(8, 6)) 
ax = fig.add_subplot(111, projection='3d')

# 3. 绘制 3D 曲面 (保持和 Layer 图一样的 cividis 配色)
surf = ax.plot_surface(X, Y, Z, cmap='cividis', 
                       edgecolor='gray', linewidth=0.3, alpha=0.9)

# 4. 设置轴标签
ax.set_xlabel('Teacher Dimension', labelpad=8)
ax.set_ylabel('Student Dimension', labelpad=8)
ax.set_zlabel('Recall@20 on Baby', labelpad=5)

# 5. 映射真实的刻度文字
ax.set_xticks(indices)
ax.set_xticklabels(labels)
ax.set_yticks(indices)
ax.set_yticklabels(labels)

# 动态调整 Z 轴刻度，涵盖 0.073 到 0.082 的区间
ax.set_zticks([0.072, 0.075, 0.078, 0.081]) 

# # 6. 图注标题 (b)
# plt.title('(b) Dimension size', y=-0.05, fontsize=14)

# 7. 保持相同的完美视角
ax.view_init(elev=25, azim=-45)
ax.dist = 11 

# 8. 无损保存
plt.savefig('dim_sensitivity_baby_3d.pdf', format='pdf', bbox_inches='tight', pad_inches=0.15, dpi=300)
plt.savefig('dim_sensitivity_baby_3d.png', format='png', bbox_inches='tight', pad_inches=0.15, dpi=300)

print("✅ (b) 维度敏感性 3D 图表已生成！")