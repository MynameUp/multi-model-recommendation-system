#!/bin/bash
DATASET="sports"
T_LAYER=3
S_LAYER=1
DIM=64

# 基础黄金参数
DKD_ALPHA=0.1
DKD_BETA=0.5
TOP_K=1
KD_RATE=0.05
PATIENCE=15

# --- 实验 1: Prompt Dropout 敏感性 ---
for p_drop in 0.0 0.2 0.4 0.6 0.8
do
    echo "🧪 [Dropout Exp] Current p_drop: ${p_drop}"
    # 1.1 训练对应 Dropout 的 Teacher
    python codes/main_DTS.py --dataset $DATASET --if_train_teacher 1 \
        --layers $T_LAYER --embed_size $DIM \
        --prompt_dropout $p_drop --num_experts 4 --top_k $TOP_K \
        --early_stopping_patience 10 \
        --point exp_param_dropout_${p_drop}_T
    
    # 1.2 训练对应的 Student
    python codes/main_DTS.py --dataset $DATASET --if_train_teacher 0 \
        --student_model_type lightgcn --layers $T_LAYER --student_n_layers $S_LAYER \
        --embed_size $DIM --student_embed_size $DIM \
        --prompt_dropout $p_drop --num_experts 4 --top_k $TOP_K \
        --decouple_alpha $DKD_ALPHA --decouple_beta $DKD_BETA \
        --early_stopping_patience $PATIENCE \
        --point exp_param_dropout_${p_drop}_S
done

# --- 实验 2: MoE 专家数量敏感性 ---
for n_exp in 1 2 4 8 16
do
    echo "🧪 [Experts Exp] Current num_experts: ${n_exp}"
    # 2.1 训练对应专家数量的 Teacher
    python codes/main_DTS.py --dataset $DATASET --if_train_teacher 1 \
        --layers $T_LAYER --embed_size $DIM \
        --prompt_dropout 0.4 --num_experts $n_exp --top_k $TOP_K \
        --early_stopping_patience 10 \
        --point exp_param_experts_${n_exp}_T
    
    # 2.2 训练对应的 Student
    python codes/main_DTS.py --dataset $DATASET --if_train_teacher 0 \
        --student_model_type lightgcn --layers $T_LAYER --student_n_layers $S_LAYER \
        --embed_size $DIM --student_embed_size $DIM \
        --prompt_dropout 0.4 --num_experts $n_exp --top_k $TOP_K \
        --decouple_alpha $DKD_ALPHA --decouple_beta $DKD_BETA \
        --early_stopping_patience $PATIENCE \
        --point exp_param_experts_${n_exp}_S
done

# --- 实验 3: 多模态注入比例敏感性 ---
for f_rate in 0.001 0.005 0.01 0.05 0.1
do
    echo "🧪 [FeatRate Exp] Current f_rate: ${f_rate}"
    # 3.1 训练对应注入比例的 Teacher
    python codes/main_DTS.py --dataset $DATASET --if_train_teacher 1 \
        --layers $T_LAYER --embed_size $DIM \
        --prompt_dropout 0.4 --num_experts 4 --top_k $TOP_K \
        --feat_soft_token_rate $f_rate \
        --early_stopping_patience 10 \
        --point exp_param_featrate_${f_rate}_T
    
    # 3.2 训练对应的 Student
    python codes/main_DTS.py --dataset $DATASET --if_train_teacher 0 \
        --student_model_type lightgcn --layers $T_LAYER --student_n_layers $S_LAYER \
        --embed_size $DIM --student_embed_size $DIM \
        --prompt_dropout 0.4 --num_experts 4 --top_k $TOP_K \
        --feat_soft_token_rate $f_rate \
        --decouple_alpha $DKD_ALPHA --decouple_beta $DKD_BETA \
        --early_stopping_patience $PATIENCE \
        --point exp_param_featrate_${f_rate}_S
done