import pickle
import matplotlib.pyplot as plt

# 替换成你实际生成的 pkl 文件名
pkl_path = './history/sports/student_run_sports_moe_logits_DTS_optimal.pkl'

with open(pkl_path, 'rb') as f:
    data = pickle.load(f)

tau_list = data['dynamic_tau_List']
epochs = list(range(len(tau_list)))

# 设置绘图风格
plt.figure(figsize=(8, 5))
plt.plot(epochs, tau_list, color='#FF6B6B', linewidth=2.5, label='Dynamic Temperature ($\\tau$)')

plt.title('Dynamic Temperature Scheduler (DTS) Annealing Curve', fontsize=14)
plt.xlabel('Epochs', fontsize=12)
plt.ylabel('Temperature $\\tau$', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend(fontsize=12)

# 保存为高清图片
plt.savefig('tau_curve.png', dpi=300, bbox_inches='tight')
print("✅ 动态温度曲线已成功保存为 tau_curve.png")