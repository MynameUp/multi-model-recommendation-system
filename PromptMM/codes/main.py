# 导入必要的库
from datetime import datetime #功能：处理日期和时间，本项目用途：主要用于生成日志文件（Log）的名称。例如，训练开始时，代码会获取当前时间（如 2023-10-27 10:00:00）作为文件名的一部分，防止不同实验的日志相互覆盖。
import math
import os #GPU 设置：虽然代码里主要用 torch.cuda，但有时会用 os.environ['CUDA_VISIBLE_DEVICES'] 来指定显卡。
import random #随机种子 (Seed)：设置随机种子以保证实验可复现（Reproducibility）。
import sys
from time import time #本项目用途：计时。计算每一个 Epoch（训练轮次）耗时多少秒，用于性能分析。
from tqdm import tqdm #本项目用途：在训练循环 (for idx in tqdm(range(n_batch)):) 中包裹迭代器，在控制台显示实时的训练进度条、剩余时间以及当前的 Loss 值。


import dgl #本项目用途：核心图结构处理。代码中用它将用户-物品交互矩阵转换为图对象 (dgl.heterograph)，用于后续在图上进行消息传递（Message Passing）或采样。虽然 LightGCN 手写了传播逻辑，但 DGL 可能用于辅助任务或复杂的 Teacher 模型。
import pickle #本项目用途：数据加载。项目中的数据集（如 train_mat）通常保存为 .pkl 二进制文件。使用 pickle.load() 可以快速将硬盘上的图结构数据读取到内存中。
import numpy as np
import scipy.sparse as sp #本项目用途：内存优化。推荐系统中的“用户-物品”矩阵极其稀疏（绝大多数用户只点击了极少数商品）。如果用普通数组存储会撑爆内存，必须使用 CSR 格式存储，只记录非零元素的位置和值。
from scipy.sparse import csr_matrix
# import  visdom #现状：被注释掉。说明作者可能早期用它画 Loss 曲线，但后来弃用了（可能转用了 TensorBoard 或直接看日志）。


import torch #本项目用途：定义张量（Tensor）、管理 GPU 设备 (.cuda())。
import torch.nn as nn #本项目用途：构建模型层。例如 nn.Linear (全连接层), nn.Embedding (嵌入层), nn.Dropout (随机失活), nn.Module (所有模型的基类)。
import torch.nn.functional as F #本项目用途：包含不需要维护状态的函数。如激活函数 (F.relu, F.leaky_relu)、归一化 (F.normalize)、Dropout 函数调用 (F.dropout)。
import torch.optim as optim #本项目用途：定义优化算法，用于更新模型参数。本项目使用了 optim.AdamW（Adam 的变体，带权重衰减，防止过拟合）。
import torch.sparse as sparse #本项目用途：LightGCN 的核心。将 SciPy 的稀疏矩阵转换为 PyTorch 的 SparseTensor，用于在 GPU 上高效执行图卷积中的稀疏矩阵乘法 (torch.sparse.mm)。
from torch import autograd #本项目用途：虽然通常不需要直接调用，但在某些高级操作（如梯度惩罚或自定义反向传播）中可能会用到。

import copy #本项目用途：模型保存。通常用于 best_model = copy.deepcopy(model)，在训练过程中，当发现当前 Epoch 的测试指标最好时，将模型参数深拷贝一份保存下来，防止后续训练变差后丢失最佳状态。

from utility.parser import args, select_dataset
# select_dataset()

# from utility.parser import parse_args
from Models import Teacher_Model, Student_LightGCN, Student_GCN, Student_MLP, PromptLearner
from utility.batch_test import * #本项目用途：计算 Recall@K, NDCG@K 等推荐系统评价指标。
from utility.logging import Logger #本项目用途：将控制台输出同时保存到 .log 文件中，方便后续查看实验记录。
from utility.norm import build_sim, build_knn_normalized_graph #本项目用途：用于构建 kNN 图或计算相似度矩阵，可能用于图结构的预处理或增强。
from torch.utils.tensorboard import SummaryWriter #本项目用途：可视化。在训练过程中记录 Loss 曲线、参数分布等，启动 TensorBoard 后可以在浏览器中看到漂亮的图表。


import setproctitle
setproctitle.setproctitle('EXP@wu') #本项目用途：服务器管理。当你在多人共用的 Linux 服务器上运行代码时，使用 top 或 ps 命令只能看到 python main.py，很难分清是谁的任务。这行代码将进程名修改为 EXP@weiw，让你能一眼认出这是你的任务，方便管理（比如 Kill 掉进程）。

# args = parse_args()
# from utility.parser import args, select_dataset

class Trainer(object):
    def __init__(self, data_config):
        # --- 日志与环境设置 ---
        # 创建基于时间的任务名，用于日志文件
        self.task_name = "%s_%s_%s" % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), args.dataset, args.cf_model,)
        self.logger = Logger(filename=self.task_name, is_debug=args.debug)
        self.logger.logging("PID: %d" % os.getpid())
        self.logger.logging(str(args))

        # --- 加载超参数 ---
        # 从 args 中提取常用参数到 self，方便调用
        self.mess_dropout = eval(args.mess_dropout)
        self.lr = args.lr
        self.student_lr = args.student_lr
        self.emb_dim = args.embed_size
        self.student_emb_dim = args.student_embed_size
        self.batch_size = args.batch_size
        self.weight_size = eval(args.weight_size)
        self.n_layers = len(self.weight_size)
        self.student_n_layers = args.student_n_layers
        self.regs = eval(args.regs)
        self.decay = self.regs[0]

        # [画图对应]: PromptMM.png 左侧的输入部分 (Input Data)
        # --- 加载多模态特征 ---
        # 加载预处理好的 .npy 文件。这些是经过 ResNet (图像) 和 BERT (文本) 提取并降维后的特征
        self.image_feats = np.load(args.data_path + '{}/image_feat.npy'.format(args.dataset))
        self.text_feats = np.load(args.data_path + '{}/text_feat.npy'.format(args.dataset))
        self.image_feat_dim = self.image_feats.shape[-1]
        self.text_feat_dim = self.text_feats.shape[-1]

        # 加载图结构 (User-Item Graph)
        self.ui_graph = self.ui_graph_raw = pickle.load(open(args.data_path + args.dataset + '/train_mat','rb'))

        # self.image_ui_graph_tmp = self.text_ui_graph_tmp = torch.tensor(self.ui_graph_raw.todense()).cuda()
        # self.image_iu_graph_tmp = self.text_iu_graph_tmp = torch.tensor(self.ui_graph_raw.T.todense()).cuda()

        # 构建 DGL 图和归一化邻接矩阵 self.adj，用于 LightGCN 传播
        #步骤 A：准备子矩阵 获取用户-物品矩阵和其转置(物品-用户矩阵)
        self.image_ui_index = {'x':[], 'y':[]}
        self.text_ui_index = {'x':[], 'y':[]}

        self.n_users = self.ui_graph.shape[0]
        self.n_items = self.ui_graph.shape[1]  
    
        #基于转置矩阵      
        self.iu_graph = self.ui_graph.T
        
        # --- 构建 DGL 图 (用于特定采样或辅助任务) ---
        # 将稀疏矩阵转换为 DGL 异构图格式

        # 构建 User -> Item 的图
        self.ui_graph_dgl = dgl.heterograph({('user','ui','item'):self.ui_graph.nonzero()})

        # 构建 Item -> User 的图 (基于转置矩阵)
        self.iu_graph_dgl = dgl.heterograph({('user','ui','item'):self.iu_graph.nonzero()})

        #步骤 B：归一化 (Normalization) 调用self.csr_norm 方法对两个子矩阵进行归一化。代码中使用了 mean_flag=True。
        self.ui_graph = self.csr_norm(self.ui_graph, mean_flag=True)
        self.iu_graph = self.csr_norm(self.iu_graph, mean_flag=True)

        #步骤 C：堆叠成大矩阵 A (用于 LightGCN 传播)
        # 结构: | 0   UI |  (注意：这里代码实现是 vstack([hstack([UI, 0]), hstack([0, IU])]) )
        #      | IU  0  |  (这种堆叠方式与标准 LightGCN 稍有不同，需配合模型 forward 理解)
        self.adj = sp.vstack([sp.hstack([self.ui_graph, csr_matrix((self.n_users, self.n_users))]), sp.hstack([csr_matrix((self.n_items, self.n_items)), self.iu_graph])])

        # 转换为 PyTorch Sparse Tensor 并移至 GPU
        self.ui_graph = self.matrix_to_tensor(self.ui_graph)
        self.iu_graph = self.matrix_to_tensor(self.iu_graph)
        self.adj = self.matrix_to_tensor(self.adj)  
        self.image_ui_graph = self.text_ui_graph = self.ui_graph
        self.image_iu_graph = self.text_iu_graph = self.iu_graph

        #[画图对应]: PromptMM.png 中间的核心模块实例化
        # 1. 初始化教师模型：输入包括 ID 数、特征维度、以及多模态特征矩阵
        self.teacher_model = Teacher_Model(self.n_users, self.n_items, self.emb_dim, self.weight_size, self.mess_dropout, self.image_feats, self.text_feats)      
        # self.student_model = Student_LightGCN(self.n_users, self.n_items, self.student_emb_dim, self.student_n_layers, self.mess_dropout, self.image_feats, self.text_feats)      
        self.teacher_model = self.teacher_model.cuda()
        # self.student_model = self.student_model.cuda()

        # 2. 初始化 Prompt 模块：这是 PromptMM 的核心创新点
        # 它需要 ui_graph 来初始化 User 的 Prompt (通过聚合 Item Prompt 得到)
        self.prompt_module = PromptLearner(self.image_feats, self.text_feats, self.ui_graph)

        self.bce = nn.BCEWithLogitsLoss()
        self.bce_loss = nn.BCELoss()        
        
        # 优化器：注意这里同时优化 教师模型参数 和 Prompt 参数
        self.opt_T = optim.AdamW([{'params':self.teacher_model.parameters()},
                                  {'params':self.prompt_module.parameters()}
                                  ], lr=self.lr, weight_decay=args.t_weight_decay)  
        # self.opt_S = optim.AdamW([{'params':self.student_model.parameters()},], lr=self.student_lr)  
       
        #配置学习率调度器
        # self.scheduler_D = self.set_lr_scheduler()


    # def set_lr_scheduler(self):
    #     fac = lambda epoch: 0.96 ** (epoch / 50)

    #     scheduler_D = optim.lr_scheduler.LambdaLR(self.optimizer_D, lr_lambda=fac)

    #     return scheduler_D

    #功能：对稀疏矩阵进行归一化（GCN 的预处理步骤）。
    def csr_norm(self, csr_mat, mean_flag=False):
        rowsum = np.array(csr_mat.sum(1))
        rowsum = np.power(rowsum+1e-8, -0.5).flatten() #构建度矩阵的逆平方根，加 1e-8 防止除以零
        rowsum[np.isinf(rowsum)] = 0.
        rowsum_diag = sp.diags(rowsum) #构建对角矩阵

        colsum = np.array(csr_mat.sum(0))
        colsum = np.power(colsum+1e-8, -0.5).flatten()
        colsum[np.isinf(colsum)] = 0.
        colsum_diag = sp.diags(colsum)
        

        #矩阵乘法归一化：
        if mean_flag == False:
            return rowsum_diag*csr_mat*colsum_diag
        else:
            return rowsum_diag*csr_mat

    #功能：将 SciPy 的稀疏矩阵 (csr_matrix 或 coo_matrix) 转换为 PyTorch 的 SparseTensor 并移动到 GPU。
    def matrix_to_tensor(self, cur_matrix):
        if type(cur_matrix) != sp.coo_matrix:
            cur_matrix = cur_matrix.tocoo()  #
        indices = torch.from_numpy(np.vstack((cur_matrix.row, cur_matrix.col)).astype(np.int64))  #
        values = torch.from_numpy(cur_matrix.data)  #
        shape = torch.Size(cur_matrix.shape)

        return torch.sparse.FloatTensor(indices, values, shape).to(torch.float32).cuda()  #

    def innerProduct(self, u_pos, i_pos, u_neg, j_neg):  
        pred_i = torch.sum(torch.mul(u_pos,i_pos), dim=-1) 
        pred_j = torch.sum(torch.mul(u_neg,j_neg), dim=-1)  
        return pred_i, pred_j


    #这些函数涉及复杂的采样策略，部分是为了对抗生成网络（GAN）或 Top-K 蒸馏服务的

    #逻辑：给定一批用户 (batIds)，从图中随机采样 sample_num 个正样本邻居，或从 g_neg（如果有）采样负样本。
    def sampleTrainBatch_dgl(self, batIds, pos_id=None, g=None, g_neg=None, sample_num=None, sample_num_neg=None):

        sub_g = dgl.sampling.sample_neighbors(g.cpu(), {'user':batIds}, sample_num, edge_dir='out', replace=True)
        row, col = sub_g.edges()
        row = row.reshape(len(batIds), sample_num)
        col = col.reshape(len(batIds), sample_num)

        if g_neg==None:
            return row, col
        else: 
            sub_g_neg = dgl.sampling.sample_neighbors(g_neg, {'user':batIds}, sample_num_neg, edge_dir='out', replace=True)
            row_neg, col_neg = sub_g_neg.edges()
            row_neg = row_neg.reshape(len(batIds), sample_num_neg)
            col_neg = col_neg.reshape(len(batIds), sample_num_neg)
            return row, col, col_neg 

    def weights_init(self, m):
        if isinstance(m, nn.Linear):
            nn.init.kaiming_normal_(m.weight)
            m.bias.data.fill_(0)

    def weighted_sum(self, anchor, nei, co):  

        ac = torch.multiply(anchor, co).sum(-1).sum(-1)  
        nc = torch.multiply(nei, co).sum(-1).sum(-1)  

        an = (anchor.permute(1, 0, 2)[0])
        ne = (nei.permute(1, 0, 2)[0])

        an_w = an*(ac.unsqueeze(-1).repeat(1, args.embed_size))
        ne_w = ne*(nc.unsqueeze(-1).repeat(1, args.embed_size))                                     
  
        res = (args.anchor_rate*an_w + (1-args.anchor_rate)*ne_w).reshape(-1, args.sample_num_ii, args.embed_size).sum(1)

        return res

    #功能：基于相似度矩阵，挖掘“困难负样本” (Hard Negatives) 或 “伪标签” (Pseudo Labels)。
    def sample_topk(self, u_sim, users, emb_type=None):
        topk_p, topk_id = torch.topk(u_sim, args.ad_topk*10, dim=-1)  
        topk_data = topk_p.reshape(-1).cpu()
        topk_col = topk_id.reshape(-1).cpu().int()
        topk_row = torch.tensor(np.array(users)).unsqueeze(1).repeat(1, args.ad_topk*args.ad_topk_multi_num).reshape(-1).int()  #
        topk_csr = csr_matrix((topk_data.detach().numpy(), (topk_row.detach().numpy(), topk_col.detach().numpy())), shape=(self.n_users, self.n_items))
        topk_g = dgl.heterograph({('user','ui','item'):topk_csr.nonzero()})
        _, topk_id = self.sampleTrainBatch_dgl(users, g=topk_g, sample_num=args.ad_topk, pos_id=None, g_neg=None, sample_num_neg=None)
        self.gene_fake[emb_type] = topk_id

        topk_id_u = torch.arange(len(users)).unsqueeze(1).repeat(1, args.ad_topk)
        topk_p = u_sim[topk_id_u, topk_id]
        return topk_p, topk_id

    def ssl_loss_calculation(self, ssl_image_logit, ssl_text_logit, ssl_common_logit):
        ssl_label_1_s2 = torch.ones(1, self.n_items).cuda()
        ssl_label_0_s2 = torch.zeros(1, self.n_items).cuda()
        ssl_label_s2 = torch.cat((ssl_label_1_s2, ssl_label_0_s2), 1)
        ssl_image_s2 = self.bce(ssl_image_logit, ssl_label_s2)
        ssl_text_s2 = self.bce(ssl_text_logit, ssl_label_s2)
        ssl_loss_s2 = ssl_image_s2 + ssl_text_s2

        ssl_label_1_c2 = torch.ones(1, self.n_items*2).cuda()
        ssl_label_0_c2 = torch.zeros(1, self.n_items*2).cuda()
        ssl_label_c2 = torch.cat((ssl_label_1_c2, ssl_label_0_c2), 1)
        ssl_result_c2 = self.bce(ssl_common_logit, ssl_label_c2)  
        ssl_loss_c2 = ssl_result_c2

        ssl_loss2 = args.ssl_s_rate*ssl_loss_s2 + args.ssl_c_rate*ssl_loss_c2 
        return ssl_loss2


    def sim(self, z1, z2):
        z1 = F.normalize(z1)  
        z2 = F.normalize(z2)
        # z1 = z1/((z1**2).sum(-1) + 1e-8)
        # z2 = z2/((z2**2).sum(-1) + 1e-8)
        return torch.mm(z1, z2.t())
    

    #标准的 InfoNCE Loss (对比学习核心损失)。
    def batched_contrastive_loss(self, z1, z2, batch_size=1024):

        device = z1.device
        num_nodes = z1.size(0)
        num_batches = (num_nodes - 1) // batch_size + 1
        f = lambda x: torch.exp(x / args.tau)   #       

        indices = torch.arange(0, num_nodes).to(device)
        losses = []

        for i in range(num_batches):
            tmp_i = indices[i * batch_size:(i + 1) * batch_size]

            tmp_refl_sim_list = []
            tmp_between_sim_list = []
            for j in range(num_batches):
                tmp_j = indices[j * batch_size:(j + 1) * batch_size]
                tmp_refl_sim = f(self.sim(z1[tmp_i], z1[tmp_j]))  
                tmp_between_sim = f(self.sim(z1[tmp_i], z2[tmp_j]))  

                tmp_refl_sim_list.append(tmp_refl_sim)
                tmp_between_sim_list.append(tmp_between_sim)

            refl_sim = torch.cat(tmp_refl_sim_list, dim=-1)
            between_sim = torch.cat(tmp_between_sim_list, dim=-1)

            losses.append(-torch.log(between_sim[:, i * batch_size:(i + 1) * batch_size].diag()/ (refl_sim.sum(1) + between_sim.sum(1) - refl_sim[:, i * batch_size:(i + 1) * batch_size].diag())+1e-8))

            del refl_sim, between_sim, tmp_refl_sim_list, tmp_between_sim_list
                   
        loss_vec = torch.cat(losses)
        return loss_vec.mean()

    def feat_reg_loss_calculation(self, g_item_image, g_item_text, g_user_image, g_user_text):
        feat_reg = 1./2*(g_item_image**2).sum() + 1./2*(g_item_text**2).sum() \
            + 1./2*(g_user_image**2).sum() + 1./2*(g_user_text**2).sum()        
        feat_reg = feat_reg / self.n_items
        feat_emb_loss = args.feat_reg_decay * feat_reg
        return feat_emb_loss

    def fake_gene_loss_calculation(self, u_emb, i_emb, emb_type=None):
        if self.gene_u!=None:
            gene_real_loss = (-F.logsigmoid((u_emb[self.gene_u]*i_emb[self.gene_real]).sum(-1)+1e-8)).mean()
            gene_fake_loss = (1-(-F.logsigmoid((u_emb[self.gene_u]*i_emb[self.gene_fake[emb_type]]).sum(-1)+1e-8))).mean()

            gene_loss = gene_real_loss + gene_fake_loss
        else:
            gene_loss = 0

        return gene_loss

    def reward_loss_calculation(self, users, re_u, re_i, topk_id, topk_p):
        self.gene_u = torch.tensor(np.array(users)).unsqueeze(1).repeat(1, args.ad_topk)
        reward_u = re_u[self.gene_u]
        reward_i = re_i[topk_id]
        reward_value = (reward_u*reward_i).sum(-1)

        reward_loss = -(((topk_p*reward_value).sum(-1)).mean()+1e-8).log()
        
        return reward_loss

    def u_sim_calculation(self, users, user_final, item_final):
        topk_u = user_final[users]
        u_ui = torch.tensor(self.ui_graph_raw[users].todense()).cuda()

        num_batches = (self.n_items - 1) // args.batch_size + 1
        indices = torch.arange(0, self.n_items).cuda()
        u_sim_list = []

        for i_b in range(num_batches):
            index = indices[i_b * args.batch_size:(i_b + 1) * args.batch_size]
            sim = torch.mm(topk_u, item_final[index].T)
            sim_gt = torch.multiply(sim, (1-u_ui[:, index]))
            u_sim_list.append(sim_gt)
                
        u_sim = F.normalize(torch.cat(u_sim_list, dim=-1), p=2, dim=1)   
        return u_sim

    def loss_function(self, pred, drop_rate):
        # loss = F.cross_entropy(y, t, reduce = False)
        # loss_mul = loss * t
        ind_sorted = np.argsort(pred.cpu().data).cuda()
        loss_sorted = pred[ind_sorted]

        remember_rate = 1 - drop_rate
        num_remember = int(remember_rate * len(loss_sorted))

        ind_update = ind_sorted[:num_remember]

        loss_update = pred[ind_update]

        return loss_update.mean()

    #功能：均方误差（MSE）损失，但加了预处理。
    def mse_criterion(self, x, y, mask_nodes_dict=None, alpha=3):

        # res_list = []
        # for id, value in enumerate(x_dict):
        #     # x, y  = x_dict[value][mask_nodes_dict[value]], y_dict[value][mask_nodes_dict[value]]
        # x, y  = x_dict[value], y_dict[value]
        
        #对 x (学生特征) 和 y (教师特征) 做 L2 归一化。
        x = F.normalize(x, p=2, dim=-1)
        y = F.normalize(y, p=2, dim=-1)

        # loss =  - (x * y).sum(dim=-1)
        # loss = (x_h - y_h).norm(dim=1).pow(alpha)
        tmp_loss = (1 - (x * y).sum(dim=-1)).pow_(alpha)
        tmp_loss = tmp_loss.mean()

        loss = F.mse_loss(x, y)
        # res_list.append(tmp_loss)
        # loss = sum(res_list)/len(res_list)
        return loss
 
    #功能：Cosine Error (余弦误差) 损失。
    def sce_criterion(self, x, y, alpha=1, tip_rate=0):
        x = F.normalize(x, p=2, dim=-1)
        y = F.normalize(y, p=2, dim=-1)

        loss = (1-(x*y).sum(dim=-1)).pow_(alpha) #1 - CosineSimilarity 就是余弦距离。


        if tip_rate!=0:
            loss = self.loss_function(loss, tip_rate)   
            return loss

        loss = loss.mean() 

        # loss = loss.mean()

        return loss


    #功能：模型的推理入口。
    def test(self, users_to_test, is_val, is_teacher=True):
        self.teacher_model.eval()
        with torch.no_grad():
            if is_teacher:
                u_embed, i_embed, *rest = self.teacher_model(self.ui_graph, self.iu_graph, self.prompt_module) #如果是教师：self.teacher_model(...)，需要输入图和 Prompt。
            else:
                if args.student_model_type=='lightgcn':
                    u_embed, i_embed = self.student_model(self.adj) #如果是学生：self.student_model(self.adj)，只需要输入邻接矩阵。
                elif args.student_model_type=='gcn': 
                    u_embed, i_embed = self.student_model(self.u_final_embed, self.i_final_embed, self.ui_graph, self.iu_graph)
                elif args.student_model_type=='mlp': 
                    u_embed, i_embed = self.student_model(self.u_final_embed, self.i_final_embed)  

        result = test_torch(u_embed, i_embed, users_to_test, is_val) #计算指标：调用 test_torch (来自 utility/batch_test.py) 计算 Recall, NDCG 等。
        return result


    def train(self):
        now_time = datetime.now()
        run_time = datetime.strftime(now_time,'%Y_%m_%d__%H_%M_%S')

        # ================= [新增 1：初始化 TensorBoard] =================
        # 这里的 log_dir 决定了日志存哪里。我们用 dataset 和 point 区分
        run_name = f"{args.dataset}_{str(args.point) if args.point else 'default'}"
        tb_writer = SummaryWriter(log_dir=f'./runs/{run_name}')
        # =============================================================

        training_time_list = []
        loss_loger, pre_loger, rec_loger, ndcg_loger, hit_loger = [], [], [], [], []

        stopping_step = 0
        should_stop = False
        cur_best_pre_0 = 0. 

        if args.if_train_teacher: 
            # ----train_teacher-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            print("########begin:Teacher###################################")
            print(args.point)
            print("########################################################")
            n_batch = data_generator.n_train // args.batch_size + 1
            s_best_recall = 0
            for epoch in range(args.epoch):
                t1 = time()
                loss, mf_loss, emb_loss, reg_loss = 0., 0., 0., 0.
                contrastive_loss = 0. 
                # n_batch = data_generator.n_train // args.batch_size + 1
                f_time, b_time, loss_time, opt_time, clip_time, emb_time = 0., 0., 0., 0., 0., 0.
                sample_time = 0.
                build_item_graph = True

                self.gene_u, self.gene_real, self.gene_fake = None, None, {}
                self.topk_p_dict, self.topk_id_dict = {}, {}

                for idx in tqdm(range(n_batch)):
                    self.teacher_model.train()

                    # 采样 Batch 数据 (Users, Pos Items, Neg Items)
                    sample_t1 = time()
                    users, pos_items, neg_items = data_generator.sample()
                    sample_time += time() - sample_t1       

                    # [核心代码] 教师模型前向传播
                    # 对应 PromptMM.png 架构图的整体流程：
                    # 输入：图结构 + Prompt 模块
                    # 输出：
                    # 1. t_u_id_embed/t_i_id_embed: 融合了 Prompt 的 ID Embedding
                    # 2. t_i_image_embed/t_i_text_embed: 经过 Prompt 增强的多模态特征
                    # 3. prompt_user/prompt_item: 学习到的 Prompt 向量
                    
                    # 【新增】末尾多接收一个 prompt_aux_loss
                    t_u_id_embed, t_i_id_embed, t_i_image_embed, t_i_text_embed, t_u_image_embed, t_u_text_embed \
                                    , G_user_emb, G_item_emb, prompt_user, prompt_item, prompt_aux_loss \
                            = self.teacher_model(self.ui_graph, self.iu_graph, self.prompt_module)

                    # [损失函数 1] 推荐任务的主损失 (BPR Loss)
                    # 让 User 和 Pos Item 的距离比 User 和 Neg Item 近
                    t_u_id_embed_pbr = t_u_id_embed[users]
                    t_i_id_embed_pbr_pos = t_i_id_embed[pos_items]
                    t_i_id_embed_pbr_neg = t_i_id_embed[neg_items]
                    t_mf_loss, t_emb_loss = self.bpr_loss(t_u_id_embed_pbr, t_i_id_embed_pbr_pos, t_i_id_embed_pbr_neg)
        
                    # [损失函数 2] Prompt 的正则化损失
                    # 对应论文中对 Prompt 的约束，防止其过拟合或漂移太远
                    # prompt
                    u_id_embed_pbr_prompt = prompt_user[users]
                    i_id_embed_pbr_pos_prompt = prompt_item[pos_items]
                    i_id_embed_pbr_neg_prompt = prompt_item[neg_items]
                    mf_loss_prompt, emb_loss_prompt = self.bpr_loss(u_id_embed_pbr_prompt, i_id_embed_pbr_pos_prompt, i_id_embed_pbr_neg_prompt)
        
                    # [损失函数 3] 多模态特征的辅助损失
                    # 确保学习到的多模态表示具有区分度
                    t_image_u_g_embeddings = t_u_image_embed[users]
                    t_image_pos_i_g_embeddings = t_i_image_embed[pos_items]
                    t_image_neg_i_g_embeddings = t_i_image_embed[neg_items]
                    t_image_batch_mf_loss, G_image_batch_emb_loss = self.bpr_loss(t_image_u_g_embeddings, t_image_pos_i_g_embeddings, t_image_neg_i_g_embeddings)

                    t_text_u_g_embeddings = t_u_text_embed[users]
                    t_text_pos_i_g_embeddings = t_i_text_embed[pos_items]
                    t_text_neg_i_g_embeddings = t_i_text_embed[neg_items]
                    t_text_batch_mf_loss, G_text_batch_emb_loss = self.bpr_loss(t_text_u_g_embeddings, t_text_pos_i_g_embeddings, t_text_neg_i_g_embeddings)


                    feat_emb_loss = self.feat_reg_loss_calculation(t_i_image_embed, t_i_text_embed, t_u_image_embed, t_u_text_embed)

                    # 总损失 = 推荐损失 + Prompt 损失 + 多模态特征损失
                    #(作者曾经想加入 Prompt 的 Embedding 正则化损失)
                    # t_batch_loss = t_mf_loss + t_emb_loss + feat_emb_loss + args.t_prompt_rate1*mf_loss_prompt #+ args.t_prompt_rate2*emb_loss_prompt + args.t_feat_mf_rate*t_image_batch_mf_loss + args.t_feat_mf_rate*t_text_batch_mf_loss
                    # 【新增】设置 MoE 负载均衡 Loss 的权重
                    moe_loss_weight = 0.05  # 你后续也可以把这个写进 args.py 里方便调参
                    
                    # 总损失 = 推荐损失 + Prompt 损失 + 多模态特征损失 + MoE负载均衡损失
                    t_batch_loss = t_mf_loss + t_emb_loss + feat_emb_loss + args.t_prompt_rate1*mf_loss_prompt + args.t_feat_mf_rate*t_image_batch_mf_loss + args.t_feat_mf_rate*t_text_batch_mf_loss + moe_loss_weight * prompt_aux_loss
                    #这是一个消融实验（Ablation Study），用于测试 Prompt 监督信号 的重要性
                    # t_batch_loss = t_mf_loss + t_emb_loss + feat_emb_loss + args.t_feat_mf_rate*t_image_batch_mf_loss + args.t_feat_mf_rate*t_text_batch_mf_loss

                    # line_cl_loss.append(batch_contrastive_loss.detach().data)
                    # 反向传播与优化                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                #+ ssl_loss2 #+ batch_contrastive_loss
                    self.opt_T.zero_grad()  
                    t_batch_loss.backward(retain_graph=False)
                    self.opt_T.step()

                    loss += float(t_batch_loss)
                    mf_loss += float(t_emb_loss)
                    # emb_loss += float(t_reg_loss)
                    # reg_loss += float(G_batch_reg_loss)
                    teacher_feat_dict = { 'item_image':t_i_image_embed.detach(),'item_text':t_i_text_embed.detach(),'user_image':t_u_image_embed.detach(),'user_text':t_u_text_embed.detach() }

        
                # del ua_embeddings, ia_embeddings, G_ua_embeddings, G_ia_embeddings, G_u_g_embeddings, G_neg_i_g_embeddings, G_pos_i_g_embeddings
                    del t_u_id_embed, t_i_id_embed, t_i_image_embed, t_i_text_embed, t_u_image_embed, t_u_text_embed \
                                        , G_user_emb, G_item_emb \
                                        , t_u_id_embed_pbr, t_i_id_embed_pbr_pos, t_i_id_embed_pbr_neg

                if math.isnan(loss) == True:
                    self.logger.logging('ERROR: loss is nan.')
                    sys.exit()

                if (epoch + 1) % args.verbose != 0:
                    perf_str = 'Epoch %d [%.1fs]: train==[%.5f=%.5f + %.5f + %.5f  + %.5f]' % (
                        epoch, time() - t1, loss, mf_loss, emb_loss, reg_loss, contrastive_loss)
                    training_time_list.append(time() - t1)
                    self.logger.logging(perf_str)

                # ================= [新增 2：记录 Teacher 数据] =================
                # 记录 Loss (损失)
                tb_writer.add_scalar('Teacher/Total_Loss', loss, epoch)
                tb_writer.add_scalar('Teacher/MF_Loss', mf_loss, epoch)
            
                t2 = time()
                users_to_test = list(data_generator.test_set.keys())
                users_to_val = list(data_generator.val_set.keys())
                s_ret = self.test(users_to_test, is_val=False)  #^-^
                training_time_list.append(t2 - t1)

                t3 = time()

                loss_loger.append(loss)
                rec_loger.append(s_ret['recall'])
                pre_loger.append(s_ret['precision'])
                ndcg_loger.append(s_ret['ndcg'])
                hit_loger.append(s_ret['hit_ratio'])


                tags = ["recall", "precision", "ndcg"]

                # 记录 Metrics (指标) - 注意：这里用的是 s_ret 变量
                tb_writer.add_scalar('Teacher/Recall@20', s_ret['recall'][1], epoch)
                tb_writer.add_scalar('Teacher/NDCG@20', s_ret['ndcg'][1], epoch)
                # ============================================================


                if args.verbose > 0:
                    perf_str = 'Teacher: Epoch %d [%.1fs + %.1fs]: train==[%.5f=%.5f + %.5f + %.5f], recall=[%.5f, %.5f, %.5f, %.5f], ' \
                            'precision=[%.5f, %.5f, %.5f, %.5f], hit=[%.5f, %.5f, %.5f, %.5f], ndcg=[%.5f, %.5f, %.5f, %.5f]' % \
                            (epoch, t2 - t1, t3 - t2, loss, mf_loss, emb_loss, reg_loss, s_ret['recall'][0], s_ret['recall'][1], s_ret['recall'][2],
                                s_ret['recall'][-1],
                                s_ret['precision'][0], s_ret['precision'][1], s_ret['precision'][2], s_ret['precision'][-1], s_ret['hit_ratio'][0], s_ret['hit_ratio'][1], s_ret['hit_ratio'][2], s_ret['hit_ratio'][-1],
                                s_ret['ndcg'][0], s_ret['ndcg'][1], s_ret['ndcg'][2], s_ret['ndcg'][-1])
                    self.logger.logging(perf_str)

                if s_ret['recall'][1] > s_best_recall:
                    s_best_recall = s_ret['recall'][1]
                    test_ret = self.test(users_to_test, is_val=False)
                    self.logger.logging("Test_Recall@%d: %.5f,  precision=[%.5f], ndcg=[%.5f]" % (eval(args.Ks)[1], test_ret['recall'][1], test_ret['precision'][1], test_ret['ndcg'][1]))
                    stopping_step = 0
                    
                    save_dir = './weights/' + args.dataset
                    if not os.path.exists(save_dir):
                        os.makedirs(save_dir)
                    torch.save(self.teacher_model.state_dict(), save_dir + '/teacher_model_great.pt')
                
                elif stopping_step < args.early_stopping_patience:
                    stopping_step += 1
                    self.logger.logging('#####Early stopping steps: %d #####' % stopping_step)
                else:
                    self.logger.logging('#####Early stop! #####')
                    break

            self.logger.logging(str(test_ret))

            # ================= [修改 1：插入教师结果保存代码] =================
            # 1. 打包教师的训练数据 (根据代码开头的变量名)
            teacher_results = {
                'loss': loss_loger,
                'recall': rec_loger,
                'precision': pre_loger,
                'ndcg': ndcg_loger,
                'hit': hit_loger,
                'time': training_time_list
            }

            # 2. 准备路径
            exp_dir = './history/' + args.dataset
            if not os.path.exists(exp_dir):
                os.makedirs(exp_dir)

            # 3. 生成带前缀的文件名 (例如: teacher_run1.pkl)
            base_name = str(args.point) if args.point else "result.pkl"
            if not base_name.endswith('.pkl'):
                base_name += '.pkl'
            
            teacher_filename = "teacher_" + base_name  # <--- 关键：加上 teacher_ 前缀
            
            # 4. 保存
            save_path = os.path.join(exp_dir, teacher_filename)
            self.logger.logging(f"保存教师实验结果到: {save_path}")
            pickle.dump(teacher_results, open(save_path, 'wb'))
            # ===============================================================

            print("######end:Teacher#####################################")
            print(args.point)
            print("######################################################")
        # ----train_teacher-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



        # # ----train_student-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        print("########begin:Student###################################")
        print(args.point)
        print("#######################################################")
        n_batch = data_generator.n_train // args.batch_size + 1
        best_recall = 0

        # [阶段转换] 教师模型训练完毕，冻结它！
        # 学生模型（Student）只使用 ID 信息，是个轻量级模型 (LightGCN/MLP)
        # self.teacher_feat_dict = torch.load('/home/weiw/Code/MM/KDMM/Model/' + args.dataset + '/teacher_feat_dict.pt')
        #self.teacher_model.load_state_dict(torch.load('/home/weiw/Code/MM/KDMM/Model/' + args.dataset + '/teacher_model_great.pt'))
        load_path = './weights/' + args.dataset + '/teacher_model_great.pt'
        self.teacher_model.load_state_dict(torch.load(load_path))
        self.teacher_model.eval() # 冻结教师

        # if args.if_train_teacher and epoch==0:
        # with torch.no_grad():
        #     pre_u_final_embed, pre_i_final_embed, _, _, _, _ \
        #     , _, _ \
        #     = self.teacher_model(self.ui_graph, self.iu_graph)
        with torch.no_grad():
            self.u_final_embed, self.i_final_embed, image_item_embeds, text_item_embeds, image_user_embeds, text_user_embeds \
            , G_user_emb, G_item_emb, prompt_user, prompt_item \
            = self.teacher_model(self.ui_graph, self.iu_graph, self.prompt_module)

        
        # 1. 学生模型的构造（Construction）
        # 学生模型通常是纯 ID 的 LightGCN 或 MLP，不包含繁重的图像/文本处理网络
        if args.student_model_type=='lightgcn':
            self.student_model = Student_LightGCN(self.n_users, self.n_items, self.student_emb_dim, self.student_n_layers, self.mess_dropout, self.image_feats, self.text_feats)   
            self.student_model.init_user_item_embed(self.u_final_embed, self.i_final_embed)
        elif args.student_model_type=='gcn': 
            self.student_model = Student_GCN(self.n_users, self.n_items, self.student_emb_dim, self.student_n_layers, self.mess_dropout, self.image_feats, self.text_feats)   
        elif args.student_model_type=='mlp': 
            self.student_model = Student_MLP()   
            self.student_model.init_user_item_embed(self.u_final_embed, self.i_final_embed)


        self.student_model = self.student_model.cuda()
        self.opt_S = optim.AdamW([{'params':self.student_model.parameters()}, # 学生优化器
                                  {'params':self.prompt_module.parameters()}
                                  ], lr=self.student_lr) 


        # ================= [修改 3：把变量初始化移到循环外] =================
        # 定义空列表，用于记录整个训练过程
        student_batch_loss_List = []
        batch_mf_loss_List = []
        kd_loss_List = []
        recall20_List = []
        recall50_List = []
        ndcg20_List = []
        ndcg50_List = []
        # ============================================================== 

        # # 👇【第四步-第1处：在此处初始化 DTS 调度器】👇
        # dynamic_tau_scheduler = RecSysDynamicTauScheduler(
        #     initial_tau=args.student_tau, 
        #     min_tau=1.0, 
        #     max_epoch=args.epoch
        # )
        # last_epoch_kd_loss = 1.0 
        # # 👆-------------------------------------------------------👆

        # --- 学生训练循环 ---
        for epoch in range(args.epoch):
            t1 = time()

            # # 👇【第四步-第2处：获取本轮的动态温度】👇
            # current_dynamic_tau = dynamic_tau_scheduler.step(epoch, last_epoch_kd_loss)
            # self.logger.logging(f"Epoch {epoch} | 当前动态温度 (Dynamic Tau): {current_dynamic_tau:.4f}")
            # tb_writer.add_scalar('Student/Dynamic_Tau', current_dynamic_tau, epoch)
            # total_kd_loss_this_epoch = 0.0
            # # 👆-------------------------------------------------------👆

            loss, mf_loss, emb_loss, reg_loss = 0., 0., 0., 0.
            contrastive_loss = 0.

            n_batch = data_generator.n_train // args.batch_size + 1
            f_time, b_time, loss_time, opt_time, clip_time, emb_time = 0., 0., 0., 0., 0., 0.

            sample_time = 0.
            build_item_graph = True

            self.gene_u, self.gene_real, self.gene_fake = None, None, {}
            self.topk_p_dict, self.topk_id_dict = {}, {}

            for idx in tqdm(range(n_batch)):
                self.teacher_model.train()
                sample_t1 = time()

                # 采样
                users, pos_items, neg_items = data_generator.sample()  # [1024], [1024], [1024] 
                sample_time += time() - sample_t1      

                # [步骤 1] 学生模型前向传播 (Student Forward)
                # 学生很单纯，只看图结构 (adj)，不看图片和文本
                # 对应 Decouple 图的下方 Student 部分
                if args.student_model_type=='lightgcn':
                    u_embed, i_embed = self.student_model(self.adj)
                elif args.student_model_type=='gcn': 
                    u_embed, i_embed = self.student_model(self.u_final_embed, self.i_final_embed, self.ui_graph, self.iu_graph)
                elif args.student_model_type=='mlp': 
                    u_embed, i_embed = self.student_model(self.u_final_embed, self.i_final_embed)
                
                #学生模型前向传播
                u_embeddings = u_embed[users]
                pos_i_embeddings = i_embed[pos_items]
                neg_i_embeddings = i_embed[neg_items]

                # [步骤 2] 计算学生的基础推荐损失
                # 学生自己也要努力学习如何推荐 (Self-Supervised)，计算学生的基础 BPR Loss
                
                # --- [修改说明] ---
                # 原始代码中 MLP 的分支计算方式与其他模型不同，导致了 Loss 变成极大的负数（优化方向反了）。
                # 下面注释掉了原来的逻辑，并统一使用 bpr_loss_for_KD 来计算。
                # -----------------

                # === [OLD CODE / 原始代码注释备份] START ==========================================
                # batch_mf_loss, batch_emb_loss = self.bpr_loss(u_embeddings, pos_i_embeddings, neg_i_embeddings)
                # # print(f'batch_mf_loss1: {batch_mf_loss}') 
                #
                # if args.student_model_type=='mlp':
                #     # 错误原因：这里可能直接返回了 LogSigmoid (负值) 且没有取负号，导致 Loss 越来越小（负无穷）
                #     batch_mf_loss = self.student_model.pairPredictwEmbeds(u_embed, i_embed, users, pos_items, neg_items).sum()
                #     student_mf_loss = self.student_model.pairPredictwEmbeds(u_embed, i_embed, users, pos_items, neg_items)
                # else:
                #     student_mf_loss, student_batch_emb_loss, batch_reg_loss = self.bpr_loss_for_KD(u_embeddings, pos_i_embeddings, neg_i_embeddings) 
                #     # print(f'batch_mf_loss2: {batch_mf_loss}') 
                # === [OLD CODE / 原始代码注释备份] END ============================================

                # === [NEW CODE / 修改后的代码] START ==============================================
                # 修正：无论是什么模型 (MLP/LightGCN)，统一使用 bpr_loss_for_KD
                # 1. student_mf_loss: 向量形式 [batch_size]，用于后续的 KD 蒸馏 (BPR Loss = -LogSigmoid)
                # 2. batch_emb_loss: 标量，L2 正则化损失
                student_mf_loss, batch_emb_loss, batch_reg_loss = self.bpr_loss_for_KD(u_embeddings, pos_i_embeddings, neg_i_embeddings)
                
                # 将向量 Loss 求平均，得到基础推荐任务的标量 Loss (用于反向传播)
                batch_mf_loss = torch.mean(student_mf_loss)
                # ================================================================================== 

                # -----------------------------KD-----------------------------------
                # 获取教师的实时输出 (作为 Soft Targets)
                with torch.no_grad(): # 这里的计算不需要梯度

                    # 教师提供了非常丰富的信息：
                    # u_final_embed: 教师的高级 User Embedding
                    # image_item_embeds: 教师提取的 Image Embedding
                    # text_item_embeds: 教师提取的 Text Embedding
                    self.u_final_embed, self.i_final_embed, image_item_embeds, text_item_embeds, image_user_embeds, text_user_embeds \
                    , G_user_emb, G_item_emb, prompt_user, prompt_item \
                    = self.teacher_model(self.ui_graph, self.iu_graph, self.prompt_module)


                # if args.student_model_type=='mlp':
                #     student_mf_loss = self.student_model.pairPredictwEmbeds(u_embed, i_embed, users, pos_items, neg_items)
                # else:
                #     student_mf_loss, student_batch_emb_loss, batch_reg_loss = self.bpr_loss_for_KD(u_embeddings, pos_i_embeddings, neg_i_embeddings) 

                # --------------------------------------list-wise ranking-------------------------------------------------------------------------------------- 
                # num_nodes = u_final_embed.size(0)             
                # batch_size = 1024 
                # num_batches = (num_nodes - 1) // batch_size + 1
                # # f = lambda x: torch.exp(x / args.tau)   #       
                # indices = torch.arange(0, num_nodes)
                # list_wise_losses = []
                # for i in range(num_batches):
                #     tmp_index = indices[i * batch_size:(i + 1) * batch_size]
                #     ### constructure graph
                #     sub_x_index, sub_y_index = self.ui_graph_raw[tmp_index].nonzero()[0], self.ui_graph_raw[tmp_index].nonzero()[1]
                #     sub_dgl_g = dgl.graph((sub_x_index, sub_y_index)).to('cuda:0')
                #     ### neg sample 
                #     neg_row, neg_col = dgl.sampling.global_uniform_negative_sampling(sub_dgl_g, tmp_index.shape[0]*args.neg_sample_num)
                #     neg_row, neg_col = neg_row.reshape((tmp_index.shape[0], args.neg_sample_num)), neg_col.reshape((tmp_index.shape[0], args.neg_sample_num))  # [1024, 10] [1024, 10]
                #     # torch.tensor(users), torch.tensor(pos_items), torch.tensor(neg_items)
                #     item_index = torch.cat((torch.tensor(pos_items).cuda().unsqueeze(1), neg_col), dim=1)
                #     # u_embed, i_embed 
                #     list_wise_score = torch.mul(u_embed[users].unsqueeze(1), i_embed[item_index]).sum(-1).softmax(-1)  
                #     # list_wise_score = torch.mul(u_final_embed[users].unsqueeze(1), i_final_embed[item_index]).sum(-1).softmax(-1)  
                #     tmp_list_wise_loss = -list_wise_score[:,0].log().sum()
                #     list_wise_losses.append(tmp_list_wise_loss)
                #     del sub_x_index, sub_y_index, sub_dgl_g
                # list_wise_losses = sum(list_wise_losses)


                ### constructure graph
                sub_x_index, sub_y_index = self.ui_graph_raw[users].nonzero()[0], self.ui_graph_raw[users].nonzero()[1]
                sub_dgl_g = dgl.graph((sub_x_index, sub_y_index)).to('cuda:0')
                ### neg sample 
                neg_row, neg_col = dgl.sampling.global_uniform_negative_sampling(sub_dgl_g, len(users)*args.neg_sample_num, replace=True)
                neg_row, neg_col = neg_row.reshape((len(users), args.neg_sample_num)), neg_col.reshape((len(users), args.neg_sample_num))  # [1024, 10] [1024, 10]
                # torch.tensor(users), torch.tensor(pos_items), torch.tensor(neg_items)
                item_index = torch.cat((torch.tensor(pos_items).cuda().unsqueeze(1), neg_col), dim=1)

                # C. 解耦蒸馏 (Decoupled Knowledge Distillation - DKD)
                # 对应图中：List-wise Ranking 拆分为 Target (正样本) 和 Non-Target (负样本) 两部分。
                # 这通过 dkd_loss 函数实现。

                # # 1. 计算学生的 List-wise 分数 (Softmax)
                # list_wise_score_s = torch.mul(u_embed[users].unsqueeze(1), i_embed[item_index]).sum(-1).softmax(-1) 
                # # list_wise_loss_s = -(list_wise_score_s[:,0]+1e-8).log() 
                # list_wise_loss_s = -(list_wise_score_s+1e-8).log() 
                # target = torch.zeros(list_wise_loss_s.shape[0]).long().cuda() 
                # # 2. 计算教师的 List-wise 分数 (Softmax)
                # list_wise_score_t = torch.mul(self.u_final_embed[users].unsqueeze(1),self.i_final_embed[item_index]).sum(-1).softmax(-1) 
                # # list_wise_loss_t = -(list_wise_score_t[:,0]+1e-8).log()
                # list_wise_loss_t = -(list_wise_score_t+1e-8).log()
                # list_wise_score_t_image = torch.mul(image_user_embeds[users].unsqueeze(1), image_item_embeds[item_index]).sum(-1).softmax(-1) 
                # # list_wise_loss_t_image = -(list_wise_score_t_image[:,0]+1e-8).log()
                # list_wise_loss_t_image = -(list_wise_score_t_image+1e-8).log()
                # list_wise_score_t_text = torch.mul(text_user_embeds[users].unsqueeze(1), text_item_embeds[item_index]).sum(-1).softmax(-1) 
                # # list_wise_loss_t_text = -(list_wise_score_t_text[:,0]+1e-8).log()
                # list_wise_loss_t_text = -(list_wise_score_t_text+1e-8).log()


                # list_wise_losses.append(tmp_list_wise_loss)

                # === [修改代码：提取纯净的 Logits (不带 Softmax)] ===
                # 1. 学生的 List-wise 原始打分 (Logits)
                list_wise_logits_s = torch.mul(u_embed[users].unsqueeze(1), i_embed[item_index]).sum(-1) 
                list_wise_loss_s = -(list_wise_logits_s.softmax(-1) + 1e-8).log() 
                target = torch.zeros(list_wise_loss_s.shape[0]).long().cuda() 
                
                # 2. 老师的 List-wise 原始打分 (Logits)
                list_wise_logits_t = torch.mul(self.u_final_embed[users].unsqueeze(1), self.i_final_embed[item_index]).sum(-1)
                list_wise_loss_t = -(list_wise_logits_t.softmax(-1) + 1e-8).log()
                
                list_wise_logits_t_image = torch.mul(image_user_embeds[users].unsqueeze(1), image_item_embeds[item_index]).sum(-1)
                list_wise_loss_t_image = -(list_wise_logits_t_image.softmax(-1) + 1e-8).log()
                
                list_wise_logits_t_text = torch.mul(text_user_embeds[users].unsqueeze(1), text_item_embeds[item_index]).sum(-1)
                list_wise_loss_t_text = -(list_wise_logits_t_text.softmax(-1) + 1e-8).log()
                # =======================================================

                del sub_x_index, sub_y_index, sub_dgl_g
                # --------------------------------------list-wise ranking-------------------------------------------------------------------------------------- 
 
                u_g_embed_mf = self.u_final_embed[users]
                pos_i_g_embed_mf = self.i_final_embed[pos_items]
                neg_i_g_embed_mf = self.i_final_embed[neg_items]

                # ================= [画图核心] 蒸馏损失计算 =================
                # 这里详细解释 Decouple.png 中的每一条连线是怎么来的

                # [连线 A: Topology Distillation / 拓扑蒸馏]
                # 目的：让学生学习教师对于 User-Item 交互的理解（分布对齐）
                # 代码逻辑：计算学生的 MF Loss 分布 和 教师的 MF Loss 分布的 KL 散度
                # teacher_mf_loss, teacher_batch_emb_loss, G_batch_reg_loss = self.bpr_loss_for_KD(u_g_embed_mf, pos_i_g_embed_mf, neg_i_g_embed_mf)
       
                image_u_embed = image_user_embeds[users]
                image_pos_i_embed = image_item_embeds[pos_items]
                image_neg_i_embed = image_item_embeds[neg_items]
                image_teacher_mf_loss, G_image_batch_emb_loss, G_image_batch_reg_loss = self.bpr_loss_for_KD(image_u_embed, image_pos_i_embed, image_neg_i_embed)

                text_u_embed = text_user_embeds[users]
                text_pos_i_embed = text_item_embeds[pos_items]
                text_neg_i_embed = text_item_embeds[neg_items]
                text_teacher_mf_loss, G_text_batch_emb_loss, G_text_batch_reg_loss = self.bpr_loss_for_KD(text_u_embed, text_pos_i_embed, text_neg_i_embed)

                # # ================= 蒸馏损失计算原理 =================
                # kd_loss = self.distillation(student_mf_loss, teacher_mf_loss, temp=args.student_tau, alpha=0.7)
                # image_kd_loss = self.distillation(student_mf_loss, image_teacher_mf_loss, temp=args.student_tau, alpha=0.7)
                # text_kd_loss = self.distillation(student_mf_loss, text_teacher_mf_loss, temp=args.student_tau, alpha=0.7)
 
                # # 调用 DKD Loss (列表级)
                # kd_loss_list = self.distillation(list_wise_loss_s, list_wise_loss_t, temp=args.student_tau, alpha=0.7)
                # kd_loss_list_image = self.distillation(list_wise_loss_s, list_wise_loss_t_image, temp=args.student_tau, alpha=0.7)
                # kd_loss_list_text = self.distillation(list_wise_loss_s, list_wise_loss_t_text, temp=args.student_tau, alpha=0.7)
                
                # # 计算 DKD Loss
                # kd_loss_list_dkd = self.dkd_loss(list_wise_score_s, list_wise_score_t, target, args.decouple_alpha, args.decouple_beta, args.decouple_t)
                # # =========================================================================


                # # ================= 蒸馏损失计算原理 =================
                # # 1. 彻底废弃旧的基于 BPR Loss 的对齐 (因为它们不能用 Softmax 处理)
                # # kd_loss, image_kd_loss, text_kd_loss 被移除，全面拥抱 Logits 蒸馏
                
                # # 2. 全面采用基于真实的 Logits 和 动态温度 (current_dynamic_tau) 的标准蒸馏
                # # 注意：这里传入的是 list_wise_logits，而不是 loss 或者 score
                # kd_loss_list = self.distillation(list_wise_logits_s, list_wise_logits_t, temp=current_dynamic_tau, alpha=0.7)
                # kd_loss_list_image = self.distillation(list_wise_logits_s, list_wise_logits_t_image, temp=current_dynamic_tau, alpha=0.7)
                # kd_loss_list_text = self.distillation(list_wise_logits_s, list_wise_logits_t_text, temp=current_dynamic_tau, alpha=0.7)
                
                # # 3. 计算 DKD Loss (注意参数替换：传入 Logits 并且使用动态温度)
                # kd_loss_list_dkd = self.dkd_loss(list_wise_logits_s, list_wise_logits_t, target, args.decouple_alpha, args.decouple_beta, current_dynamic_tau)
                # # =========================================================================

                # ================= 蒸馏损失计算原理 =================
                # 注意：这里我们使用静态的 args.student_tau！
                kd_loss_list = self.distillation(list_wise_logits_s, list_wise_logits_t, temp=args.student_tau)
                kd_loss_list_image = self.distillation(list_wise_logits_s, list_wise_logits_t_image, temp=args.student_tau)
                kd_loss_list_text = self.distillation(list_wise_logits_s, list_wise_logits_t_text, temp=args.student_tau)
                
                # DKD 同样使用静态的 args.student_tau
                kd_loss_list_dkd = self.dkd_loss(list_wise_logits_s, list_wise_logits_t, target, args.decouple_alpha, args.decouple_beta, args.student_tau)
                # =========================================================================

                # user_embedding, item_embedding = self.student_model.get_embedding()
                # paras_list = [ user_embedding, item_embedding ]
                reg_loss = self.calcRegLoss([u_embed, i_embed])*args.emb_reg

                # ----feat kd loss-----------------------------------------------------------------------------------------------------------
                # self.u_final_embed, self.i_final_embed, image_item_embeds, text_item_embeds, image_user_embeds, text_user_embeds

                # reconstru_feat = decoder(feat_learned)

                # B. 特征蒸馏 (Feature Distillation)
                # 对应图中：Teacher's Multimodal Feats ---> Student's ID Embeddings
                # 原理：学生模型虽然没有处理图片的 encoder，但它的 ID Embedding 应该包含图片的信息。
                # 代码中通过 MSE 或 SCE 损失，强制学生 Embedding 去逼近教师的多模态 Embedding。
                if args.feat_loss_type=='mse':
                    # feature_loss = sce_criterion(reconstru_feat, features, mask_nodes_dict, alpha=args.alpha_l)
                    kd_loss_feat = self.mse_criterion(self.i_final_embed, i_embed, alpha=args.alpha_l)
                elif args.feat_loss_type=='sce':
                    kd_loss_feat = self.sce_criterion(image_item_embeds, i_embed, alpha=args.alpha_l, tip_rate=args.tip_rate_feat) + self.sce_criterion(text_item_embeds, i_embed, alpha=args.alpha_l, tip_rate=args.tip_rate_feat)
                # ----feat kd loss-----------------------------------------------------------------------------------------------------------


                # feat_emb_loss = self.feat_reg_loss_calculation(G_image_item_embeds, G_text_item_embeds, G_image_user_embeds, G_text_user_embeds)
                # student_batch_loss = batch_mf_loss + batch_emb_loss + args.kd_loss_rate*kd_loss + args.kd_loss_list_rate*kd_loss_list + args.kd_loss_feat_rate*kd_loss_feat + args.kd_loss_rate*image_kd_loss + args.kd_loss_rate*text_kd_loss + args.kd_loss_list_rate*kd_loss_list_image + args.kd_loss_list_rate*kd_loss_list_text
                # student_batch_loss = batch_mf_loss + batch_emb_loss + args.kd_loss_rate*kd_loss + args.kd_loss_list_rate*kd_loss_list + args.kd_loss_feat_rate*kd_loss_feat + args.kd_loss_list_rate*kd_loss_list_image + args.kd_loss_list_rate*kd_loss_list_text
                
                # student_batch_loss = batch_mf_loss + batch_emb_loss + args.kd_loss_rate*kd_loss + args.kd_loss_list_rate*kd_loss_list_image + args.kd_loss_list_rate*kd_loss_list_text
                # student_batch_loss = batch_mf_loss + batch_emb_loss 
                # student_batch_loss = batch_mf_loss + batch_emb_loss + args.kd_loss_rate*kd_loss
                
                # [总损失] 将所有知识融合
                # student_batch_loss = batch_mf_loss + batch_emb_loss + args.kd_loss_rate*kd_loss + args.kd_loss_list_rate*kd_loss_list_image + args.kd_loss_list_rate*kd_loss_list_text + args.kd_loss_feat_rate*kd_loss_feat
                
                # print(f'batch_mf_loss3: {batch_mf_loss}')  
                # print(f'batch_mf_loss: {batch_mf_loss}')
                # print(f'batch_emb_loss: {batch_emb_loss}')
                # print(f'kd_loss: {kd_loss}')
                # print(f'image_kd_loss: {image_kd_loss}')
                # print(f'text_kd_loss: {text_kd_loss}')
                # print(f'kd_loss_list: {kd_loss_list}')

                # line_var_loss.append(student_batch_loss.detach().data)
                             
                # 反向传播                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         #+ ssl_loss2 #+ batch_contrastive_loss
                # self.opt_S.zero_grad()  
                # student_batch_loss.backward(retain_graph=False)
                # self.opt_S.step()

                # 👇【第四步-第4处：更新总损失，并累加 KD loss】👇
                # [总损失] 将所有知识融合 (删除了基于BPR Loss的旧 kd_loss，引入真正的 DKD 损失)
                student_batch_loss = batch_mf_loss + batch_emb_loss + args.kd_loss_list_rate*kd_loss_list_image + args.kd_loss_list_rate*kd_loss_list_text + args.kd_loss_feat_rate*kd_loss_feat + kd_loss_list_dkd
                
                # 反向传播 
                self.opt_S.zero_grad()  
                student_batch_loss.backward(retain_graph=False)
                self.opt_S.step()

                # # 累加本 Batch 的 KD Loss，用于算出 Epoch 的平均值给下一轮的 DTS 调度器用
                # total_kd_loss_this_epoch += float(kd_loss_list_dkd)
                # # 👆-------------------------------------------------------👆

                loss += float(student_batch_loss)
                mf_loss += float(batch_mf_loss)
                emb_loss += float(batch_emb_loss)
                # reg_loss += float(G_batch_reg_loss)
        
                student_batch_loss_List.append(student_batch_loss.item())
                batch_mf_loss_List.append(batch_mf_loss.item())
                
                # 建议改为记录两个
                # kd_loss_List.append(kd_loss.item()) # 拓扑蒸馏损失
                # 建议改为记录两个
                kd_loss_List.append(kd_loss_list.item()) # 记录真正的 Logits 拓扑蒸馏损失
                # dkd_loss_List.append(kd_loss_list.item()) # List-wise 蒸馏损失 (如果你想记的话)

                # del ua_embeddings, ia_embeddings, G_ua_embeddings, G_ia_embeddings, G_u_g_embeddings, G_neg_i_g_embeddings, G_pos_i_g_embeddings
                del u_embed, i_embed, u_embeddings, pos_i_embeddings, neg_i_embeddings

            # # 👇【第四步-第5处：在 batch 循环结束后，计算平均值】👇
            # # 这一步极其重要，决定了下一轮温度降多少
            # last_epoch_kd_loss = total_kd_loss_this_epoch / n_batch
            # # 👆-------------------------------------------------------👆

            if math.isnan(loss) == True:
                self.logger.logging('ERROR: loss is nan.')
                sys.exit()

            if (epoch + 1) % args.verbose != 0:
                perf_str = 'Epoch %d [%.1fs]: train==[%.5f=%.5f + %.5f + %.5f  + %.5f]' % (
                    epoch, time() - t1, loss, mf_loss, emb_loss, reg_loss, contrastive_loss)
                training_time_list.append(time() - t1)
                self.logger.logging(perf_str)
            
            # 1. 记录各种 Loss，方便分析蒸馏起没起作用
            tb_writer.add_scalar('Student/Total_Loss', loss, epoch)
            tb_writer.add_scalar('Student/MF_Loss', mf_loss, epoch) # 基础推荐Loss
            tb_writer.add_scalar('Student/KD_Loss', sum(kd_loss_List)/len(kd_loss_List) if kd_loss_List else 0, epoch)
            # tb_writer.add_scalar('Student/KD_Loss', kd_loss, epoch) # 蒸馏Loss

            t2 = time()
            users_to_test = list(data_generator.test_set.keys())
            users_to_val = list(data_generator.val_set.keys())
            ret = self.test(users_to_test, is_val=False, is_teacher=False)  #^-^
            training_time_list.append(t2 - t1)
            t3 = time()

            recall20_List.append(ret['recall'][1])
            recall50_List.append(ret['recall'][-1])
            ndcg20_List.append(ret['ndcg'][1])
            ndcg50_List.append(ret['ndcg'][-1])

            # 2. 记录效果 Metrics - 注意：这里用的是 ret 变量
            tb_writer.add_scalar('Student/Recall@20', ret['recall'][1], epoch)
            tb_writer.add_scalar('Student/Recall@50', ret['recall'][-1], epoch)
            tb_writer.add_scalar('Student/NDCG@20', ret['ndcg'][1], epoch)

            tags = ["recall", "precision", "ndcg"]
           
            if args.verbose > 0:
                perf_str = 'Student: Epoch %d [%.1fs + %.1fs]: train==[%.5f=%.5f + %.5f + %.5f], recall=[%.5f, %.5f, %.5f, %.5f], ' \
                           'precision=[%.5f, %.5f, %.5f, %.5f], hit=[%.5f, %.5f, %.5f, %.5f], ndcg=[%.5f, %.5f, %.5f, %.5f]' % \
                           (epoch, t2 - t1, t3 - t2, loss, mf_loss, emb_loss, reg_loss, ret['recall'][0], ret['recall'][1], ret['recall'][2],
                            ret['recall'][-1],
                            ret['precision'][0], ret['precision'][1], ret['precision'][2], ret['precision'][-1], ret['hit_ratio'][0], ret['hit_ratio'][1], ret['hit_ratio'][2], ret['hit_ratio'][-1],
                            ret['ndcg'][0], ret['ndcg'][1], ret['ndcg'][2], ret['ndcg'][-1])
                self.logger.logging(perf_str)

            if ret['recall'][1] > best_recall:
                best_recall = ret['recall'][1]
                test_ret = self.test(users_to_test, is_val=False, is_teacher=False)
                self.logger.logging("Test_Recall@%d: %.5f,  precision=[%.5f], ndcg=[%.5f]" % (eval(args.Ks)[1], test_ret['recall'][1], test_ret['precision'][1], test_ret['ndcg'][1]))
                stopping_step = 0
            elif stopping_step < args.early_stopping_patience:
                stopping_step += 1
                self.logger.logging('#####Early stopping steps: %d #####' % stopping_step)
            else:
                self.logger.logging('#####Early stop! #####')
                break

        self.logger.logging(str(test_ret))
        
        print("Student 训练结束，正在保存结果...")
        
        # 重新打包一下 results，确保数据是最全的
        results = {
            'student_batch_loss_List': student_batch_loss_List,
            'batch_mf_loss_List': batch_mf_loss_List,
            'kd_loss_List':kd_loss_List,
            'recall20_List':recall20_List,
            'recall50_List':recall50_List,
            'ndcg20_List':ndcg20_List,
            'ndcg50_List':ndcg50_List,
        }

        exp_dir = './history/' + args.dataset
        if not os.path.exists(exp_dir):
            os.makedirs(exp_dir)

        base_name = str(args.point) if args.point else "result.pkl"
        if not base_name.endswith('.pkl'):
            base_name += '.pkl'

        student_filename = "student_" + base_name 

        save_path = os.path.join(exp_dir, student_filename)
        pickle.dump(results, open(save_path, 'wb'))

        print("########end:Student###################################")
        print(args.point)
        print("######################################################")

        tb_writer.close()
    # ----train_student-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def dkd_loss(self, logits_student, logits_teacher, target, alpha, beta, temperature):

        def _get_gt_mask(logits, target):
            target = target.reshape(-1)
            mask = torch.zeros_like(logits).scatter_(1, target.unsqueeze(1), 1).bool()
            return mask


        def _get_other_mask(logits, target):
            target = target.reshape(-1)
            mask = torch.ones_like(logits).scatter_(1, target.unsqueeze(1), 0).bool()
            return mask

        def _cat_mask(t, mask1, mask2):
            t1 = (t * mask1).sum(dim=1, keepdims=True)
            t2 = (t * mask2).sum(1, keepdims=True)
            rt = torch.cat([t1, t2], dim=1)
            return rt

        gt_mask = _get_gt_mask(logits_student, target)
        other_mask = _get_other_mask(logits_student, target)
        pred_student = F.softmax(logits_student / temperature, dim=1)
        pred_teacher = F.softmax(logits_teacher / temperature, dim=1)
        pred_student = _cat_mask(pred_student, gt_mask, other_mask)
        pred_teacher = _cat_mask(pred_teacher, gt_mask, other_mask)
        log_pred_student = torch.log(pred_student)
        tckd_loss = (
            F.kl_div(log_pred_student, pred_teacher, size_average=False)
            * (temperature**2)
            / target.shape[0]
        )
        pred_teacher_part2 = F.softmax(
            logits_teacher / temperature - 1000.0 * gt_mask, dim=1
        )
        log_pred_student_part2 = F.log_softmax(
            logits_student / temperature - 1000.0 * gt_mask, dim=1
        )
        nckd_loss = (
            F.kl_div(log_pred_student_part2, pred_teacher_part2, size_average=False)
            * (temperature**2)
            / target.shape[0]
        )
        return alpha * tckd_loss + beta * nckd_loss

    # def distillation(self, y, teacher_scores, temp, alpha):
    #     return nn.KLDivLoss()(F.log_softmax(y.unsqueeze(0) / temp, dim=1), F.softmax(teacher_scores.unsqueeze(0) / temp, dim=1)) 


    # def distillation(self, y, teacher_scores, temp, alpha):
    #     return nn.KLDivLoss()( y.unsqueeze(0), teacher_scores.unsqueeze(0) ) 之前跑实验用的函数

    # def distillation(self, y, labels, teacher_scores, temp, alpha):
    #     return nn.KLDivLoss()(F.log_softmax(y / temp, dim=1), F.softmax(teacher_scores / temp, dim=1)) * (
    #             temp * temp * 2.0 * alpha) + F.cross_entropy(y, labels) * (1. - alpha)

    # === [属于你的创新：标准温度缩放 KD] ===
    def distillation(self, student_logits, teacher_logits, temp):
        # 严格的 Hinton KD 公式
        return nn.KLDivLoss(reduction='batchmean')(
            F.log_softmax(student_logits / temp, dim=1), 
            F.softmax(teacher_logits / temp, dim=1)
        ) * (temp ** 2)

    def calcRegLoss(self, params=None, model=None):
        ret = 0
        if params is not None:
            for W in params:
                ret += W.norm(2).square()
        if model is not None:
            for W in model.parameters():
                ret += W.norm(2).square()
        # ret += (model.usrStruct + model.itmStruct)
        return ret

    def bpr_loss(self, users, pos_items, neg_items):
        pos_scores = torch.sum(torch.mul(users, pos_items), dim=1)
        neg_scores = torch.sum(torch.mul(users, neg_items), dim=1)

        regularizer = 1./2*(users**2).sum() + 1./2*(pos_items**2).sum() + 1./2*(neg_items**2).sum()        
        regularizer = regularizer / self.batch_size

        maxi = F.logsigmoid(pos_scores - neg_scores)
        mf_loss = -torch.mean(maxi)

        emb_loss = self.decay * regularizer
        return mf_loss, emb_loss

    def bpr_loss_for_KD(self, users, pos_items, neg_items):
        pos_scores = torch.sum(torch.mul(users, pos_items), dim=1)
        neg_scores = torch.sum(torch.mul(users, neg_items), dim=1)

        regularizer = 1./2*(users**2).sum() + 1./2*(pos_items**2).sum() + 1./2*(neg_items**2).sum()
        # regularizer = 1./2*(users**2) + 1./2*(pos_items**2) + 1./2*(neg_items**2)
        regularizer = regularizer / self.batch_size

        maxi = F.logsigmoid(pos_scores - neg_scores)
        # mf_loss = -torch.mean(maxi)
        mf_loss = -maxi

        emb_loss = self.decay * regularizer
        reg_loss = 0.0
        return mf_loss, emb_loss, reg_loss   

    def sparse_mx_to_torch_sparse_tensor(self, sparse_mx):
        """Convert a scipy sparse matrix to a torch sparse tensor."""
        sparse_mx = sparse_mx.tocoo().astype(np.float32)
        indices = torch.from_numpy(
            np.vstack((sparse_mx.row, sparse_mx.col)).astype(np.int64))
        values = torch.from_numpy(sparse_mx.data)
        shape = torch.Size(sparse_mx.shape)
        return torch.sparse.FloatTensor(indices, values, shape)

def set_seed(seed):
    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(seed) 
    torch.cuda.manual_seed_all(seed)  

if __name__ == '__main__':
    select_dataset()
    os.environ["CUDA_VISIBLE_DEVICES"] = str(args.gpu_id)
    set_seed(args.seed)
    config = dict()
    config['n_users'] = data_generator.n_users
    config['n_items'] = data_generator.n_items
    trainer = Trainer(data_config=config)
    trainer.train()

