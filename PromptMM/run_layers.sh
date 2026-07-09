#!/bin/bash
DATASET="baby" # 或者 "sports" 保持一致
DIM=64

# 统一的成功参数配置 (提取自消融实验)
TOP_K=1
PROMPT_DROP=0.4
FEAT_SOFT_RATE=0.01
KD_LIST_RATE=0.05
KD_FEAT_RATE=0.05
DKD_ALPHA=0.1
DKD_BETA=0.5
MOE_WEIGHT=0.05

for t_layer in 1 2 3 4
do
    echo "========================================"
    echo "🚀 开始训练 Teacher (层数: ${t_layer})"
    echo "========================================"
    
    # 1. 重新训练老师 (确保老师也是用正确的参数训练的)
    python codes/main_DTS.py --dataset $DATASET --if_train_teacher 1 \
        --layers $t_layer --embed_size $DIM \
        --epoch 500 --early_stopping_patience 15 \
        --top_k $TOP_K --prompt_dropout $PROMPT_DROP \
        --feat_soft_token_rate $FEAT_SOFT_RATE \
        --moe_loss_weight $MOE_WEIGHT \
        --point exp_layer_T${t_layer}_pretrain

    for s_layer in 1 2 3 4
    do
        echo "----------------------------------------"
        echo "🎓 Testing LightGCN Student: T_Layer=${t_layer}, S_Layer=${s_layer}"
        echo "----------------------------------------"
        
        # 2. 训练学生 (加入所有正确的 KD 约束参数)
        python codes/main_DTS.py --dataset $DATASET --if_train_teacher 0 \
            --student_model_type lightgcn \
            --layers $t_layer \
            --student_n_layers $s_layer \
            --embed_size $DIM --student_embed_size $DIM \
            --epoch 1000 --early_stopping_patience 15 \
            --top_k $TOP_K --prompt_dropout $PROMPT_DROP \
            --feat_soft_token_rate $FEAT_SOFT_RATE \
            --kd_loss_list_rate $KD_LIST_RATE \
            --kd_loss_feat_rate $KD_FEAT_RATE \
            --decouple_alpha $DKD_ALPHA \
            --decouple_beta $DKD_BETA \
            --moe_loss_weight $MOE_WEIGHT \
            --point exp_layer_T${t_layer}_S${s_layer}
    done
done