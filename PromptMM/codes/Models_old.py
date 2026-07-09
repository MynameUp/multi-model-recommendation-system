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
        self.image_feats = torch.tensor(image_feats).float().cuda()
        self.text_feats = torch.tensor(text_feats).float().cuda()
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


    def forward(self, ui_graph, iu_graph, prompt_module=None):

    # def forward(self, ui_graph, iu_graph):

        # 1. 获取 Prompt
        # prompt_user, prompt_item  = prompt_module()  # [n*32]
    
        # 替换为以下代码：
        prompt_outputs = prompt_module()
        if len(prompt_outputs) == 3:
            prompt_user, prompt_item, prompt_aux_loss = prompt_outputs
        else:
            prompt_user, prompt_item = prompt_outputs
            prompt_aux_loss = torch.tensor(0.0).cuda()
        # ----feature prompt----

        # [画图原理] Prompt-enhanced Features (Prompt 增强特征)
        # 对应图中：Prompt 向量与原始 Image/Text 特征交互的部分
        # 代码逻辑：计算 Prompt 与 特征 的相关性，生成特征层面的 Prompt
        # 利用 Soft Prompt 对原始特征进行增强。
        # 计算方式: Prompt * (Prompt^T * Feature) -> 利用 Prompt 提取特征中的相关分量
        feat_prompt_item_image = torch.mm(prompt_item, torch.mm(prompt_item.T, self.image_feats))
        feat_prompt_item_text = torch.mm(prompt_item, torch.mm(prompt_item.T, self.text_feats))

        # 原始特征 + 归一化后的 Prompt 增强特征，再过线性层
        image_feats = image_item_feats = self.dropout(self.image_trans(self.image_feats + args.feat_soft_token_rate*F.normalize(feat_prompt_item_image, p=2, dim=1) ))  
        text_feats = text_item_feats = self.dropout(self.text_trans(self.text_feats + args.feat_soft_token_rate*F.normalize(feat_prompt_item_text, p=2, dim=1) ))

        # 多模态特征的图传播 (GCN)
        # 对应图中多层的 Graph Convolution 模块, 让 User 聚合交互过的 Item 的图片/文本特征
        for i in range(args.layers):
            image_user_feats = self.mm(ui_graph, image_feats)
            image_item_feats = self.mm(iu_graph, image_user_feats)

            text_user_feats = self.mm(ui_graph, text_feats)
            text_item_feats = self.mm(iu_graph, text_user_feats)


        # ID Embedding 的 Prompt 注入 (Soft Prompt Tuning)
        # 最终 ID 表示 = 基础 ID Embedding + 归一化 Soft Prompt
        u_g_embeddings = self.user_id_embedding.weight  + args.soft_token_rate*F.normalize(prompt_user, p=2, dim=1)
        i_g_embeddings = self.item_id_embedding.weight  + args.soft_token_rate*F.normalize(prompt_item, p=2, dim=1)
        user_emb_list = [u_g_embeddings]
        item_emb_list = [i_g_embeddings]

        # ID Embedding 的图传播
        for i in range(self.n_ui_layers):    
            if i == (self.n_ui_layers-1):
                u_g_embeddings = self.softmax( torch.mm(ui_graph, i_g_embeddings) ) 
                i_g_embeddings = self.softmax( torch.mm(iu_graph, u_g_embeddings) )

            else:
                u_g_embeddings = torch.mm(ui_graph, i_g_embeddings) 
                i_g_embeddings = torch.mm(iu_graph, u_g_embeddings) 

            user_emb_list.append(u_g_embeddings)
            item_emb_list.append(i_g_embeddings)

        # 取所有层的均值作为最终 ID 表示
        u_g_embeddings = torch.mean(torch.stack(user_emb_list), dim=0)
        i_g_embeddings = torch.mean(torch.stack(item_emb_list), dim=0)

        # [画图原理] Multi-modal Fusion (多模态融合)
        # 对应图中最后的 Concatenation 或 Summation 模块

        # 最终融合 (Final Concatenation/Sum)
        # 融合 ID 表示、图像表示、文本表示
        u_g_embeddings = u_g_embeddings + args.model_cat_rate*F.normalize(image_user_feats, p=2, dim=1) + args.model_cat_rate*F.normalize(text_user_feats, p=2, dim=1)
        i_g_embeddings = i_g_embeddings + args.model_cat_rate*F.normalize(image_item_feats, p=2, dim=1) + args.model_cat_rate*F.normalize(text_item_feats, p=2, dim=1)

        # 在 forward 的最末尾 return 的时候，把 prompt_aux_loss 也传出去
        return u_g_embeddings, i_g_embeddings, image_item_feats, text_item_feats, image_user_feats, text_user_feats, u_g_embeddings, i_g_embeddings, prompt_user, prompt_item, prompt_aux_loss


# 1. 单模态 MoE 核心网络 (修复路由崩溃与特征未对齐)
class SingleModality_MoE(nn.Module):
    def __init__(self, in_dim, out_dim, num_experts, top_k=1):
        super(SingleModality_MoE, self).__init__()
        self.num_experts = num_experts
        self.top_k = top_k
        self.out_dim = out_dim
        
        # 【修复点 3】 加入 LayerNorm，防止高维原始特征直接喂给 Linear 导致 Logits 爆炸
        self.norm = nn.LayerNorm(in_dim)
        
        # 专家网络
        self.experts = nn.ModuleList([
            nn.Linear(in_dim, out_dim) for _ in range(num_experts)
        ])
        
        # 门控网络
        self.gate = nn.Linear(in_dim, num_experts)
        
        # 初始化
        for expert in self.experts:
            nn.init.xavier_uniform_(expert.weight)
        nn.init.xavier_uniform_(self.gate.weight)

    def forward(self, x):
        # 1. 特征归一化
        x_norm = self.norm(x)
        
        # 2. 门控计算
        gate_logits = self.gate(x_norm)
        weights, indices = torch.topk(gate_logits, self.top_k, dim=-1)
        weights = F.softmax(weights, dim=-1) # 在选中的 top_k 内部重新归一化
        
        # 【修复点 2】 计算负载均衡损失 (Load Balancing Loss)
        # 目标：强制 Gate 将样本均匀分配给每个专家，防止“旱的旱死，涝的涝死”
        gate_probs = F.softmax(gate_logits, dim=-1) # [N, num_experts]
        expert_density = gate_probs.mean(dim=0)     # 每个专家获得的概率均值 [num_experts]
        
        idx_one_hot = F.one_hot(indices, num_classes=self.num_experts).float() # [N, top_k, num_experts]
        assignment_density = idx_one_hot.sum(dim=1).mean(dim=0)                # 每个专家实际被选中的频率 [num_experts]
        
        aux_loss = self.num_experts * torch.sum(expert_density * assignment_density)
        
        # 3. 专家前向传播
        # 注意：为了代码简单，这里采用计算所有专家后 Gather 的方式。
        # 你的 num_experts 很小，这种做法在 GPU 上矩阵乘法并行度更高。
        all_expert_outputs = torch.stack([expert(x_norm) for expert in self.experts], dim=1) # [N, num_experts, out_dim]
        
        final_out = torch.zeros(x.size(0), self.out_dim, device=x.device)
        for i in range(self.top_k):
            exp_idx = indices[:, i] # [N]
            exp_weight = weights[:, i].unsqueeze(1) # [N, 1]
            selected_out = all_expert_outputs[torch.arange(x.size(0)), exp_idx]
            final_out += exp_weight * selected_out
            
        return final_out, aux_loss

# 2. 真正解耦的 MultiModal MoE (保证两边都不饿死)
class MultiModal_MoE_Prompt_Layer(nn.Module):
    def __init__(self, dim_image, dim_text, embed_size, num_experts=4, top_k=2):
        super(MultiModal_MoE_Prompt_Layer, self).__init__()
        
        # 【修复点 1】 解耦模态。
        # 如果总专家数是 4，我们分给 Image 2个，分给 Text 2个。
        # 这里强制子 MoE 的 top_k = 1，这意味着每个模态会激活 1 个专家，总共激活 2 个，保持你的计算预算不变。
        img_experts = max(2, num_experts // 2)
        txt_experts = max(2, num_experts - img_experts)
        local_top_k = 1 
        
        self.img_moe = SingleModality_MoE(dim_image, embed_size, img_experts, top_k=local_top_k)
        self.txt_moe = SingleModality_MoE(dim_text, embed_size, txt_experts, top_k=local_top_k)

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

            # 实例化多模态 MoE 层
            self.trans_user = MultiModal_MoE_Prompt_Layer(dim_image, dim_text, args.embed_size, args.num_experts, args.top_k).cuda()
            self.trans_item = MultiModal_MoE_Prompt_Layer(dim_image, dim_text, args.embed_size, args.num_experts, args.top_k).cuda()

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

        # # teacher_feat_dict = { 'item_image':t_i_image_embed.deteach(),'item_text':t_i_text_embed.deteach(),'user_image':t_u_image_embed.deteach(),'user_text':t_u_text_embed.deteach() }
        # tmp_feat_dict = {}   
        # for index,value in enumerate(teacher_feat_dict.keys()): 
        #     tmp_feat_dict[value] = self.feat_trans(teacher_feat_dict[value])
        # u_g_embeddings = self.user_id_embedding.weight + args.model_cat_rate*F.normalize(tmp_feat_dict['user_image'], p=2, dim=1) + args.model_cat_rate*F.normalize(tmp_feat_dict['user_text'], p=2, dim=1)
        # i_g_embeddings = self.item_id_embedding.weight + args.model_cat_rate*F.normalize(tmp_feat_dict['item_image'], p=2, dim=1) + args.model_cat_rate*F.normalize(tmp_feat_dict['item_text'], p=2, dim=1)
        # ego_embeddings = torch.cat((u_g_embeddings, i_g_embeddings), dim=0)

        # self.user_id_embedding_pre = nn.Embedding.from_pretrained(pre_u_embed, freeze=False)
        # self.item_id_embedding_pre = nn.Embedding.from_pretrained(pre_i_embed, freeze=False)

        # 标准的 LightGCN 传播
        # 初始 Embedding: User + Item
        ego_embeddings = torch.cat((self.user_id_embedding.weight+self.user_id_embedding_pre.weight, self.item_id_embedding.weight+self.item_id_embedding_pre.weight), dim=0)
        # ego_embeddings = torch.cat((self.user_id_embedding.weight, self.item_id_embedding.weight), dim=0)
        all_embeddings = [ego_embeddings]

        # 图卷积: E^(k+1) = D^-0.5 A D^-0.5 E^k
        for i in range(self.n_ui_layers):
            side_embeddings = torch.sparse.mm(adj, ego_embeddings)
            ego_embeddings = side_embeddings
            all_embeddings += [ego_embeddings]
        all_embeddings = torch.stack(all_embeddings, dim=1)
        all_embeddings = all_embeddings.mean(dim=1, keepdim=False)

        # 拆分回 User 和 Item
        u_g_embeddings, i_g_embeddings = torch.split(all_embeddings, [self.n_users, self.n_items], dim=0)
        # u_g_embeddings += teacher_feat_dict['user_image'] + teacher_feat_dict['user_text']
        # i_g_embeddings += teacher_feat_dict['item_image'] + teacher_feat_dict['item_text']
        # u_g_embeddings = u_g_embeddings + args.model_cat_rate*F.normalize(teacher_feat_dict['user_image'], p=2, dim=1) + args.model_cat_rate*F.normalize(teacher_feat_dict['user_text'], p=2, dim=1)
        # i_g_embeddings = i_g_embeddings + args.model_cat_rate*F.normalize(teacher_feat_dict['item_image'], p=2, dim=1) + args.model_cat_rate*F.normalize(teacher_feat_dict['item_text'], p=2, dim=1)

        return u_g_embeddings, i_g_embeddings
        # return self.user_id_embedding.weight, self.item_id_embedding.weight



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

        self.trans_user =  nn.Linear(args.embed_size, args.embed_size).cuda()
        self.trans_item =  nn.Linear(args.embed_size, args.embed_size).cuda()


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
        self.image_feats = torch.tensor(image_feats).float().cuda()
        self.text_feats = torch.tensor(text_feats).float().cuda()

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

