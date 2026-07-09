#!/bin/bash
DATASET="baby" # 或者 sports，保持一致
T_LAYER=3      # 之前实验证明 T=3 效果最好
S_LAYER=1      # 【建议】之前实验 S=1 效果最好，如果你想测 S=2 也可以改回 2

# 统一的成功参数配置 (必须覆盖 parse_args 的致命默认值)
TOP_K=1
PROMPT_DROP=0.4
FEAT_SOFT_RATE=0.01
KD_LIST_RATE=0.05
KD_FEAT_RATE=0.05
DKD_ALPHA=0.1
DKD_BETA=0.5
MOE_WEIGHT=0.05
PATIENCE=20    # 增加早停耐心，防止刚起步就停

for t_dim in 16 32 64 128
do
    echo "========================================"
    echo "🚀 开始训练 Teacher (维度: ${t_dim})"
    echo "========================================"
    # 1. 训练老师 (必须带上正确的 MoE 和 Prompt 参数)
    python codes/main_DTS.py --dataset $DATASET --if_train_teacher 1 \
        --layers $T_LAYER \
        --embed_size $t_dim \
        --epoch 500 --early_stopping_patience $PATIENCE \
        --top_k $TOP_K --prompt_dropout $PROMPT_DROP \
        --feat_soft_token_rate $FEAT_SOFT_RATE \
        --moe_loss_weight $MOE_WEIGHT \
        --point exp_dim_T${t_dim}_pretrain

    for s_dim in 16 32 64 128
    do
        echo "----------------------------------------"
        echo "🎓 开始训练 Student (T维度: ${t_dim}, S维度: ${s_dim})"
        echo "----------------------------------------"
        # 2. 训练学生 (必须指定 lightgcn，并带上全套 KD 参数)
        python codes/main_DTS.py --dataset $DATASET --if_train_teacher 0 \
            --student_model_type lightgcn \
            --layers $T_LAYER --student_n_layers $S_LAYER \
            --embed_size $t_dim --student_embed_size $s_dim \
            --epoch 1000 --early_stopping_patience $PATIENCE \
            --top_k $TOP_K --prompt_dropout $PROMPT_DROP \
            --feat_soft_token_rate $FEAT_SOFT_RATE \
            --kd_loss_list_rate $KD_LIST_RATE \
            --kd_loss_feat_rate $KD_FEAT_RATE \
            --decouple_alpha $DKD_ALPHA \
            --decouple_beta $DKD_BETA \
            --moe_loss_weight $MOE_WEIGHT \
            --point exp_dim_T${t_dim}_S${s_dim}
    done
done