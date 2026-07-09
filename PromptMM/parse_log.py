import re
import sys

def parse_log(log_path):
    # 初始化时 Epoch 设为 -1 作为判断标志
    best_teacher = {"Epoch": -1, "Recall@20": -1}
    best_student = {"Epoch": -1, "Recall@20": -1}

    # 正则表达式保持不变，精准捕获所有核心指标
    pattern = re.compile(r'(Teacher|Student): Epoch (\d+) .*? recall=\[(.*?)\], precision=\[(.*?)\], hit=\[(.*?)\], ndcg=\[(.*?)\]')

    print(f"[*] 正在解析日志文件: {log_path}\n")

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            for line in f:
                match = pattern.search(line)
                if match:
                    role = match.group(1)
                    epoch = int(match.group(2))
                    recall = [float(x) for x in match.group(3).split(',')]
                    precision = [float(x) for x in match.group(4).split(',')]
                    hit = [float(x) for x in match.group(5).split(',')]
                    ndcg = [float(x) for x in match.group(6).split(',')]

                    metrics = {
                        "Epoch": epoch,
                        "Recall": recall, "NDCG": ndcg, 
                        "Hit": hit, "Precision": precision,
                        "Recall@20": recall[1]
                    }

                    # 更新 Teacher 最佳成绩
                    if role == "Teacher" and metrics["Recall@20"] > best_teacher["Recall@20"]:
                        best_teacher = metrics
                    # 更新 Student 最佳成绩
                    elif role == "Student" and metrics["Recall@20"] > best_student["Recall@20"]:
                        best_student = metrics
                        
    except FileNotFoundError:
        print(f"❌ 找不到文件: {log_path}")
        return

    # === [智能判定模式] ===
    has_teacher = best_teacher["Epoch"] != -1
    has_student = best_student["Epoch"] != -1

    if not has_teacher and not has_student:
        print("⚠️ 未在日志中找到任何有效的 Teacher 或 Student 训练记录。")
        return

    # === [动态生成表头] ===
    print("="*65)
    if has_teacher and has_student:
        print(f"{'指标 (Metric)':<15} | {'Teacher (Ep '+str(best_teacher['Epoch'])+')':<15} | {'Student (Ep '+str(best_student['Epoch'])+')':<15} | {'恢复率 (Recovery)'}")
    elif has_teacher:
        print(f"{'指标 (Metric)':<15} | {'Teacher (Ep '+str(best_teacher['Epoch'])+')':<15}")
    elif has_student:
        print(f"{'指标 (Metric)':<15} | {'Student (Ep '+str(best_student['Epoch'])+')':<15}")
    print("-" * 65)

    # === [动态打印表格数据] ===
    metrics_names = ["Recall", "NDCG", "Hit", "Precision"]
    k_values = ["@10", "@20", "@40", "@50"]

    for m_name in metrics_names:
        for i, k in enumerate(k_values):
            metric_label = f"{m_name+k:<15}"
            
            # 模式 1: 都有，对比并计算恢复率
            if has_teacher and has_student:
                t_val = best_teacher[m_name][i]
                s_val = best_student[m_name][i]
                recovery = (s_val / t_val) * 100 if t_val > 0 else 0
                print(f"{metric_label} | {t_val:<15.5f} | {s_val:<15.5f} | {recovery:.2f}%")
                
            # 模式 2: 只有 Teacher
            elif has_teacher:
                t_val = best_teacher[m_name][i]
                print(f"{metric_label} | {t_val:<15.5f}")
                
            # 模式 3: 只有 Student
            elif has_student:
                s_val = best_student[m_name][i]
                print(f"{metric_label} | {s_val:<15.5f}")
                
        print("-" * 65)
        
    print("🎉 解析完毕！")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("💡 用法: python parse_log.py <你的日志文件.log>")
    else:
        parse_log(sys.argv[1])