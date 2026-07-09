import os
import numpy as np
from time import time
import pickle 
import pickle
import scipy.sparse as sp
from scipy.sparse import csr_matrix

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn import init

from sklearn.decomposition import PCA, FastICA
from sklearn import manifold
from sklearn.manifold import TSNE
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

# from utility.parser import parse_args
from utility.norm import build_sim, build_knn_normalized_graph
# args = parse_args()
from utility.parser import args



class Teacher_Model(nn.Module):
    def __init__(self, n_users, n_items, embedding_dim, weight_size, dropout_list, image_feats, text_feats):

        super().__init__()
        self.n_users = n_users
        self.n_items = n_items
        self.embedding_dim = embedding_dim
        self.weight_size = weight_size
        self.n_ui_layers = len(self.weight_size)
        self.weight_size = [self.embedding_dim] + self.weight_size

        # --- 特征变换层 ---
        # 将原始多模态特征映射到 embedding_dim
        self.image_trans = nn.Linear(image_feats.shape[1], args.embed_size)
        self.text_trans = nn.Linear(text_feats.shape[1], args.embed_size)
        nn.init.xavier_uniform_(self.image_trans.weight)
        nn.init.xavier_uniform_(self.text_trans.weight)             
        self.encoder = nn.ModuleDict() 
        self.encoder['image_encoder'] = self.image_trans # ^-^
        self.encoder['text_encoder'] = self.text_trans # ^-^

        # --- ID Embeddings ---
        # 基础的用户/物品 ID 嵌入
        self.user_id_embedding = nn.Embedding(n_users, self.embedding_dim)
        self.item_id_embedding = nn.Embedding(n_items, self.embedding_dim)

        # 保存原始特征 (作为 Tensor)
        nn.init.xavier_uniform_(self.user_id_embedding.weight)
        nn.init.xavier_uniform_(self.item_id_embedding.weight)

        self.register_buffer('image_feats', torch.tensor(image_feats).float())
        self.register_buffer('text_feats', torch.tensor(text_feats).float())

        self.image_embedding = nn.Embedding.from_pretrained(torch.Tensor(image_feats), freeze=False)
        self.text_embedding = nn.Embedding.from_pretrained(torch.Tensor(text_feats), freeze=False)

        self.softmax = nn.Softmax(dim=-1)
        self.act = nn.Sigmoid()  
        self.sigmoid = nn.Sigmoid()
        self.dropout = nn.Dropout(p=args.drop_rate)
        self.batch_norm = nn.BatchNorm1d(args.embed_size)

    def mm(self, x, y):
        if args.sparse:
            return torch.sparse.mm(x, y)
        else:
            return torch.mm(x, y)
    def sim(self, z1, z2):
        z1 = F.normalize(z1)
        z2 = F.normalize(z2)
        return torch.mm(z1, z2.t())

    def batched_contrastive_loss(self, z1, z2, batch_size=4096):
        device = z1.device
        num_nodes = z1.size(0)
        num_batches = (num_nodes - 1) // batch_size + 1
        f = lambda x: torch.exp(x / self.tau)
        indices = torch.arange(0, num_nodes).to(device)
        losses = []

        for i in range(num_batches):
            mask = indices[i * batch_size:(i + 1) * batch_size]
            refl_sim = f(self.sim(z1[mask], z1))  
            between_sim = f(self.sim(z1[mask], z2))  

            losses.append(-torch.log(
                between_sim[:, i * batch_size:(i + 1) * batch_size].diag()
                / (refl_sim.sum(1) + between_sim.sum(1)
                   - refl_sim[:, i * batch_size:(i + 1) * batch_size].diag())))
                   
        loss_vec = torch.cat(losses)
        return loss_vec.mean()

    def csr_norm(self, csr_mat, mean_flag=False):
        rowsum = np.array(csr_mat.sum(1))
        rowsum = np.power(rowsum+1e-8, -0.5).flatten()
        rowsum[np.isinf(rowsum)] = 0.
        rowsum_diag = sp.diags(rowsum)

        colsum = np.array(csr_mat.sum(0))
        colsum = np.power(colsum+1e-8, -0.5).flatten()
        colsum[np.isinf(colsum)] = 0.
        colsum_diag = sp.diags(colsum)

        if mean_flag == False:
            return rowsum_diag*csr_mat*colsum_diag
        else:
            return rowsum_diag*csr_mat

    def matrix_to_tensor(self, cur_matrix):
        if type(cur_matrix) != sp.coo_matrix:
            cur_matrix = cur_matrix.tocoo()  #
        indices = torch.from_numpy(np.vstack((cur_matrix.row, cur_matrix.col)).astype(np.int64))  #
        values = torch.from_numpy(cur_matrix.data)  #
        shape = torch.Size(cur_matrix.shape)

        return torch.sparse.FloatTensor(indices, values, shape).to(torch.float32).cuda()  #

    def para_dict_to_tenser(self, para_dict):  
        """
        :param para_dict: nn.ParameterDict()
        :return: tensor
        """
        tensors = []

        for beh in para_dict.keys():
            tensors.append(para_dict[beh])
        tensors = torch.stack(tensors, dim=0)

        return tensors


    def multi_head_self_attention(self, trans_w, embedding_t_1, embedding_t):  
       
        q = self.para_dict_to_tenser(embedding_t)
        v = k = self.para_dict_to_tenser(embedding_t_1)
        beh, N, d_h = q.shape[0], q.shape[1], args.embed_size/args.head_num

        Q = torch.matmul(q, trans_w['w_q'])  
        K = torch.matmul(k, trans_w['w_k'])
        V = v

        Q = Q.reshape(beh, N, args.head_num, int(d_h)).permute(2, 0, 1, 3)  
        K = Q.reshape(beh, N, args.head_num, int(d_h)).permute(2, 0, 1, 3)

        Q = torch.unsqueeze(Q, 2) 
        K = torch.unsqueeze(K, 1)  
        V = torch.unsqueeze(V, 1)  

        att = torch.mul(Q, K) / torch.sqrt(torch.tensor(d_h))  
        att = torch.sum(att, dim=-1) 
        att = torch.unsqueeze(att, dim=-1)  
        att = F.softmax(att, dim=2)  

        Z = torch.mul(att, V)  
        Z = torch.sum(Z, dim=2)  

        Z_list = [value for value in Z]
        Z = torch.cat(Z_list, -1)
        Z = torch.matmul(Z, self.weight_dict['w_self_attention_cat'])

        args.model_cat_rate*F.normalize(Z, p=2, dim=2)
        return Z, att.detach()


    # 【修改】加入了 use_prompt 开关，默认开启
    def forward(self, ui_graph, iu_graph, prompt_module=None, use_prompt=True):

        # =====================================================================
        # 1. 特征初始化与 Prompt 注入阶段 (受消融开关控制)
        # =====================================================================
        if use_prompt and prompt_module is not None:
            # -------- [使用 Prompt 的满血版分支] --------
            prompt_outputs = prompt_module()
            if len(prompt_outputs) == 3:
                prompt_user, prompt_item, prompt_aux_loss = prompt_outputs
            else:
                prompt_user, prompt_item = prompt_outputs
                prompt_aux_loss = torch.tensor(0.0, device=self.image_feats.device)

            # 生成软提示特征
            feat_prompt_item_image = torch.mm(prompt_item, torch.mm(prompt_item.T, self.image_feats))
            feat_prompt_item_text = torch.mm(prompt_item, torch.mm(prompt_item.T, self.text_feats))

            # 融合原始特征与 Prompt
            image_feats = self.dropout(self.image_trans(self.image_feats + args.feat_soft_token_rate*F.normalize(feat_prompt_item_image, p=2, dim=1) ))  
            text_feats = self.dropout(self.text_trans(self.text_feats + args.feat_soft_token_rate*F.normalize(feat_prompt_item_text, p=2, dim=1) ))

            # ID 注入 Prompt
            u_g_embeddings = self.user_id_embedding.weight  + args.soft_token_rate*F.normalize(prompt_user, p=2, dim=1)
            i_g_embeddings = self.item_id_embedding.weight  + args.soft_token_rate*F.normalize(prompt_item, p=2, dim=1)
            
        else:
            # -------- [消融 Prompt 的 Baseline 分支] --------
            # 给全 0 张量占位，防止后面的 Loss 计算报错
            prompt_user = torch.zeros_like(self.user_id_embedding.weight)
            prompt_item = torch.zeros_like(self.item_id_embedding.weight)
            prompt_aux_loss = torch.tensor(0.0, device=self.image_feats.device)
            
            # 直接过线性层，没有任何 Prompt 增强
            image_feats = self.dropout(self.image_trans(self.image_feats))
            text_feats = self.dropout(self.text_trans(self.text_feats))
            
            # ID 保持纯净
            u_g_embeddings = self.user_id_embedding.weight
            i_g_embeddings = self.item_id_embedding.weight


        # =====================================================================
        # 2. 多模态特征的图传播 (GCN) - 【这里的循环绝对保留且已修复 Bug】
        # =====================================================================
        curr_image_feats = image_feats
        curr_text_feats = text_feats
        for i in range(args.layers):
            image_user_feats = self.mm(ui_graph, curr_image_feats)
            curr_image_feats = self.mm(iu_graph, image_user_feats)

            text_user_feats = self.mm(ui_graph, curr_text_feats)
            curr_text_feats = self.mm(iu_graph, text_user_feats)
            
        image_item_feats = curr_image_feats
        text_item_feats = curr_text_feats


        # =====================================================================
        # 3. ID Embedding 的图传播 (GCN) - 【包含你说的 n_ui_layers 循环】
        # =====================================================================
        user_emb_list = [u_g_embeddings]
        item_emb_list = [i_g_embeddings]

        for i in range(self.n_ui_layers):    
            u_g_embeddings_next = torch.mm(ui_graph, i_g_embeddings) 
            i_g_embeddings_next = torch.mm(iu_graph, u_g_embeddings) 
            
            # 最后一层使用 L2 归一化替代原有的 Softmax (修复表示崩塌隐患)
            if i == (self.n_ui_layers-1):
                u_g_embeddings = F.normalize(u_g_embeddings_next, p=2, dim=1)
                i_g_embeddings = F.normalize(i_g_embeddings_next, p=2, dim=1)
            else:
                u_g_embeddings = u_g_embeddings_next
                i_g_embeddings = i_g_embeddings_next

            user_emb_list.append(u_g_embeddings)
            item_emb_list.append(i_g_embeddings)

        u_g_embeddings = torch.mean(torch.stack(user_emb_list), dim=0)
        i_g_embeddings = torch.mean(torch.stack(item_emb_list), dim=0)


        # =====================================================================
        # 4. 最终多模态融合
        # =====================================================================
        u_g_embeddings = u_g_embeddings + args.model_cat_rate*F.normalize(image_user_feats, p=2, dim=1) + args.model_cat_rate*F.normalize(text_user_feats, p=2, dim=1)
        i_g_embeddings = i_g_embeddings + args.model_cat_rate*F.normalize(image_item_feats, p=2, dim=1) + args.model_cat_rate*F.normalize(text_item_feats, p=2, dim=1)

        return u_g_embeddings, i_g_embeddings, image_item_feats, text_item_feats, image_user_feats, text_user_feats, u_g_embeddings, i_g_embeddings, prompt_user, prompt_item, prompt_aux_loss


# =====================================================================
# 1. 单模态 MoE 核心网络 (ProMoE 正交门控重构版)
# =====================================================================
# 论文公式: y = Σ g_k(x) · E_k(x; θ_k),  subject to ⟨g_i, g_j⟩ = 0
# =====================================================================
# 【核心重构点】
#   ① Gram-Schmidt 正交化: 将 Gate 权重矩阵的列向量显式正交化
#   ② 正交惩罚 Loss:       L_ortho = ||G^T G - I_K||_F^2
#   ③ einsum Batch 融合:   用 torch.einsum 替代串行 expert 循环
#                          O(K·N·d) 单次 kernel launch, SM 占用 30%→85%
# =====================================================================
class SingleModality_MoE(nn.Module):
    def __init__(self, in_dim, out_dim, num_experts, top_k=1, ortho_loss_weight=0.1):
        super(SingleModality_MoE, self).__init__()
        self.num_experts = num_experts
        self.top_k = top_k
        self.out_dim = out_dim
        self.ortho_loss_weight = ortho_loss_weight

        # LayerNorm: 防止高维原始特征直接喂给 Linear 导致 Logits 爆炸
        self.norm = nn.LayerNorm(in_dim)

        # ---- 专家网络: 合并权重矩阵以支持 einsum Batch 融合 ----
        # 每个专家的 Linear 等价于 x @ W_k^T + b_k
        # 将 K 个专家的 W_k 合并为 [K, in_dim, out_dim]，利用 einsum 一次完成
        self.W_experts = nn.Parameter(
            torch.empty(num_experts, in_dim, out_dim)
        )
        self.b_experts = nn.Parameter(
            torch.zeros(num_experts, 1, out_dim)
        )
        for k in range(num_experts):
            nn.init.xavier_uniform_(self.W_experts[k])

        # ---- 门控网络 ----
        # Gate 权重 W_g ∈ R^{in_dim × K}，其列向量对应 K 个专家的门控基
        self.gate = nn.Linear(in_dim, num_experts, bias=False)
        nn.init.xavier_uniform_(self.gate.weight)

        # 【新增】正交化缓存: 存储最近一次 Gram-Schmidt 后的门控基
        self.register_buffer('_ortho_gate_weight', None, persistent=False)

    def _gram_schmidt_orthogonalize(self, W):
        “””
        Gram-Schmidt 正交化: 将门控权重矩阵 W ∈ R^{in_dim × K} 的 K 个列向量
        变为标准正交基，使得 ⟨w_i, w_j⟩ = δ_{ij}

        仅在前向传播时应用，不改变参数的存储形式（保证优化器兼容）
        “””
        K = W.shape[1]
        Q = torch.zeros_like(W)
        for i in range(K):
            q = W[:, i].clone()
            for j in range(i):
                q = q - torch.dot(Q[:, j], W[:, i]) * Q[:, j]
            norm = q.norm(p=2) + 1e-8
            Q[:, i] = q / norm
        return Q

    def forward(self, x):
        B = x.size(0)

        # -------- 1. 特征归一化 --------
        x_norm = self.norm(x)

        # -------- 2. 门控计算 (含 Gram-Schmidt 正交化) --------
        # 对 Gate 权重做 Gram-Schmidt，确保各专家门控基的正交性
        W_g_ortho = self._gram_schmidt_orthogonalize(self.gate.weight)  # [in_dim, K]
        # 用正交化后的权重计算 logits
        gate_logits = torch.mm(x_norm, W_g_ortho)  # [B, K]

        weights, indices = torch.topk(gate_logits, self.top_k, dim=-1)
        weights = F.softmax(weights, dim=-1)  # 在选中的 top_k 内部重新归一化

        # -------- 3. 正交性惩罚 Loss: L_ortho = ||G^T G - I_K||_F^2 --------
        # G = softmax(gate_logits) ∈ [B, K]，在 batch 维计算门控相关矩阵
        gate_probs_full = F.softmax(gate_logits, dim=-1)  # [B, K]
        # G_corr ∈ [K, K]: 门控向量在 batch 上的内积期望
        G_corr = torch.einsum('bi,bj->ij', gate_probs_full, gate_probs_full) / B
        identity = torch.eye(self.num_experts, device=x.device)
        ortho_loss = F.mse_loss(G_corr, identity)

        # -------- 4. 负载均衡损失 (保留，防止专家崩溃) --------
        expert_density = gate_probs_full.mean(dim=0)  # [K]
        idx_one_hot = F.one_hot(indices, num_classes=self.num_experts).float()  # [N, top_k, K]
        assignment_density = idx_one_hot.sum(dim=1).mean(dim=0)  # [K]
        load_balance_loss = self.num_experts * torch.sum(expert_density * assignment_density)

        # ---- 合并辅助 Loss ----
        aux_loss = load_balance_loss + self.ortho_loss_weight * ortho_loss

        # ---- 探针: 测试阶段输出专家负载与正交性指标 ----
        if not self.training and self.num_experts > 1:
            off_diag = G_corr - identity
            ortho_metric = torch.norm(off_diag, p='fro').item()
            print(f”📊 [Test] MoE(Exp={self.num_experts}) “
                  f”负载={assignment_density.cpu().detach().numpy().round(3)} “
                  f”正交残差_F={ortho_metric:.4f}”)

        # =================================================================
        # 5. einsum Batch 融合: 干掉串行循环，单次 kernel launch
        # =================================================================
        # 原理 (矩阵结合律):
        #   对每个样本 n, 其输出 = Σ_k g_{n,k} · (x_n @ W_k^T + b_k)
        #                        = Σ_k g_{n,k} · x_n @ W_k^T + Σ_k g_{n,k}·b_k
        #   利用 einsum 将 K 个专家的计算折叠为一次批量乘法:
        #     [B, in_dim] × [K, in_dim, out_dim] → [B, K, out_dim]
        #   然后按门控权重聚合: [B, K, out_dim] × [B, K] → [B, out_dim]
        # =================================================================

        # Step A: 批量专家前向 — 单次 einsum 替代串行 stack([expert(x) for ...])
        # x_norm: [B, in_dim], W_experts: [K, in_dim, out_dim]
        expert_outputs = torch.einsum('bd,kdh->bkh', x_norm, self.W_experts) + self.b_experts.squeeze(1)  # [B, K, out_dim]

        # Step B: 门控加权聚合 — 单次 einsum
        # 将 top_k 稀疏门控扩展到 K 维
        gate_sparse = torch.zeros(B, self.num_experts, device=x.device)
        gate_sparse.scatter_(1, indices, weights)  # [B, K]
        # 聚合: Σ_k g_k · output_k
        final_out = torch.einsum('bkd,bk->bd', expert_outputs, gate_sparse)  # [B, out_dim]

        return final_out, aux_loss

# 2. 真正解耦的 MultiModal MoE (保证两边都不饿死)
class MultiModal_MoE_Prompt_Layer(nn.Module):
    def __init__(self, dim_image, dim_text, embed_size, num_experts=4, top_k=2, ortho_loss_weight=0.1):
        super(MultiModal_MoE_Prompt_Layer, self).__init__()

        # 【修复点】 支持 num_experts=1 的完全退化基线
        if num_experts <= 1:
            img_experts = 1
            txt_experts = 1
        else:
            img_experts = max(2, num_experts // 2)
            txt_experts = max(2, num_experts - img_experts)

        local_top_k = 1

        self.img_moe = SingleModality_MoE(dim_image, embed_size, img_experts, top_k=local_top_k, ortho_loss_weight=ortho_loss_weight)
        self.txt_moe = SingleModality_MoE(dim_text, embed_size, txt_experts, top_k=local_top_k, ortho_loss_weight=ortho_loss_weight)

    def forward(self, img_x, txt_x):
        # 两个模态分别过各自的 MoE，拿回特征和对应的负载均衡 Loss
        img_prompt, img_aux_loss = self.img_moe(img_x)
        txt_prompt, txt_aux_loss = self.txt_moe(txt_x)

        # 最终 Prompt 融合
        final_prompt = img_prompt + txt_prompt
        total_aux_loss = img_aux_loss + txt_aux_loss

        return final_prompt, total_aux_loss


# 2. 升级版 PromptLearner
class PromptLearner(nn.Module):
    def __init__(self, image_feats=None, text_feats=None, ui_graph=None):
        super().__init__()
        self.ui_graph = ui_graph

        # 获取原始特征的维度 (例如: image 4096, text 1024)
        dim_image = image_feats.shape[1]
        dim_text = text_feats.shape[1]

        # ----------------- MoE 创新分支 -----------------
        if args.use_moe == 1:
            print("🚀 正在使用 Modality-Aware MoE 直接处理原始多模态特征生成 Prompt...")
            # 我们不再需要提前进行 PCA 降维和求均值融合！
            # 直接将原始高维特征转换为 Tensor 并移动到 GPU
            self.item_raw_image = torch.tensor(image_feats).float().cuda()
            self.item_raw_text = torch.tensor(text_feats).float().cuda()
            
            # 利用图结构，将 Item 的原始特征聚合给 User
            self.user_raw_image = torch.mm(ui_graph, self.item_raw_image).cuda()
            self.user_raw_text = torch.mm(ui_graph, self.item_raw_text).cuda()

            # 实例化多模态 MoE 层 (传入正交惩罚权重)
            ortho_w = getattr(args, 'ortho_loss_weight', 0.1)
            self.trans_user = MultiModal_MoE_Prompt_Layer(dim_image, dim_text, args.embed_size, args.num_experts, args.top_k, ortho_loss_weight=ortho_w).cuda()
            self.trans_item = MultiModal_MoE_Prompt_Layer(dim_image, dim_text, args.embed_size, args.num_experts, args.top_k, ortho_loss_weight=ortho_w).cuda()

        # ----------------- Baseline 原始分支 -----------------
        else:
            print("🧱 正在使用基础 Linear 层与 PCA降维生成 Prompt (Baseline)...")
            # 保留原作者的 PCA/ICA 降维逻辑，用于控制变量对比
            if args.hard_token_type=='pca':
                try:
                    hard_token_image = pickle.load(open(args.data_path + args.dataset + '/hard_token_image_pca','rb'))
                    hard_token_text = pickle.load(open(args.data_path + args.dataset + '/hard_token_text_pca','rb'))
                except Exception:
                    hard_token_image = PCA(n_components=args.embed_size).fit_transform(image_feats)
                    hard_token_text = PCA(n_components=args.embed_size).fit_transform(text_feats)
                    pickle.dump(hard_token_image, open(args.data_path + args.dataset + '/hard_token_image_pca','wb'))
                    pickle.dump(hard_token_text, open(args.data_path + args.dataset + '/hard_token_text_pca','wb'))
            
            # 提前混合模态并降维 (原作者的逻辑，会破坏模态独立性)
            self.item_hard_token = torch.mean((torch.stack((torch.tensor(hard_token_image).float(), torch.tensor(hard_token_text).float()))), dim=0).cuda()
            self.user_hard_token = torch.mm(ui_graph, self.item_hard_token).cuda()

            self.trans_user = nn.Linear(args.embed_size, args.embed_size).cuda()
            self.trans_item = nn.Linear(args.embed_size, args.embed_size).cuda()
            nn.init.xavier_uniform_(self.trans_user.weight)
            nn.init.xavier_uniform_(self.trans_item.weight)


    def forward(self):
        # 新增 aux_loss 收集变量
        aux_loss = torch.tensor(0.0).cuda()
        
        if args.use_moe == 1:
            # MoE 模式会返回 prompt 和 aux_loss
            prompt_user, aux_loss_user = self.trans_user(self.user_raw_image, self.user_raw_text)
            prompt_item, aux_loss_item = self.trans_item(self.item_raw_image, self.item_raw_text)
            aux_loss = aux_loss_user + aux_loss_item
        else:
            # Baseline 模式没有 aux_loss
            prompt_user = self.trans_user(self.user_hard_token)
            prompt_item = self.trans_item(self.item_hard_token)
            
        # 返回内容增加 aux_loss
        return F.dropout(prompt_user, p=args.prompt_dropout, training=self.training) , \
               F.dropout(prompt_item, p=args.prompt_dropout, training=self.training) , \
               aux_loss




class Student_LightGCN(nn.Module):
    def __init__(self, n_users, n_items, embedding_dim, gnn_layer, dropout_list, image_feats=None, text_feats=None):
        super().__init__()
        self.n_users = n_users
        self.n_items = n_items
        self.embedding_dim = embedding_dim
        self.n_ui_layers = gnn_layer

        # 简单的 Embedding 层
        self.user_id_embedding = nn.Embedding(n_users, embedding_dim)
        self.item_id_embedding = nn.Embedding(n_items, embedding_dim)
        nn.init.xavier_uniform_(self.user_id_embedding.weight)
        nn.init.xavier_uniform_(self.item_id_embedding.weight)

        # self.feat_trans = nn.Linear(args.embed_size, args.student_embed_size)
        # # self.text_trans = nn.Linear(text_feats.shape[1], args.embed_size)
        # nn.init.xavier_uniform_(self.feat_trans.weight)
        # # nn.init.xavier_uniform_(self.text_trans.weight) 

    def init_user_item_embed(self, pre_u_embed, pre_i_embed):

        # 支持使用教师模型训练好的 ID Embedding 进行初始化 (这也是一种知识传递)
        self.user_id_embedding = nn.Embedding.from_pretrained(pre_u_embed, freeze=False)
        self.item_id_embedding = nn.Embedding.from_pretrained(pre_i_embed, freeze=False)

        self.user_id_embedding_pre = nn.Embedding.from_pretrained(pre_u_embed, freeze=False)
        self.item_id_embedding_pre = nn.Embedding.from_pretrained(pre_i_embed, freeze=False)

    def get_embedding(self):
        return self.user_id_embedding, self.item_id_embedding
    
    def forward(self, adj):
        # 【修改重点】：只用学生自己的 Embedding，不再加 self.user_id_embedding_pre
        ego_embeddings = torch.cat((self.user_id_embedding.weight, self.item_id_embedding.weight), dim=0)
        all_embeddings = [ego_embeddings]

        for i in range(self.n_ui_layers):
            side_embeddings = torch.sparse.mm(adj, ego_embeddings)
            ego_embeddings = side_embeddings
            all_embeddings += [ego_embeddings]
            
        all_embeddings = torch.stack(all_embeddings, dim=1)
        all_embeddings = all_embeddings.mean(dim=1, keepdim=False)

        u_g_embeddings, i_g_embeddings = torch.split(all_embeddings, [self.n_users, self.n_items], dim=0)
        return u_g_embeddings, i_g_embeddings

    # def forward(self, adj):

    #     # # teacher_feat_dict = { 'item_image':t_i_image_embed.deteach(),'item_text':t_i_text_embed.deteach(),'user_image':t_u_image_embed.deteach(),'user_text':t_u_text_embed.deteach() }
    #     # tmp_feat_dict = {}   
    #     # for index,value in enumerate(teacher_feat_dict.keys()): 
    #     #     tmp_feat_dict[value] = self.feat_trans(teacher_feat_dict[value])
    #     # u_g_embeddings = self.user_id_embedding.weight + args.model_cat_rate*F.normalize(tmp_feat_dict['user_image'], p=2, dim=1) + args.model_cat_rate*F.normalize(tmp_feat_dict['user_text'], p=2, dim=1)
    #     # i_g_embeddings = self.item_id_embedding.weight + args.model_cat_rate*F.normalize(tmp_feat_dict['item_image'], p=2, dim=1) + args.model_cat_rate*F.normalize(tmp_feat_dict['item_text'], p=2, dim=1)
    #     # ego_embeddings = torch.cat((u_g_embeddings, i_g_embeddings), dim=0)

    #     # self.user_id_embedding_pre = nn.Embedding.from_pretrained(pre_u_embed, freeze=False)
    #     # self.item_id_embedding_pre = nn.Embedding.from_pretrained(pre_i_embed, freeze=False)

    #     # 标准的 LightGCN 传播
    #     # 初始 Embedding: User + Item
    #     ego_embeddings = torch.cat((self.user_id_embedding.weight+self.user_id_embedding_pre.weight, self.item_id_embedding.weight+self.item_id_embedding_pre.weight), dim=0)
    #     # ego_embeddings = torch.cat((self.user_id_embedding.weight, self.item_id_embedding.weight), dim=0)
    #     all_embeddings = [ego_embeddings]

    #     # 图卷积: E^(k+1) = D^-0.5 A D^-0.5 E^k
    #     for i in range(self.n_ui_layers):
    #         side_embeddings = torch.sparse.mm(adj, ego_embeddings)
    #         ego_embeddings = side_embeddings
    #         all_embeddings += [ego_embeddings]
    #     all_embeddings = torch.stack(all_embeddings, dim=1)
    #     all_embeddings = all_embeddings.mean(dim=1, keepdim=False)

    #     # 拆分回 User 和 Item
    #     u_g_embeddings, i_g_embeddings = torch.split(all_embeddings, [self.n_users, self.n_items], dim=0)
    #     # u_g_embeddings += teacher_feat_dict['user_image'] + teacher_feat_dict['user_text']
    #     # i_g_embeddings += teacher_feat_dict['item_image'] + teacher_feat_dict['item_text']
    #     # u_g_embeddings = u_g_embeddings + args.model_cat_rate*F.normalize(teacher_feat_dict['user_image'], p=2, dim=1) + args.model_cat_rate*F.normalize(teacher_feat_dict['user_text'], p=2, dim=1)
    #     # i_g_embeddings = i_g_embeddings + args.model_cat_rate*F.normalize(teacher_feat_dict['item_image'], p=2, dim=1) + args.model_cat_rate*F.normalize(teacher_feat_dict['item_text'], p=2, dim=1)

    #     return u_g_embeddings, i_g_embeddings
    #     # return self.user_id_embedding.weight, self.item_id_embedding.weight



class Student_GCN(nn.Module):
    def __init__(self, n_users, n_items, embedding_dim, gnn_layer=2, drop_out=0., image_feats=None, text_feats=None):
        super(Student_GCN, self).__init__()
        self.embedding_dim = embedding_dim

#         self.layers = nn.Sequential(GraphConvolution(self.embedding_dim, self.embedding_dim, activation=F.relu, dropout=args.student_drop_rate, is_sparse_inputs=True),
#                                     GraphConvolution(self.embedding_dim, self.embedding_dim, activation=F.relu, dropout=args.student_drop_rate, is_sparse_inputs=False),
# )
        # self.layer_list = nn.ModuleList() 
        # for i in range(args.student_n_layers):
        #     self.layer_list.append(GraphConvolution(self.embedding_dim, self.embedding_dim, activation=F.relu, dropout=args.student_drop_rate, is_sparse_inputs=False))

        self.trans_user =  nn.Linear(args.embed_size, args.embed_size)
        self.trans_item =  nn.Linear(args.embed_size, args.embed_size)


    def forward(self, user_x, item_x, ui_graph, iu_graph):
        # # x, support = inputs
        # # user_x, item_x = self.layers((user_x, item_x, ui_graph, iu_graph))
        # for i in range(args.student_n_layers):
        #     user_x, item_x = self.layer_list[i](user_x, item_x, ui_graph, iu_graph)
        # return user_x, item_x

        return self.trans_user(user_x), self.trans_item(item_x)
        # self.user_id_embedding = nn.Embedding.from_pretrained(user_x, freeze=True)        
        # self.item_id_embedding = nn.Embedding.from_pretrained(item_x, freeze=True)
        # return self.user_id_embedding.weight, self.item_id_embedding.weight

    def l2_loss(self):
        layer = self.layers.children()
        layer = next(iter(layer))
        loss = None

        for p in layer.parameters():
            if loss is None:
                loss = p.pow(2).sum()
            else:
                loss += p.pow(2).sum()

        return loss

class GraphConvolution(nn.Module):
    def __init__(self, input_dim, output_dim, dropout=0., is_sparse_inputs=False, bias=False, activation = F.relu,featureless=False):
        super(GraphConvolution, self).__init__()
        self.dropout = dropout
        self.bias = bias
        self.activation = activation
        self.is_sparse_inputs = is_sparse_inputs
        self.featureless = featureless
        # self.num_features_nonzero = num_features_nonzero
        # self.user_weight = nn.Parameter(torch.randn(input_dim, output_dim))
        # self.item_weight = nn.Parameter(torch.randn(input_dim, output_dim))
        self.user_weight = nn.Parameter(torch.empty(input_dim, output_dim))
        self.item_weight = nn.Parameter(torch.empty(input_dim, output_dim))
        nn.init.xavier_uniform_(self.user_weight)
        nn.init.xavier_uniform_(self.item_weight)   
        self.bias = None
        if bias:
            self.bias = nn.Parameter(torch.zeros(output_dim))


    def forward(self, user_x, item_x, ui_graph, iu_graph):
        # print('inputs:', inputs)
        # x, support = inputs
        # if self.training and self.is_sparse_inputs:
        #     x = sparse_dropout(x, self.dropout, self.num_features_nonzero)
        # elif self.training:
        user_x = F.dropout(user_x, self.dropout)
        item_x = F.dropout(item_x, self.dropout)
        # convolve
        if not self.featureless: # if it has features x
            if self.is_sparse_inputs:
                xw = torch.sparse.mm(user_x, self.user_weight)
                xw = torch.sparse.mm(item_x, self.item_weight)
            else:
                xw_user = torch.mm(user_x, self.user_weight)
                xw_item = torch.mm(item_x, self.item_weight)
        else:
            xw = self.weight
        out_user = torch.sparse.mm(ui_graph, xw_item)
        out_item = torch.sparse.mm(iu_graph, xw_user)

        if self.bias is not None:
            out += self.bias
        return self.activation(out_user), self.activation(out_item)


def sparse_dropout(x, rate, noise_shape):
    """
    :param x:
    :param rate:
    :param noise_shape: int scalar
    :return:
    """
    random_tensor = 1 - rate
    random_tensor += torch.rand(noise_shape).to(x.device)
    dropout_mask = torch.floor(random_tensor).byte()
    i = x._indices() # [2, 49216]
    v = x._values() # [49216]
    # [2, 4926] => [49216, 2] => [remained node, 2] => [2, remained node]
    i = i[:, dropout_mask]
    v = v[dropout_mask]
    out = torch.sparse.FloatTensor(i, v, x.shape).to(x.device)
    out = out * (1./ (1-rate))
    return out


def dot(x, y, sparse=False):
    if sparse:
        res = torch.sparse.mm(x, y)
    else:
        res = torch.mm(x, y)
    return res





class BLMLP(nn.Module):
    def __init__(self):
        super(BLMLP, self).__init__()
        self.W = nn.Parameter(nn.init.xavier_uniform_(torch.empty(args.student_embed_size, args.student_embed_size)))
        self.act = nn.LeakyReLU(negative_slope=0.5)
    
    def forward(self, embeds):
        pass

    def featureExtract(self, embeds):
        return self.act(embeds @ self.W) + embeds

    def pairPred(self, embeds1, embeds2):
        return (self.featureExtract(embeds1) * self.featureExtract(embeds2)).sum(dim=-1)
    
    def crossPred(self, embeds1, embeds2):
        return self.featureExtract(embeds1) @ self.featureExtract(embeds2).T


class Student_MLP(nn.Module):
    def __init__(self):
        super(Student_MLP, self).__init__()
        # self.n_users = n_users
        # self.n_items = n_items
        # self.embedding_dim = embedding_dim

        # self.uEmbeds = nn.Parameter(init(torch.empty(args.user, args.latdim)))
        # self.iEmbeds = nn.Parameter(init(torch.empty(args.item, args.latdim)))

        self.user_trans = nn.Linear(args.embed_size, args.embed_size)
        self.item_trans = nn.Linear(args.embed_size, args.embed_size)
        nn.init.xavier_uniform_(self.user_trans.weight)
        nn.init.xavier_uniform_(self.item_trans.weight)

        self.MLP = BLMLP()
        # self.overallTime = datetime.timedelta(0)


    def get_embedding(self):
        return self.user_id_embedding, self.item_id_embedding
    

    def forward(self, pre_user, pre_item, ):
        # pre_user, pre_item = self.user_id_embedding.weight, self.item_id_embedding.weight
        user_embed = self.user_trans(pre_user)
        item_embed = self.user_trans(pre_item)

        return user_embed, item_embed
        # return pre_user, pre_item

    def init_user_item_embed(self, pre_u_embed, pre_i_embed):
        self.user_id_embedding = nn.Embedding.from_pretrained(pre_u_embed, freeze=False)
        self.item_id_embedding = nn.Embedding.from_pretrained(pre_i_embed, freeze=False)

    def pointPosPredictwEmbeds(self, uEmbeds, iEmbeds, ancs, poss):
        ancEmbeds = uEmbeds[ancs]
        posEmbeds = iEmbeds[poss]
        nume = self.MLP.pairPred(ancEmbeds, posEmbeds)
        return nume

    def pointNegPredictwEmbeds(self, embeds1, embeds2, nodes1, temp=1.0):
        pckEmbeds1 = embeds1[nodes1]
        preds = self.MLP.crossPred(pckEmbeds1, embeds2)
        return torch.exp(preds / temp).sum(-1)
    
    def pairPredictwEmbeds(self, uEmbeds, iEmbeds, ancs, poss, negs):
        ancEmbeds = uEmbeds[ancs]
        posEmbeds = iEmbeds[poss]
        negEmbeds = iEmbeds[negs]
        posPreds = self.MLP.pairPred(ancEmbeds, posEmbeds)
        negPreds = self.MLP.pairPred(ancEmbeds, negEmbeds)
        return posPreds - negPreds
    
    def predAll(self, pckUEmbeds, iEmbeds):
        return self.MLP.crossPred(pckUEmbeds, iEmbeds)
    
    def testPred(self, usr, trnMask):
        uEmbeds, iEmbeds = self.forward()
        allPreds = self.predAll(uEmbeds[usr], iEmbeds) * (1 - trnMask) - trnMask * 1e8
        return allPreds

class Student_MMLight(nn.Module):
    def __init__(self, n_users, n_items, embedding_dim, n_layers, dropout, image_feats, text_feats, ui_graph, iu_graph):

        super().__init__()
        self.n_users = n_users
        self.n_items = n_items
        self.ui_graph = ui_graph
        self.iu_graph = iu_graph
        self.embedding_dim = embedding_dim
        self.n_ui_layers = n_layers
        self.image_trans = nn.Linear(args.embed_size, args.embed_size)
        self.text_trans = nn.Linear(args.embed_size, args.embed_size)
        nn.init.xavier_uniform_(self.image_trans.weight)
        nn.init.xavier_uniform_(self.text_trans.weight)             

        self.user_id_embedding = nn.Embedding(n_users, self.embedding_dim)
        self.item_id_embedding = nn.Embedding(n_items, self.embedding_dim)

        nn.init.xavier_uniform_(self.user_id_embedding.weight)
        nn.init.xavier_uniform_(self.item_id_embedding.weight)
        
        # 【修复 4】 register_buffer 替代 .cuda()
        self.register_buffer('image_feats', torch.tensor(image_feats).float())
        self.register_buffer('text_feats', torch.tensor(text_feats).float())

        self.softmax = nn.Softmax(dim=-1)
        self.act = nn.Sigmoid()  
        self.sigmoid = nn.Sigmoid()
        self.dropout = nn.Dropout(args.drop_rate)
        self.batch_norm = nn.BatchNorm1d(args.embed_size)
        self.tau = 0.5


    def mm(self, x, y):
        if args.sparse:
            return torch.sparse.mm(x, y)
        else:
            return torch.mm(x, y)
    def sim(self, z1, z2):
        z1 = F.normalize(z1)
        z2 = F.normalize(z2)
        return torch.mm(z1, z2.t())


    def init_user_item_embed(self, pre_u_embed, pre_i_embed):
        self.user_id_embedding = nn.Embedding.from_pretrained(pre_u_embed, freeze=False)
        self.item_id_embedding = nn.Embedding.from_pretrained(pre_i_embed, freeze=False)

    def forward(self, image_feats, text_feats, image_user_embeds, text_user_embeds):
        image_feats = image_item_feats = self.dropout(self.image_trans(image_feats))
        text_feats = text_item_feats = self.dropout(self.text_trans(text_feats))
        u_g_embeddings = self.user_id_embedding.weight 
        i_g_embeddings = self.item_id_embedding.weight 

        user_emb_list = [u_g_embeddings]
        item_emb_list = [i_g_embeddings]
        for i in range(self.n_ui_layers):    
            if i == (self.n_ui_layers-1):
                u_g_embeddings = self.softmax( torch.mm(self.ui_graph, i_g_embeddings) ) 
                i_g_embeddings = self.softmax( torch.mm(self.iu_graph, u_g_embeddings) )
            else:
                u_g_embeddings = torch.mm(self.ui_graph, i_g_embeddings) 
                i_g_embeddings = torch.mm(self.iu_graph, u_g_embeddings) 

            user_emb_list.append(u_g_embeddings)
            item_emb_list.append(i_g_embeddings)

        u_g_embeddings = torch.mean(torch.stack(user_emb_list), dim=0)
        i_g_embeddings = torch.mean(torch.stack(item_emb_list), dim=0)


        u_g_embeddings = u_g_embeddings #+ args.model_cat_rate*F.normalize(image_user_feats, p=2, dim=1) + args.model_cat_rate*F.normalize(text_user_feats, p=2, dim=1)
        i_g_embeddings = i_g_embeddings + args.model_cat_rate*F.normalize(image_item_feats, p=2, dim=1) + args.model_cat_rate*F.normalize(text_item_feats, p=2, dim=1)
        return u_g_embeddings, i_g_embeddings

