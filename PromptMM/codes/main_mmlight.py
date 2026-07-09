from datetime import datetime
import math
import os
import random
import sys
from time import time
from tqdm import tqdm
import dgl
import pickle
import numpy as np
import scipy.sparse as sp
from scipy.sparse import csr_matrix

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torch.sparse as sparse
from torch import autograd

import copy

from utility.parser import args, select_dataset
# 注意：这里改成了 Models_mmlight
from Models_mmlight import Teacher_Model, Student_LightGCN, Student_GCN, Student_MLP, PromptLearner, Student_MMLight
from utility.batch_test import *
from utility.logging import Logger
from utility.norm import build_sim, build_knn_normalized_graph
from torch.utils.tensorboard import SummaryWriter

import setproctitle
setproctitle.setproctitle('EXP@weiw')

class Trainer(object):
    def __init__(self, data_config):
       
        self.task_name = "%s_%s_%s" % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), args.dataset, args.cf_model,)
        self.logger = Logger(filename=self.task_name, is_debug=args.debug)
        self.logger.logging("PID: %d" % os.getpid())
        self.logger.logging(str(args))

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
 
        self.image_feats = np.load(args.data_path + '{}/image_feat.npy'.format(args.dataset))
        self.text_feats = np.load(args.data_path + '{}/text_feat.npy'.format(args.dataset))
        self.image_feat_dim = self.image_feats.shape[-1]
        self.text_feat_dim = self.text_feats.shape[-1]

        self.ui_graph = self.ui_graph_raw = pickle.load(open(args.data_path + args.dataset + '/train_mat','rb'))

        self.image_ui_index = {'x':[], 'y':[]}
        self.text_ui_index = {'x':[], 'y':[]}

        self.n_users = self.ui_graph.shape[0]
        self.n_items = self.ui_graph.shape[1]        
        self.iu_graph = self.ui_graph.T
  
        self.ui_graph_dgl = dgl.heterograph({('user','ui','item'):self.ui_graph.nonzero()})
        self.iu_graph_dgl = dgl.heterograph({('user','ui','item'):self.iu_graph.nonzero()})

        self.ui_graph = self.csr_norm(self.ui_graph, mean_flag=True)
        self.iu_graph = self.csr_norm(self.iu_graph, mean_flag=True)
        self.adj = sp.vstack([sp.hstack([self.ui_graph, csr_matrix((self.n_users, self.n_users))]), sp.hstack([csr_matrix((self.n_items, self.n_items)), self.iu_graph])])

        self.ui_graph = self.matrix_to_tensor(self.ui_graph)
        self.iu_graph = self.matrix_to_tensor(self.iu_graph)
        self.adj = self.matrix_to_tensor(self.adj)  
        self.image_ui_graph = self.text_ui_graph = self.ui_graph
        self.image_iu_graph = self.text_iu_graph = self.iu_graph

        self.teacher_model = Teacher_Model(self.n_users, self.n_items, self.emb_dim, self.weight_size, self.mess_dropout, self.image_feats, self.text_feats)      
        self.teacher_model = self.teacher_model.cuda()
        self.prompt_module = PromptLearner(self.image_feats, self.text_feats, self.ui_graph)

        self.bce = nn.BCEWithLogitsLoss()
        self.bce_loss = nn.BCELoss()        

        self.opt_T = optim.AdamW([{'params':self.teacher_model.parameters()},
                                  {'params':self.prompt_module.parameters()}
                                  ], lr=self.lr, weight_decay=args.t_weight_decay)  

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

    def innerProduct(self, u_pos, i_pos, u_neg, j_neg):  
        pred_i = torch.sum(torch.mul(u_pos,i_pos), dim=-1) 
        pred_j = torch.sum(torch.mul(u_neg,j_neg), dim=-1)  
        return pred_i, pred_j

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
        return torch.mm(z1, z2.t())

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
        ind_sorted = np.argsort(pred.cpu().data).cuda()
        loss_sorted = pred[ind_sorted]
        remember_rate = 1 - drop_rate
        num_remember = int(remember_rate * len(loss_sorted))
        ind_update = ind_sorted[:num_remember]
        loss_update = pred[ind_update]
        return loss_update.mean()

    def mse_criterion(self, x, y, mask_nodes_dict=None, alpha=3):
        x = F.normalize(x, p=2, dim=-1)
        y = F.normalize(y, p=2, dim=-1)
        tmp_loss = (1 - (x * y).sum(dim=-1)).pow_(alpha)
        tmp_loss = tmp_loss.mean()
        loss = F.mse_loss(x, y)
        return loss

    def sce_criterion(self, x, y, alpha=1, tip_rate=0):
        x = F.normalize(x, p=2, dim=-1)
        y = F.normalize(y, p=2, dim=-1)
        loss = (1-(x*y).sum(dim=-1)).pow_(alpha)
        if tip_rate!=0:
            loss = self.loss_function(loss, tip_rate)   
            return loss
        loss = loss.mean() 
        return loss

    def test(self, users_to_test, is_val, is_teacher=True):
        self.teacher_model.eval()
        with torch.no_grad():
            if is_teacher:
                u_embed, i_embed, *rest = self.teacher_model(self.ui_graph, self.iu_graph, self.prompt_module)
            else:
                # MMLight Student 需要 Teacher 的多模态 Embedding 作为输入
                with torch.no_grad():
                        self.u_final_embed, self.i_final_embed, image_item_embeds, text_item_embeds, image_user_embeds, text_user_embeds \
                        , G_user_emb, G_item_emb, prompt_user, prompt_item \
                        = self.teacher_model(self.ui_graph, self.iu_graph, self.prompt_module)

                if args.student_model_type=='lightgcn':
                    u_embed, i_embed = self.student_model(self.adj, image_item_embeds, text_item_embeds, image_user_embeds, text_user_embeds)
                elif args.student_model_type=='gcn': 
                    u_embed, i_embed = self.student_model(self.u_final_embed, self.i_final_embed, self.ui_graph, self.iu_graph, image_item_embeds, text_item_embeds, image_user_embeds, text_user_embeds)
                elif args.student_model_type=='mlp': 
                    u_embed, i_embed = self.student_model(self.u_final_embed, self.i_final_embed, image_item_embeds, text_item_embeds, image_user_embeds, text_user_embeds)  
                elif args.student_model_type=='mm_light':
                    u_embed, i_embed = self.student_model(image_item_embeds, text_item_embeds, image_user_embeds, text_user_embeds)
                    
        result = test_torch(u_embed, i_embed, users_to_test, is_val)
        return result

    def train(self):
        now_time = datetime.now()
        run_time = datetime.strftime(now_time,'%Y_%m_%d__%H_%M_%S')

        # ================= [TensorBoard] =================
        run_name = f"{args.dataset}_{str(args.point) if args.point else 'default'}"
        tb_writer = SummaryWriter(log_dir=f'./runs/{run_name}')
        # ================================================

        training_time_list = []
        loss_loger, pre_loger, rec_loger, ndcg_loger, hit_loger = [], [], [], [], []
        
        # 遗留变量，保持不报错
        line_var_loss, line_g_loss, line_d_loss, line_cl_loss, line_var_recall, line_var_precision, line_var_ndcg = [], [], [], [], [], [], []
        
        stopping_step = 0
        should_stop = False
        cur_best_pre_0 = 0. 

        # ==================== Teacher Training ====================
        if args.if_train_teacher: 
            print("########begin:Teacher###################################")
            print(args.point)
            print("########################################################")
            n_batch = data_generator.n_train // args.batch_size + 1
            s_best_recall = 0
            
            for epoch in range(args.epoch):
                t1 = time()
                loss, mf_loss, emb_loss, reg_loss = 0., 0., 0., 0.
                contrastive_loss = 0.
                f_time, b_time, loss_time, opt_time, clip_time, emb_time = 0., 0., 0., 0., 0., 0.
                sample_time = 0.
                build_item_graph = True

                self.gene_u, self.gene_real, self.gene_fake = None, None, {}
                self.topk_p_dict, self.topk_id_dict = {}, {}

                for idx in tqdm(range(n_batch)):
                    self.teacher_model.train()
                    sample_t1 = time()
                    users, pos_items, neg_items = data_generator.sample()
                    sample_time += time() - sample_t1       

                    t_u_id_embed, t_i_id_embed, t_i_image_embed, t_i_text_embed, t_u_image_embed, t_u_text_embed \
                                    , G_user_emb, G_item_emb, prompt_user, prompt_item \
                            = self.teacher_model(self.ui_graph, self.iu_graph, self.prompt_module)

                    t_u_id_embed_pbr = t_u_id_embed[users]
                    t_i_id_embed_pbr_pos = t_i_id_embed[pos_items]
                    t_i_id_embed_pbr_neg = t_i_id_embed[neg_items]
                    t_mf_loss, t_emb_loss = self.bpr_loss(t_u_id_embed_pbr, t_i_id_embed_pbr_pos, t_i_id_embed_pbr_neg)
        
                    u_id_embed_pbr_prompt = prompt_user[users]
                    i_id_embed_pbr_pos_prompt = prompt_item[pos_items]
                    i_id_embed_pbr_neg_prompt = prompt_item[neg_items]
                    mf_loss_prompt, emb_loss_prompt = self.bpr_loss(u_id_embed_pbr_prompt, i_id_embed_pbr_pos_prompt, i_id_embed_pbr_neg_prompt)
        
                    t_image_u_g_embeddings = t_u_image_embed[users]
                    t_image_pos_i_g_embeddings = t_i_image_embed[pos_items]
                    t_image_neg_i_g_embeddings = t_i_image_embed[neg_items]
                    t_image_batch_mf_loss, G_image_batch_emb_loss = self.bpr_loss(t_image_u_g_embeddings, t_image_pos_i_g_embeddings, t_image_neg_i_g_embeddings)

                    t_text_u_g_embeddings = t_u_text_embed[users]
                    t_text_pos_i_g_embeddings = t_i_text_embed[pos_items]
                    t_text_neg_i_g_embeddings = t_i_text_embed[neg_items]
                    t_text_batch_mf_loss, G_text_batch_emb_loss = self.bpr_loss(t_text_u_g_embeddings, t_text_pos_i_g_embeddings, t_text_neg_i_g_embeddings)

                    feat_emb_loss = self.feat_reg_loss_calculation(t_i_image_embed, t_i_text_embed, t_u_image_embed, t_u_text_embed)

                    t_batch_loss = t_mf_loss + t_emb_loss + feat_emb_loss + args.t_prompt_rate1*mf_loss_prompt + args.t_feat_mf_rate*t_image_batch_mf_loss + args.t_feat_mf_rate*t_text_batch_mf_loss

                    line_var_loss.append(t_batch_loss.detach().data)
                    
                    self.opt_T.zero_grad()  
                    t_batch_loss.backward(retain_graph=False)
                    self.opt_T.step()

                    loss += float(t_batch_loss)
                    mf_loss += float(t_emb_loss)
                    
                    del t_u_id_embed, t_i_id_embed, t_i_image_embed, t_i_text_embed, t_u_image_embed, t_u_text_embed \
                                    , G_user_emb, G_item_emb, t_u_id_embed_pbr, t_i_id_embed_pbr_pos, t_i_id_embed_pbr_neg

                if math.isnan(loss) == True:
                    self.logger.logging('ERROR: loss is nan.')
                    sys.exit()

                if (epoch + 1) % args.verbose != 0:
                    perf_str = 'Epoch %d [%.1fs]: train==[%.5f=%.5f + %.5f + %.5f  + %.5f]' % (
                        epoch, time() - t1, loss, mf_loss, emb_loss, reg_loss, contrastive_loss)
                    training_time_list.append(time() - t1)
                    self.logger.logging(perf_str)

                # TensorBoard Teacher Loss
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

                # TensorBoard Teacher Metrics
                tb_writer.add_scalar('Teacher/Recall@20', s_ret['recall'][1], epoch)
                tb_writer.add_scalar('Teacher/NDCG@20', s_ret['ndcg'][1], epoch)

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
            print("######end:Teacher#####################################")
            
            # 保存教师结果
            teacher_results = {
                'loss': loss_loger,
                'recall': rec_loger,
                'precision': pre_loger,
                'ndcg': ndcg_loger,
                'hit': hit_loger,
                'time': training_time_list
            }
            exp_dir = './history/' + args.dataset
            if not os.path.exists(exp_dir): os.makedirs(exp_dir)
            base_name = str(args.point) if args.point else "result.pkl"
            if not base_name.endswith('.pkl'): base_name += '.pkl'
            teacher_filename = "teacher_" + base_name
            save_path = os.path.join(exp_dir, teacher_filename)
            self.logger.logging(f"保存教师实验结果到: {save_path}")
            pickle.dump(teacher_results, open(save_path, 'wb'))


        # ==================== Student Training ====================
        print("########begin:Student###################################")
        print(args.point)
        print("#######################################################")
        n_batch = data_generator.n_train // args.batch_size + 1
        best_recall = 0

        # Load Teacher
        load_path = './weights/' + args.dataset + '/teacher_model_great.pt'
        self.teacher_model.load_state_dict(torch.load(load_path))
        self.teacher_model.eval()

        with torch.no_grad():
            self.u_final_embed, self.i_final_embed, image_item_embeds, text_item_embeds, image_user_embeds, text_user_embeds \
            , G_user_emb, G_item_emb, prompt_user, prompt_item \
            = self.teacher_model(self.ui_graph, self.iu_graph, self.prompt_module)

        # Init Student
        if args.student_model_type=='lightgcn':
            self.student_model = Student_LightGCN(self.n_users, self.n_items, self.student_emb_dim, self.student_n_layers, self.mess_dropout, self.image_feats, self.text_feats)   
            self.student_model.init_user_item_embed(self.u_final_embed, self.i_final_embed)
        elif args.student_model_type=='gcn': 
            self.student_model = Student_GCN(self.n_users, self.n_items, self.student_emb_dim, self.student_n_layers, self.mess_dropout, self.image_feats, self.text_feats)   
        elif args.student_model_type=='mlp': 
            self.student_model = Student_MLP()   
            self.student_model.init_user_item_embed(self.u_final_embed, self.i_final_embed)
        elif args.student_model_type=='mm_light':
            self.student_model = Student_MMLight(self.n_users, self.n_items, self.student_emb_dim, self.student_n_layers, self.mess_dropout, self.image_feats, self.text_feats, self.ui_graph, self.iu_graph)   
            self.student_model.init_user_item_embed(self.u_final_embed, self.i_final_embed)

        self.student_model = self.student_model.cuda()
        self.opt_S = optim.AdamW([{'params':self.student_model.parameters()},
                                  {'params':self.prompt_module.parameters()}
                                  ], lr=self.student_lr)  

        # ================= [Fixed: Init List outside loop] =================
        student_batch_loss_List = []
        batch_mf_loss_List = []
        kd_loss_List = []
        recall20_List = []
        recall50_List = []
        ndcg20_List = []
        ndcg50_List = []
        # ===================================================================

        for epoch in range(args.epoch):
            t1 = time()
            loss, mf_loss, emb_loss, reg_loss = 0., 0., 0., 0.
            contrastive_loss = 0.
            f_time, b_time, loss_time, opt_time, clip_time, emb_time = 0., 0., 0., 0., 0., 0.
            sample_time = 0.
            build_item_graph = True

            self.gene_u, self.gene_real, self.gene_fake = None, None, {}
            self.topk_p_dict, self.topk_id_dict = {}, {}

            for idx in tqdm(range(n_batch)):
                self.teacher_model.train()
                sample_t1 = time()
                users, pos_items, neg_items = data_generator.sample()  # [1024], [1024], [1024] 
                sample_time += time() - sample_t1      

                # MM Light 需要 Teacher 的特征作为输入
                with torch.no_grad():
                    self.u_final_embed, self.i_final_embed, image_item_embeds, text_item_embeds, image_user_embeds, text_user_embeds \
                    , G_user_emb, G_item_emb, prompt_user, prompt_item \
                    = self.teacher_model(self.ui_graph, self.iu_graph, self.prompt_module)

                if args.student_model_type=='lightgcn':
                    u_embed, i_embed = self.student_model(self.adj, image_item_embeds, text_item_embeds, image_user_embeds, text_user_embeds)
                elif args.student_model_type=='gcn': 
                    u_embed, i_embed = self.student_model(self.u_final_embed, self.i_final_embed, self.ui_graph, self.iu_graph, image_item_embeds, text_item_embeds, image_user_embeds, text_user_embeds)
                elif args.student_model_type=='mlp': 
                    u_embed, i_embed = self.student_model(self.u_final_embed, self.i_final_embed, image_item_embeds, text_item_embeds, image_user_embeds, text_user_embeds)
                elif args.student_model_type=='mm_light': 
                    u_embed, i_embed = self.student_model(image_item_embeds, text_item_embeds, image_user_embeds, text_user_embeds)

                u_embeddings = u_embed[users]
                pos_i_embeddings = i_embed[pos_items]
                neg_i_embeddings = i_embed[neg_items]
                batch_mf_loss, batch_emb_loss = self.bpr_loss(u_embeddings, pos_i_embeddings, neg_i_embeddings)

                if args.student_model_type=='mlp':
                    batch_mf_loss = self.student_model.pairPredictwEmbeds(u_embed, i_embed, users, pos_items, neg_items).sum()

                # -----------------------------KD-----------------------------------
                if args.student_model_type=='mlp':
                    student_mf_loss = self.student_model.pairPredictwEmbeds(u_embed, i_embed, users, pos_items, neg_items)
                else:
                    student_mf_loss, student_batch_emb_loss, batch_reg_loss = self.bpr_loss_for_KD(u_embeddings, pos_i_embeddings, neg_i_embeddings) 

                # List-wise Ranking Preparation
                sub_x_index, sub_y_index = self.ui_graph_raw[users].nonzero()[0], self.ui_graph_raw[users].nonzero()[1]
                sub_dgl_g = dgl.graph((sub_x_index, sub_y_index)).to('cuda:0')
                neg_row, neg_col = dgl.sampling.global_uniform_negative_sampling(sub_dgl_g, len(users)*args.neg_sample_num, replace=True)
                neg_row, neg_col = neg_row.reshape((len(users), args.neg_sample_num)), neg_col.reshape((len(users), args.neg_sample_num))
                item_index = torch.cat((torch.tensor(pos_items).cuda().unsqueeze(1), neg_col), dim=1)

                list_wise_score_s = torch.mul(u_embed[users].unsqueeze(1), i_embed[item_index]).sum(-1).softmax(-1) 
                list_wise_loss_s = -(list_wise_score_s+1e-8).log() 
                target = torch.zeros(list_wise_loss_s.shape[0]).long().cuda() 
                
                list_wise_score_t = torch.mul(self.u_final_embed[users].unsqueeze(1),self.i_final_embed[item_index]).sum(-1).softmax(-1) 
                list_wise_loss_t = -(list_wise_score_t+1e-8).log()
                list_wise_score_t_image = torch.mul(image_user_embeds[users].unsqueeze(1), image_item_embeds[item_index]).sum(-1).softmax(-1) 
                list_wise_loss_t_image = -(list_wise_score_t_image+1e-8).log()
                list_wise_score_t_text = torch.mul(text_user_embeds[users].unsqueeze(1), text_item_embeds[item_index]).sum(-1).softmax(-1) 
                list_wise_loss_t_text = -(list_wise_score_t_text+1e-8).log()

                del sub_x_index, sub_y_index, sub_dgl_g
 
                u_g_embed_mf = self.u_final_embed[users]
                pos_i_g_embed_mf = self.i_final_embed[pos_items]
                neg_i_g_embed_mf = self.i_final_embed[neg_items]

                teacher_mf_loss, teacher_batch_emb_loss, G_batch_reg_loss = self.bpr_loss_for_KD(u_g_embed_mf, pos_i_g_embed_mf, neg_i_g_embed_mf)
       
                image_u_embed = image_user_embeds[users]
                image_pos_i_embed = image_item_embeds[pos_items]
                image_neg_i_embed = image_item_embeds[neg_items]
                image_teacher_mf_loss, G_image_batch_emb_loss, G_image_batch_reg_loss = self.bpr_loss_for_KD(image_u_embed, image_pos_i_embed, image_neg_i_embed)

                text_u_embed = text_user_embeds[users]
                text_pos_i_embed = text_item_embeds[pos_items]
                text_neg_i_embed = text_item_embeds[neg_items]
                text_teacher_mf_loss, G_text_batch_emb_loss, G_text_batch_reg_loss = self.bpr_loss_for_KD(text_u_embed, text_pos_i_embed, text_neg_i_embed)

                kd_loss = self.distillation(student_mf_loss, teacher_mf_loss, temp=args.student_tau, alpha=0.7)
                image_kd_loss = self.distillation(student_mf_loss, image_teacher_mf_loss, temp=args.student_tau, alpha=0.7)
                text_kd_loss = self.distillation(student_mf_loss, text_teacher_mf_loss, temp=args.student_tau, alpha=0.7)

                kd_loss_list = self.distillation(list_wise_loss_s, list_wise_loss_t, temp=args.student_tau, alpha=0.7)
                kd_loss_list_image = self.distillation(list_wise_loss_s, list_wise_loss_t_image, temp=args.student_tau, alpha=0.7)
                kd_loss_list_text = self.distillation(list_wise_loss_s, list_wise_loss_t_text, temp=args.student_tau, alpha=0.7)

                # kd_loss_list = self.dkd_loss(list_wise_score_s, list_wise_score_t, target, args.decouple_alpha, args.decouple_beta, args.decouple_t)
                
                reg_loss = self.calcRegLoss([u_embed, i_embed])*args.emb_reg

                # ----feat kd loss-----------------------------------------------------------------------------------------------------------
                if args.feat_loss_type=='mse':
                    kd_loss_feat = self.mse_criterion(self.i_final_embed, i_embed, alpha=args.alpha_l)
                elif args.feat_loss_type=='sce':
                    kd_loss_feat = self.sce_criterion(image_item_embeds, i_embed, alpha=args.alpha_l, tip_rate=args.tip_rate_feat) + self.sce_criterion(text_item_embeds, i_embed, alpha=args.alpha_l, tip_rate=args.tip_rate_feat)
                # ----feat kd loss-----------------------------------------------------------------------------------------------------------

                student_batch_loss = batch_mf_loss + batch_emb_loss + args.kd_loss_rate*kd_loss + args.kd_loss_list_rate*kd_loss_list_image + args.kd_loss_list_rate*kd_loss_list_text + args.kd_loss_feat_rate*kd_loss_feat

                self.opt_S.zero_grad()  
                student_batch_loss.backward(retain_graph=False)
                self.opt_S.step()

                loss += float(student_batch_loss)
                mf_loss += float(batch_mf_loss)
                emb_loss += float(batch_emb_loss)
        
                student_batch_loss_List.append(student_batch_loss.item())
                batch_mf_loss_List.append(batch_mf_loss.item())
                kd_loss_List.append(kd_loss_list.item())

                del u_embed, i_embed, u_embeddings, pos_i_embeddings, neg_i_embeddings

            if math.isnan(loss) == True:
                self.logger.logging('ERROR: loss is nan.')
                sys.exit()

            if (epoch + 1) % args.verbose != 0:
                perf_str = 'Epoch %d [%.1fs]: train==[%.5f=%.5f + %.5f + %.5f  + %.5f]' % (
                    epoch, time() - t1, loss, mf_loss, emb_loss, reg_loss, contrastive_loss)
                training_time_list.append(time() - t1)
                self.logger.logging(perf_str)

            # TensorBoard Student
            tb_writer.add_scalar('Student/Total_Loss', loss, epoch)
            tb_writer.add_scalar('Student/MF_Loss', mf_loss, epoch)
            tb_writer.add_scalar('Student/KD_Loss', kd_loss, epoch)

            t2 = time()
            users_to_test = list(data_generator.test_set.keys())
            users_to_val = list(data_generator.val_set.keys())
            ret = self.test(users_to_test, is_val=False, is_teacher=False)  #^-^
            training_time_list.append(t2 - t1)
            t3 = time()

            # Record Metrics
            recall20_List.append(ret['recall'][1])
            recall50_List.append(ret['recall'][-1])
            ndcg20_List.append(ret['ndcg'][1])
            ndcg50_List.append(ret['ndcg'][-1])

            # TensorBoard Metrics
            tb_writer.add_scalar('Student/Recall@20', ret['recall'][1], epoch)
            tb_writer.add_scalar('Student/Recall@50', ret['recall'][-1], epoch)
            tb_writer.add_scalar('Student/NDCG@20', ret['ndcg'][1], epoch)

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
        print("########end:S###################################")
        
        # Save Student Results
        print("Student 训练结束，正在保存结果...")
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
        if not os.path.exists(exp_dir): os.makedirs(exp_dir)
        base_name = str(args.point) if args.point else "result.pkl"
        if not base_name.endswith('.pkl'): base_name += '.pkl'
        student_filename = "student_" + base_name 
        save_path = os.path.join(exp_dir, student_filename)
        pickle.dump(results, open(save_path, 'wb'))

        print(args.point)
        print("######################################################")

        tb_writer.close()

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

    def distillation(self, y, teacher_scores, temp, alpha):
        return nn.KLDivLoss()( y.unsqueeze(0), teacher_scores.unsqueeze(0) ) 

    def calcRegLoss(self, params=None, model=None):
        ret = 0
        if params is not None:
            for W in params:
                ret += W.norm(2).square()
        if model is not None:
            for W in model.parameters():
                ret += W.norm(2).square()
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
        regularizer = 1./2*(users**2) + 1./2*(pos_items**2) + 1./2*(neg_items**2)
        regularizer = regularizer / self.batch_size
        maxi = F.logsigmoid(pos_scores - neg_scores)
        mf_loss = -maxi
        emb_loss = self.decay * regularizer
        reg_loss = 0.0
        return mf_loss, emb_loss, reg_loss   

    def sparse_mx_to_torch_sparse_tensor(self, sparse_mx):
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