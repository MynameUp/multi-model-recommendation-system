import argparse
# # #----mf-------------------------------------------------------------------------------------------------------------------------
# def parse_args():
#     parser = argparse.ArgumentParser(description="")

# #     parser = argparse.ArgumentParser(description="")

#     parser.add_argument('--data_path', nargs='?', default='/home/ww/Code/work5/MASL/data/',
#                         help='Input data path.')
#     parser.add_argument('--seed', type=int, default=2022,
#                         help='Random seed')
#     parser.add_argument('--dataset', nargs='?', default='baby',
#                         help='Choose a dataset from {sports, baby, clothing, tiktok, allrecipes}')
#     parser.add_argument('--verbose', type=int, default=5,
#                         help='Interval of evaluation.')
#     parser.add_argument('--epoch', type=int, default=1000,
#                         help='Number of epoch.')  #default: 1000
#     parser.add_argument('--batch_size', type=int, default=1024,
#                         help='Batch size.')
#     parser.add_argument('--regs', nargs='?', default='[1e-5,1e-5,1e-2]',
#                         help='Regularizations.')  #default: '[1e-5,1e-5,1e-2]'
#     parser.add_argument('--lr', type=float, default=0.0005,
#                         help='Learning rate.')
#     parser.add_argument('--D_lr', type=float, default=3e-4, help='Learning rate.')

#     parser.add_argument('--embed_size', type=int, default=64,
#                         help='Embedding size.')                     
#     parser.add_argument('--weight_size', nargs='?', default='[64, 64]',
#                         help='Output sizes of every layer')  #default: '[64, 64]'
#     parser.add_argument('--core', type=int, default=5,
#                         help='5-core for warm-start; 0-core for cold start')
#     parser.add_argument('--topk', type=int, default=10, help='K value of k-NN sparsification')  
#     parser.add_argument('--lambda_coeff', type=float, default=0.9,
#                         help='Lambda value of skip connection')
#     parser.add_argument('--cf_model', nargs='?', default='mmgcn',
#                         help='Downstream Collaborative Filtering model {mf, ngcf, lightgcn, mmgcn, vbpr, hafr, slmrec}')   
#     parser.add_argument('--early_stopping_patience', type=int, default=7,
#                         help='') 
#     parser.add_argument('--layers', type=int, default=1,
#                         help='Number of item graph conv layers')  
#     parser.add_argument('--mess_dropout', nargs='?', default='[0.1, 0.1]',
#                         help='Keep probability w.r.t. message dropout (i.e., 1-dropout_ratio) for each deep layer. 1: no dropout.')

#     parser.add_argument('--sparse', type=int, default=1, help='Sparse or dense adjacency matrix')   
#     parser.add_argument('--debug', action='store_true')  
#     parser.add_argument('--cl_rate', type=float, default=0.03, help='Control the effect of the contrastive auxiliary task')        
#     parser.add_argument('--norm_type', nargs='?', default='sym', help='Adjacency matrix normalization operation') 
#     parser.add_argument('--gpu_id', type=int, default=0,
#                         help='GPU id')
#     parser.add_argument('--Ks', nargs='?', default='[10, 20, 50]',
#                         help='K value of ndcg/recall @ k')
#     parser.add_argument('--test_flag', nargs='?', default='part',
#                         help='Specify the test type from {part, full}, indicating whether the reference is done in mini-batch')

#     parser.add_argument('--metapath_threshold', default=2, type=int, help='metapath_threshold') 
#     parser.add_argument('--sc', type=float, default=1.0, help='GCN self connection')
#     parser.add_argument('--drop_rate', type=float, default=0.2, help='dropout rate')
#     parser.add_argument('--model_cat_rate', type=float, default=0.55, help='model_cat_rate')
#     parser.add_argument('--ssl_c_rate', type=float, default=1.3, help='ssl_c_rate')
#     parser.add_argument('--ssl_s_rate', type=float, default=0.8, help='ssl_s_rate')
#     parser.add_argument('--g_rate', type=float, default=0.000029, help='ssl_s_rate')
#     parser.add_argument('--sample_num', default=1, type=int, help='sample_num') 
#     parser.add_argument('--sample_num_neg', default=1, type=int, help='sample_num') 
#     parser.add_argument('--sample_num_ii', default=8, type=int, help='sample_num') 
#     parser.add_argument('--sample_num_co', default=2, type=int, help='sample_num') 
#     parser.add_argument('--mask_rate', default=0.75, type=float, help='sample_num') 
#     parser.add_argument('--gss_rate', default=0.85, type=float, help='gene_self_subgraph_rate') 
#     parser.add_argument('--anchor_rate', default=0.75, type=float, help='anchor_rate') 
#     parser.add_argument('--feat_reg_decay', default=1e-5, type=float, help='feat_reg_decay') 
#     parser.add_argument('--ad1_rate', default=0.2, type=float, help='ad1_rate') 
#     parser.add_argument('--ad2_rate', default=0.2, type=float, help='ad1_rate') 
#     parser.add_argument('--ad_sampNum', type=int, default=1, help='ad topk')  
#     parser.add_argument('--ad_topk_multi_num', type=int, default=100, help='ad topk')  
#     parser.add_argument('--fake_gene_rate', default=0.0001, type=float, help='fake_gene_rate') 
#     parser.add_argument('--ID_layers', type=int, default=1, help='Number of item graph conv layers')  
#     parser.add_argument('--reward_rate', default=1, type=float, help='fake_gene_rate') 
#     parser.add_argument('--G_embed_size', type=int, default=64, help='Embedding size.')   
#     parser.add_argument('--model_num', default=2, type=float, help='fake_gene_rate') 
#     parser.add_argument('--negrate', default=0.01, type=float, help='item_neg_sample_rate')
#     parser.add_argument('--cis', default=25, type=int, help='') 
#     parser.add_argument('--confidence', default=0.5, type=float, help='') 
#     parser.add_argument('--tau', default=0.5, type=float, help='')  #
#     parser.add_argument('--geneGraph_rate', default=0.1, type=float, help='')  #
#     parser.add_argument('--geneGraph_rate_pos', default=2, type=float, help='')  #
#     parser.add_argument('--geneGraph_rate_neg', default=-1, type=float, help='')  #     

#     parser.add_argument('--ii_it', default=15, type=int, help='') 
#     parser.add_argument('--G_rate', default=0.0003, type=float, help='')  #
#     parser.add_argument('--G_drop1', default=0.31, type=float, help='')  #
#     parser.add_argument('--G_drop2', default=0.5, type=float, help='')  #
#     parser.add_argument('--gp_rate', default=1, type=float, help='')  #
#     parser.add_argument('--real_data_tau', default=0.002, type=float, help='')  #
#     parser.add_argument('--L2_alpha', default=1e-3, type=float, help='')  #
#     parser.add_argument('--emm', default=1e-3, type=float, help='')  #
#     parser.add_argument('--isload', default=False , type=bool, help='whether load model')  #布尔值加引号...直接编译为True
#     parser.add_argument('--isJustTest', default=False , type=bool, help='whether load model')
#     parser.add_argument('--loadModelPath', default='/home/ww/Code/work3/BSTRec/Model/retailrocket/for_meta_hidden_dim_dim__8_retailrocket_2021_07_10__18_35_32_lr_0.0003_reg_0.01_batch_size_1024_gnn_layer_[16,16,16].pth', type=str, help='loadModelPath')
#     parser.add_argument('--title', default="try_to_draw_line", type=str, help='')  #

#     return parser.parse_args()
# # #----mf-------------------------------------------------------------------------------------------------------------------------


# #----allrecipes--------------------------------------------------------------------------------------------------------------------------
# def parse_args():
#     parser = argparse.ArgumentParser(description="")

# #     parser = argparse.ArgumentParser(description="")

#     parser.add_argument('--data_path', nargs='?', default='/home/ww/Code/work5/MASL/data/',
#                         help='Input data path.')
#     parser.add_argument('--seed', type=int, default=2022,
#                         help='Random seed')
#     parser.add_argument('--dataset', nargs='?', default='allrecipes',
#                         help='Choose a dataset from {sports, baby, clothing, tiktok, allrecipes}')
#     parser.add_argument('--verbose', type=int, default=5,
#                         help='Interval of evaluation.')
#     parser.add_argument('--epoch', type=int, default=1000,
#                         help='Number of epoch.')  #default: 1000
#     parser.add_argument('--batch_size', type=int, default=1024,
#                         help='Batch size.')
#     parser.add_argument('--regs', nargs='?', default='[1e-5,1e-5,1e-2]',
#                         help='Regularizations.')  #default: '[1e-5,1e-5,1e-2]'
#     parser.add_argument('--lr', type=float, default=0.00056,
#                         help='Learning rate.')
#     parser.add_argument('--D_lr', type=float, default=0.00025, help='Learning rate.')

#     parser.add_argument('--embed_size', type=int, default=64,
#                         help='Embedding size.')                     
#     parser.add_argument('--weight_size', nargs='?', default='[64, 64]',
#                         help='Output sizes of every layer')  #default: '[64, 64]'
#     parser.add_argument('--core', type=int, default=5,
#                         help='5-core for warm-start; 0-core for cold start')
#     parser.add_argument('--topk', type=int, default=10, help='K value of k-NN sparsification')  
#     parser.add_argument('--lambda_coeff', type=float, default=0.9,
#                         help='Lambda value of skip connection')
#     parser.add_argument('--cf_model', nargs='?', default='hafr',
#                         help='Downstream Collaborative Filtering model {mf, ngcf, lightgcn, vbpr, hafr, ngcf_init, light_init}')   
#     parser.add_argument('--early_stopping_patience', type=int, default=7,
#                         help='') 
#     parser.add_argument('--layers', type=int, default=1,
#                         help='Number of item graph conv layers')  
#     parser.add_argument('--mess_dropout', nargs='?', default='[0.1, 0.1]',
#                         help='Keep probability w.r.t. message dropout (i.e., 1-dropout_ratio) for each deep layer. 1: no dropout.')

#     parser.add_argument('--sparse', type=int, default=1, help='Sparse or dense adjacency matrix')   
#     parser.add_argument('--debug', action='store_true')  
#     parser.add_argument('--cl_rate', type=float, default=0.03, help='Control the effect of the contrastive auxiliary task')        
#     parser.add_argument('--norm_type', nargs='?', default='sym', help='Adjacency matrix normalization operation') 
#     parser.add_argument('--gpu_id', type=int, default=0,
#                         help='GPU id')
#     parser.add_argument('--Ks', nargs='?', default='[10, 20, 50]',
#                         help='K value of ndcg/recall @ k')
#     parser.add_argument('--test_flag', nargs='?', default='part',
#                         help='Specify the test type from {part, full}, indicating whether the reference is done in mini-batch')

#     parser.add_argument('--metapath_threshold', default=2, type=int, help='metapath_threshold') 
#     parser.add_argument('--sc', type=float, default=1.0, help='GCN self connection')
#     parser.add_argument('--drop_rate', type=float, default=0.2, help='dropout rate')
#     parser.add_argument('--model_cat_rate', type=float, default=0.55, help='model_cat_rate')
#     parser.add_argument('--id_cat_rate', type=float, default=0.34, help='id_cat_rate')
#     parser.add_argument('--feat_cat_rate', type=float, default=0.34, help='id_cat_rate')    
#     parser.add_argument('--ssl_c_rate', type=float, default=1.3, help='ssl_c_rate')
#     parser.add_argument('--ssl_s_rate', type=float, default=0.8, help='ssl_s_rate')
#     parser.add_argument('--g_rate', type=float, default=0.000029, help='ssl_s_rate')
#     parser.add_argument('--sample_num', default=1, type=int, help='sample_num') 
#     parser.add_argument('--sample_num_neg', default=1, type=int, help='sample_num') 
#     parser.add_argument('--sample_num_ii', default=8, type=int, help='sample_num') 
#     parser.add_argument('--sample_num_co', default=2, type=int, help='sample_num') 
#     parser.add_argument('--mask_rate', default=0.75, type=float, help='sample_num') 
#     parser.add_argument('--gss_rate', default=0.85, type=float, help='gene_self_subgraph_rate') 
#     parser.add_argument('--anchor_rate', default=0.75, type=float, help='anchor_rate') 
#     parser.add_argument('--feat_reg_decay', default=1e-5, type=float, help='feat_reg_decay') 
#     parser.add_argument('--ad1_rate', default=0.2, type=float, help='ad1_rate') 
#     parser.add_argument('--ad2_rate', default=0.2, type=float, help='ad1_rate') 
#     parser.add_argument('--ad_sampNum', type=int, default=1, help='ad topk')  
#     parser.add_argument('--ad_topk_multi_num', type=int, default=100, help='ad topk')  
#     parser.add_argument('--fake_gene_rate', default=0.0001, type=float, help='fake_gene_rate') 
#     parser.add_argument('--ID_layers', type=int, default=1, help='Number of item graph conv layers')  
#     parser.add_argument('--reward_rate', default=1, type=float, help='fake_gene_rate') 
#     parser.add_argument('--G_embed_size', type=int, default=64, help='Embedding size.')   
#     parser.add_argument('--model_num', default=2, type=float, help='fake_gene_rate') 
#     parser.add_argument('--negrate', default=0.01, type=float, help='item_neg_sample_rate')
#     parser.add_argument('--cis', default=25, type=int, help='') 
#     parser.add_argument('--confidence', default=0.5, type=float, help='') 
#     parser.add_argument('--tau', default=0.3, type=float, help='')  #
#     parser.add_argument('--geneGraph_rate', default=0.1, type=float, help='')  #
#     parser.add_argument('--geneGraph_rate_pos', default=2, type=float, help='')  #
#     parser.add_argument('--geneGraph_rate_neg', default=-1, type=float, help='')  #     

#     parser.add_argument('--ii_it', default=15, type=int, help='') 
#     parser.add_argument('--G_rate', default=0.00030, type=float, help='')  #
#     parser.add_argument('--G_drop1', default=0.31, type=float, help='')  #
#     parser.add_argument('--G_drop2', default=0.5, type=float, help='')  #
#     parser.add_argument('--gp_rate', default=1, type=float, help='')  #
#     parser.add_argument('--real_data_tau', default=0.02, type=float, help='')  #
#     parser.add_argument('--L2_alpha', default=1e-3, type=float, help='')  #
#     parser.add_argument('--emm', default=1e-3, type=float, help='')  #
#     parser.add_argument('--isload', default=False , type=bool, help='whether load model')  #
#     parser.add_argument('--isJustTest', default=False , type=bool, help='whether load model')
#     parser.add_argument('--loadModelPath', default='/home/ww/Code/work3/BSTRec/Model/retailrocket/for_meta_hidden_dim_dim__8_retailrocket_2021_07_10__18_35_32_lr_0.0003_reg_0.01_batch_size_1024_gnn_layer_[16,16,16].pth', type=str, help='loadModelPath')
#     parser.add_argument('--title', default="try_to_draw_line", type=str, help='')  #
#     parser.add_argument('--head_num', default=4, type=int, help='head_num_of_multihead_attention')  #
#     # parser.add_argument('--id_cat_rate', type=float, default=0.36, help='id_cat_rate')
#     parser.add_argument('--id_cat_rate1', type=float, default=0.36, help='id_cat_rate')
#     parser.add_argument('--T', default=2, type=int, help='it for ui update')  
#     parser.add_argument('--m_topk_rate', default=0.02, type=float, help='it for ui update')  
#     parser.add_argument('--ui_pre_scale', default=100, type=int, help='ui_pre_scale')  
#     parser.add_argument('--log_log_scale', default=0.00001, type=int, help='log_log_scale')  

#     return parser.parse_args()
# # ----allrecipes--------------------------------------------------------------------------------------------------------------------------
# # ----allrecipes--------------------------------------------------------------------------------------------------------------------------



# #----baby--------------------------------------------------------------------------------------------------------------------------
# def parse_args():
#     parser = argparse.ArgumentParser(description="")

#     #use less
#     parser.add_argument('--verbose', type=int, default=5, help='Interval of evaluation.')    
#     parser.add_argument('--core', type=int, default=5, help='5-core for warm-start; 0-core for cold start')
#     parser.add_argument('--lambda_coeff', type=float, default=0.9, help='Lambda value of skip connection')

#     parser.add_argument('--early_stopping_patience', type=int, default=7, help='') 
#     parser.add_argument('--layers', type=int, default=1, help='Number of feature graph conv layers')  
#     parser.add_argument('--mess_dropout', nargs='?', default='[0.1, 0.1]', help='Keep probability w.r.t. message dropout (i.e., 1-dropout_ratio) for each deep layer. 1: no dropout.')
#     parser.add_argument('--sparse', type=int, default=1, help='Sparse or dense adjacency matrix')   

#     parser.add_argument('--test_flag', nargs='?', default='part', help='Specify the test type from {part, full}, indicating whether the reference is done in mini-batch')
#     parser.add_argument('--metapath_threshold', default=2, type=int, help='metapath_threshold') 
#     parser.add_argument('--sc', type=float, default=1.0, help='GCN self connection')
#     parser.add_argument('--ssl_c_rate', type=float, default=1.3, help='ssl_c_rate')
#     parser.add_argument('--ssl_s_rate', type=float, default=0.8, help='ssl_s_rate')
#     parser.add_argument('--g_rate', type=float, default=0.000029, help='ssl_s_rate')
#     parser.add_argument('--sample_num', default=1, type=int, help='sample_num') 
#     parser.add_argument('--sample_num_neg', default=1, type=int, help='sample_num') 
#     parser.add_argument('--sample_num_ii', default=8, type=int, help='sample_num') 
#     parser.add_argument('--sample_num_co', default=2, type=int, help='sample_num') 
#     parser.add_argument('--mask_rate', default=0.75, type=float, help='sample_num') 
#     parser.add_argument('--gss_rate', default=0.85, type=float, help='gene_self_subgraph_rate') 
#     parser.add_argument('--anchor_rate', default=0.75, type=float, help='anchor_rate') 
#     parser.add_argument('--feat_reg_decay', default=1e-5, type=float, help='feat_reg_decay') 
#     parser.add_argument('--ad1_rate', default=0.2, type=float, help='ad1_rate') 
#     parser.add_argument('--ad2_rate', default=0.2, type=float, help='ad1_rate')     
#     parser.add_argument('--ad_sampNum', type=int, default=1, help='ad topk')  
#     parser.add_argument('--ad_topk_multi_num', type=int, default=100, help='ad topk')  
#     parser.add_argument('--fake_gene_rate', default=0.0001, type=float, help='fake_gene_rate') 
#     parser.add_argument('--ID_layers', type=int, default=1, help='Number of item graph conv layers')  
#     parser.add_argument('--reward_rate', default=1, type=float, help='fake_gene_rate') 
#     parser.add_argument('--G_embed_size', type=int, default=64, help='Embedding size.')   
#     parser.add_argument('--model_num', default=2, type=float, help='fake_gene_rate') 
#     parser.add_argument('--negrate', default=0.01, type=float, help='item_neg_sample_rate')
#     parser.add_argument('--cis', default=25, type=int, help='') 
#     parser.add_argument('--confidence', default=0.5, type=float, help='') 
#     parser.add_argument('--ii_it', default=15, type=int, help='') 
#     parser.add_argument('--isload', default=False , type=bool, help='whether load model')  #布尔值加引号...直接编译为True
#     parser.add_argument('--isJustTest', default=False , type=bool, help='whether load model')
#     parser.add_argument('--loadModelPath', default='/home/ww/Code/work3/BSTRec/Model/retailrocket/for_meta_hidden_dim_dim__8_retailrocket_2021_07_10__18_35_32_lr_0.0003_reg_0.01_batch_size_1024_gnn_layer_[16,16,16].pth', type=str, help='loadModelPath')
#     parser.add_argument('--title', default="try_to_draw_line", type=str, help='')  #


#     #train
#     parser.add_argument('--data_path', nargs='?', default='/home/weiw/Code/MM/KDMM/data/', help='Input data path.')
#     parser.add_argument('--seed', type=int, default=2022, help='Random seed')
#     parser.add_argument('--dataset', nargs='?', default='baby', help='Choose a dataset from {sports, baby, clothing, tiktok, allrecipes}')
#     parser.add_argument('--epoch', type=int, default=1000, help='Number of epoch.')  #default: 1000
#     parser.add_argument('--batch_size', type=int, default=1024, help='Batch size.')
#     parser.add_argument('--embed_size', type=int, default=64,help='Embedding size.')                     
#     parser.add_argument('--D_lr', type=float, default=3e-4, help='Learning rate.')
#     parser.add_argument('--topk', type=int, default=10, help='K value of k-NN sparsification')  
#     parser.add_argument('--cf_model', nargs='?', default='slmrec', help='Downstream Collaborative Filtering model {mf, ngcf, lightgcn, vbpr, hafr, clcrec, slmrec}')   
#     parser.add_argument('--debug', action='store_true')  
#     parser.add_argument('--cl_rate', type=float, default=0.03, help='Control the effect of the contrastive auxiliary task')        
#     parser.add_argument('--norm_type', nargs='?', default='sym', help='Adjacency matrix normalization operation') 
#     parser.add_argument('--gpu_id', type=int, default=0, help='GPU id')
#     parser.add_argument('--Ks', nargs='?', default='[10, 20, 40,50]', help='K value of ndcg/recall @ k')
#     parser.add_argument('--regs', nargs='?', default='[1e-5,1e-5,1e-2]', help='for emb_loss.')  #default: '[1e-5,1e-5,1e-2]'
#     parser.add_argument('--lr', type=float, default=0.00055, help='Learning rate.')
#     parser.add_argument('--emm', default=1e-3, type=float, help='for feature embedding bpr')  #
#     parser.add_argument('--L2_alpha', default=1e-3, type=float, help='')  #
#     parser.add_argument('--weight_decay', default=1e-4, type=float, help='for opt_D')  #


#     #GNN
#     parser.add_argument('--drop_rate', type=float, default=0.2, help='dropout rate')
#     parser.add_argument('--model_cat_rate', type=float, default=0.55, help='model_cat_rate')
#     parser.add_argument('--gnn_cat_rate', type=float, default=0.55, help='gnn_cat_rate')
#     parser.add_argument('--id_cat_rate', type=float, default=0.36, help='before GNNs')
#     parser.add_argument('--id_cat_rate1', type=float, default=0.36, help='id_cat_rate')
#     parser.add_argument('--head_num', default=4, type=int, help='head_num_of_multihead_attention. For multi-model relation.')  #
#     parser.add_argument('--dgl_nei_num', default=8, type=int, help='dgl_nei_num')  #


#     #GAN
#     parser.add_argument('--weight_size', nargs='?', default='[64, 64]', help='Output sizes of every layer')  #default: '[64, 64]'
#     parser.add_argument('--G_rate', default=0.0001, type=float, help='for D model1')  #
#     parser.add_argument('--G_drop1', default=0.31, type=float, help='for D model2')  #
#     parser.add_argument('--G_drop2', default=0.5, type=float, help='')  #
#     parser.add_argument('--gp_rate', default=1, type=float, help='gradient penal')  #

#     parser.add_argument('--real_data_tau', default=0.005, type=float, help='for real_data soft')  #
#     parser.add_argument('--ui_pre_scale', default=100, type=int, help='ui_pre_scale')  


#     #cl
#     parser.add_argument('--T', default=1, type=int, help='it for ui update')  
#     parser.add_argument('--tau', default=0.5, type=float, help='')  #
#     parser.add_argument('--geneGraph_rate', default=0.1, type=float, help='')  #
#     parser.add_argument('--geneGraph_rate_pos', default=2, type=float, help='')  #
#     parser.add_argument('--geneGraph_rate_neg', default=-1, type=float, help='')  #     
#     parser.add_argument('--m_topk_rate', default=0.0001, type=float, help='for reconstruct')  
#     parser.add_argument('--log_log_scale', default=0.00001, type=int, help='log_log_scale')  
#     parser.add_argument('--point', default='', type=str, help='point')  

#     # kd
#     parser.add_argument('--kd_loss_rate', default=500000, type=float, help='')  #
#     parser.add_argument('--kd_loss_image_rate', default=500000, type=float, help='')  #
#     parser.add_argument('--kd_loss_text_rate', default=500000, type=float, help='')  #
#     parser.add_argument('--student_embed_size', type=int, default=32, help='Embedding size.')  # 16, 32        
#     parser.add_argument('--student_lr', type=float, default=0.002, help='Learning rate.')  #0.002 0.001, 0.00001   
#     parser.add_argument('--student_n_layers', type=int, default=1, help='Number of item graph conv layers')  
#     parser.add_argument('--student_tau', type=float, default=5, help='Learning rate.')  #0.002 0.001, 0.00001     
#     parser.add_argument('--neg_sample_num', type=float, default=10, help='Learning rate.')     
            

#     return parser.parse_args()
# #----baby--------------------------------------------------------------------------------------------------------------------------





# #----netflix--------------------------------------------------------------------------------------------------------------------------
# def parse_args():
#     parser = argparse.ArgumentParser(description="")


#     return parser.parse_args()
# #----netflix--------------------------------------------------------------------------------------------------------------------------








#----clothing--------------------------------------------------------------------------------------------------------------------------
# def parse_args():
#     parser = argparse.ArgumentParser(description="")

#     parser.add_argument('--data_path', nargs='?', default='/home/weiw/Code/MM/KDMM/data/',
#                         help='Input data path.')  # /home/weiw/Code/MM/MICRO2Ours/data/     /home/weiw/Datasets/MM/LATTICE/    /home/weiw/Code/MM/KDMM/data/
#     parser.add_argument('--seed', type=int, default=2022,
#                         help='Random seed')
#     parser.add_argument('--dataset', nargs='?', default='clothing',
#                         help='Choose a dataset from {sports, baby, clothing, tiktok, allrecipes}')
#     parser.add_argument('--verbose', type=int, default=5,
#                         help='Interval of evaluation.')
#     parser.add_argument('--epoch', type=int, default=1000,
#                         help='Number of epoch.')  #default: 1000
#     parser.add_argument('--batch_size', type=int, default=1024,
#                         help='Batch size.')
#     parser.add_argument('--regs', nargs='?', default='[1e-5,1e-5,1e-2]',
#                         help='Regularizations.')  #default: '[1e-5,1e-5,1e-2]'
#     parser.add_argument('--lr', type=float, default=0.0005,
#                         help='Learning rate.')
#     parser.add_argument('--D_lr', type=float, default=3e-4, help='Learning rate.')

#     parser.add_argument('--embed_size', type=int, default=32,
#                         help='Embedding size.')                     
#     parser.add_argument('--weight_size', nargs='?', default='[64, 64]',
#                         help='Output sizes of every layer')  #default: '[64, 64]'
#     parser.add_argument('--core', type=int, default=5,
#                         help='5-core for warm-start; 0-core for cold start')
#     parser.add_argument('--topk', type=int, default=10, help='K value of k-NN sparsification')  
#     parser.add_argument('--lambda_coeff', type=float, default=0.9,
#                         help='Lambda value of skip connection')
#     parser.add_argument('--cf_model', nargs='?', default='light_init',
#                         help='Downstream Collaborative Filtering model {mf, ngcf, lightgcn, vbpr, hafr, ngcf_init, light_init}')   #light_init
#     parser.add_argument('--early_stopping_patience', type=int, default=7,
#                         help='') 
#     parser.add_argument('--layers', type=int, default=1,
#                         help='Number of item graph conv layers')  
#     parser.add_argument('--mess_dropout', nargs='?', default='[0.1, 0.1]',
#                         help='Keep probability w.r.t. message dropout (i.e., 1-dropout_ratio) for each deep layer. 1: no dropout.')

#     parser.add_argument('--sparse', type=int, default=1, help='Sparse or dense adjacency matrix')   
#     parser.add_argument('--debug', action='store_true')  
#     parser.add_argument('--cl_rate', type=float, default=0.03, help='Control the effect of the contrastive auxiliary task')        
#     parser.add_argument('--norm_type', nargs='?', default='sym', help='Adjacency matrix normalization operation') 
#     parser.add_argument('--gpu_id', type=int, default=2, help='GPU id')
#     parser.add_argument('--Ks', nargs='?', default='[10, 20, 40, 50]',
#                         help='K value of ndcg/recall @ k')
#     parser.add_argument('--test_flag', nargs='?', default='part',
#                         help='Specify the test type from {part, full}, indicating whether the reference is done in mini-batch')

#     parser.add_argument('--metapath_threshold', default=2, type=int, help='metapath_threshold') 
#     parser.add_argument('--sc', type=float, default=1.0, help='GCN self connection')
#     parser.add_argument('--drop_rate', type=float, default=0.2, help='dropout rate')
#     parser.add_argument('--model_cat_rate', type=float, default=0.55, help='model_cat_rate')
#     parser.add_argument('--ssl_c_rate', type=float, default=1.3, help='ssl_c_rate')
#     parser.add_argument('--ssl_s_rate', type=float, default=0.8, help='ssl_s_rate')
#     parser.add_argument('--g_rate', type=float, default=0.000029, help='ssl_s_rate')
#     parser.add_argument('--sample_num', default=1, type=int, help='sample_num') 
#     parser.add_argument('--sample_num_neg', default=1, type=int, help='sample_num') 
#     parser.add_argument('--sample_num_ii', default=8, type=int, help='sample_num') 
#     parser.add_argument('--sample_num_co', default=2, type=int, help='sample_num') 
#     parser.add_argument('--mask_rate', default=0.75, type=float, help='sample_num') 
#     parser.add_argument('--gss_rate', default=0.85, type=float, help='gene_self_subgraph_rate') 
#     parser.add_argument('--anchor_rate', default=0.75, type=float, help='anchor_rate') 
#     parser.add_argument('--feat_reg_decay', default=1e-5, type=float, help='feat_reg_decay') 
#     parser.add_argument('--ad1_rate', default=0.2, type=float, help='ad1_rate') 
#     parser.add_argument('--ad2_rate', default=0.2, type=float, help='ad1_rate') 
#     parser.add_argument('--ad_sampNum', type=int, default=1, help='ad topk')  
#     parser.add_argument('--ad_topk_multi_num', type=int, default=100, help='ad topk')  
#     parser.add_argument('--fake_gene_rate', default=0.0001, type=float, help='fake_gene_rate') 
#     parser.add_argument('--ID_layers', type=int, default=1, help='Number of item graph conv layers')  
#     parser.add_argument('--reward_rate', default=1, type=float, help='fake_gene_rate') 
#     parser.add_argument('--G_embed_size', type=int, default=32, help='Embedding size.')   
#     parser.add_argument('--model_num', default=2, type=float, help='fake_gene_rate') 
#     parser.add_argument('--negrate', default=0.01, type=float, help='item_neg_sample_rate')
#     parser.add_argument('--cis', default=25, type=int, help='') 
#     parser.add_argument('--confidence', default=0.5, type=float, help='') 
#     parser.add_argument('--tau', default=0.5, type=float, help='')  #
#     parser.add_argument('--geneGraph_rate', default=0.1, type=float, help='')  #
#     parser.add_argument('--geneGraph_rate_pos', default=2, type=float, help='')  #
#     parser.add_argument('--geneGraph_rate_neg', default=-1, type=float, help='')  #     

#     parser.add_argument('--ii_it', default=15, type=int, help='') 
#     parser.add_argument('--G_rate', default=0.0001, type=float, help='')  #
#     parser.add_argument('--G_drop1', default=0.31, type=float, help='')  #
#     parser.add_argument('--G_drop2', default=0.5, type=float, help='')  #
#     parser.add_argument('--gp_rate', default=1, type=float, help='')  #
#     parser.add_argument('--real_data_tau', default=0.002, type=float, help='')  #
#     parser.add_argument('--weight_decay', default=1e-4, type=float, help='')  #
#     parser.add_argument('--L2_alpha', default=1e-3, type=float, help='')  #
#     parser.add_argument('--emm', default=1.1e-3, type=float, help='')  #
#     parser.add_argument('--isload', default=False , type=bool, help='whether load model')  #布尔值加引号...直接编译为True
#     parser.add_argument('--isJustTest', default=False , type=bool, help='whether load model')
#     parser.add_argument('--loadModelPath', default='/home/ww/Code/work3/BSTRec/Model/retailrocket/for_meta_hidden_dim_dim__8_retailrocket_2021_07_10__18_35_32_lr_0.0003_reg_0.01_batch_size_1024_gnn_layer_[16,16,16].pth', type=str, help='loadModelPath')
#     parser.add_argument('--title', default="try_to_draw_line", type=str, help='')  #
#     parser.add_argument('--head_num', default=4, type=int, help='head_num_of_multihead_attention')  #
#     parser.add_argument('--id_cat_rate', type=float, default=0.36, help='id_cat_rate')
#     parser.add_argument('--id_cat_rate1', type=float, default=0.36, help='id_cat_rate')
#     parser.add_argument('--T', default=2, type=int, help='it for ui update')  
#     parser.add_argument('--m_topk_rate', default=0.02, type=float, help='it for ui update')
#     parser.add_argument('--point', default='', type=str, help='point')  

#     # kd
#     parser.add_argument('--kd_loss_rate', default=500000, type=float, help='')  #
#     parser.add_argument('--student_embed_size', type=int, default=32, help='Embedding size.')  # 16, 32        
#     parser.add_argument('--student_lr', type=float, default=0.002, help='Learning rate.')  #0.002 0.001, 0.00001   
#     parser.add_argument('--student_n_layers', type=int, default=1, help='Number of item graph conv layers')  
#     parser.add_argument('--student_tau', type=float, default=5, help='Learning rate.')  #0.002 0.001, 0.00001 
#     parser.add_argument('--kd_loss_image_rate', default=500000, type=float, help='')  #
#     parser.add_argument('--kd_loss_text_rate', default=500000, type=float, help='')  #      
            

#     return parser.parse_args()
#----clothing--------------------------------------------------------------------------------------------------------------------------


#----sports--------------------------------------------------------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="PromptMM")

    # ==================== 1. 基础环境与数据配置 ====================
    parser.add_argument('--data_path', nargs='?', default='/root/autodl-tmp/PromptMM/data/', help='Input data path.')
    parser.add_argument('--seed', type=int, default=2022, help='Random seed')
    parser.add_argument('--dataset', nargs='?', default='sports', help='Choose a dataset')
    parser.add_argument('--verbose', type=int, default=5, help='Interval of evaluation.')
    parser.add_argument('--epoch', type=int, default=1000, help='Number of epoch.')
    parser.add_argument('--batch_size', type=int, default=1024, help='Batch size.')
    parser.add_argument('--gpu_id', type=int, default=0, help='GPU id')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--isload', default=False, type=bool, help='whether load model')
    parser.add_argument('--isJustTest', default=False, type=bool, help='whether load model')
    parser.add_argument('--loadModelPath', default='', type=str, help='loadModelPath')
    parser.add_argument('--title', default="try_to_draw_line", type=str, help='')
    parser.add_argument('--point', default='run_sports_moe_v1', type=str, help='point')

    # ==================== 2. 模型核心配置 ====================
    parser.add_argument('--cf_model', nargs='?', default='light_init', help='Downstream CF model')
    parser.add_argument('--embed_size', type=int, default=64, help='Embedding size.')
    parser.add_argument('--weight_size', nargs='?', default='[64, 64]', help='Output sizes of every layer')
    parser.add_argument('--layers', type=int, default=3, help='Number of item graph conv layers')
    parser.add_argument('--mess_dropout', nargs='?', default='[0.1, 0.1]', help='Message dropout')
    parser.add_argument('--drop_rate', type=float, default=0.2, help='dropout rate')
    parser.add_argument('--model_cat_rate', type=float, default=0.8, help='model_cat_rate')
    parser.add_argument('--sparse', type=int, default=1, help='Sparse or dense adjacency matrix')
    parser.add_argument('--norm_type', nargs='?', default='sym', help='Adjacency matrix normalization')
    parser.add_argument('--head_num', default=4, type=int, help='head_num_of_multihead_attention')

    # ==================== 3. 训练与优化器配置 ====================
    parser.add_argument('--lr', type=float, default=0.0005, help='Learning rate.')
    parser.add_argument('--D_lr', type=float, default=3e-4, help='Learning rate.')
    parser.add_argument('--regs', nargs='?', default='[1e-5,1e-5,1e-2]', help='Regularizations.')
    parser.add_argument('--emb_reg', default=1e-7, type=float, help='weight decay regularizer')
    parser.add_argument('--early_stopping_patience', type=int, default=8, help='')
    parser.add_argument('--Ks', nargs='?', default='[10, 20, 40, 50]', help='K value of ndcg/recall @ k')
    parser.add_argument('--test_flag', nargs='?', default='part', help='Specify the test type')

    # ==================== 4. Teacher 特定配置 ====================
    # parser.add_argument('--if_train_teacher', default=True, type=bool, help='')
    parser.add_argument('--if_train_teacher', default=1, type=int, help='1 for true, 0 for false')
    parser.add_argument('--teacher_reg_rate', type=float, default=1, help='')
    parser.add_argument('--t_feat_mf_rate', type=float, default=1, help='model_cat_rate')
    parser.add_argument('--t_weight_decay', type=float, default=0.001, help='T_weight_decay')
    parser.add_argument('--feat_reg_decay', default=1e-5, type=float, help='feat_reg_decay')

    # ==================== 5. Student & 蒸馏 (KD) 配置 ====================
    parser.add_argument('--student_model_type', type=str, default='mlp')
    parser.add_argument('--student_embed_size', type=int, default=64, help='Embedding size.')
    parser.add_argument('--student_lr', type=float, default=0.001, help='Learning rate.')
    parser.add_argument('--student_reg_rate', type=float, default=1, help='')
    parser.add_argument('--student_n_layers', type=int, default=1, help='Number of item graph conv layers')
    parser.add_argument('--student_tau', type=float, default=2.0, help='Temperature')
    parser.add_argument('--student_drop_rate', type=float, default=0.2, help='dropout rate')
    parser.add_argument('--neg_sample_num', type=int, default=10, help='Learning rate.')
    
    # 各种蒸馏 Loss 的权重
    parser.add_argument('--kd_loss_rate', default=1.0, type=float, help='')
    parser.add_argument('--kd_loss_list_rate', default=1.0, type=float, help='')
    parser.add_argument('--kd_loss_feat_rate', type=float, default=1.0, help='dropout rate')
    parser.add_argument('--kd_loss_image_rate', default=500000, type=float, help='')
    parser.add_argument('--kd_loss_text_rate', default=500000, type=float, help='')
    parser.add_argument('--list_wise_loss_rate', type=float, default=1, help='Learning rate.')

    # DKD (Decoupled Knowledge Distillation) 参数
    parser.add_argument('--decouple_alpha', default=100, type=float, help='DKD alpha')
    parser.add_argument('--decouple_beta', default=1, type=float, help='DKD beta')
    parser.add_argument('--decouple_t', default=1, type=float, help='DKD temperature')

    # 特征 Loss 参数
    parser.add_argument('--feat_loss_type', type=str, default='sce', help='mse, sce')
    parser.add_argument("--alpha_l", type=float, default=2, help="pow index for sce loss")
    parser.add_argument("--tip_rate_feat", type=float, default=0, help="")

    # ==================== 6. Prompt 与 MoE (创新点) 配置 ====================
    parser.add_argument('--hard_token_type', type=str, default='pca', help='pca, ica, isomap, tsne, lda')
    parser.add_argument('--soft_token_rate', default=1, type=float, help='')
    parser.add_argument('--feat_soft_token_rate', type=float, default=0.05, help='控制Prompt注入多模态特征的比例')
    parser.add_argument('--t_prompt_rate1', default=1, type=float, help='')
    parser.add_argument('--t_prompt_rate2', default=1, type=float, help='')
    parser.add_argument('--t_prompt_rate3', default=1, type=float, help='')
    
    # MoE 开关与参数
    parser.add_argument('--use_moe', type=int, default=1, help='1:开启MoE, 0:使用原始Linear层')
    parser.add_argument('--num_experts', type=int, default=4, help='Total number of experts') 
    parser.add_argument('--top_k', type=int, default=2, help='Number of active experts')
    parser.add_argument('--prompt_dropout', type=float, default=0.1, help='Dropout rate')

    # 【新增】MoE 负载均衡 Loss 的权重
    parser.add_argument('--moe_loss_weight', type=float, default=0.05, help='Weight for MoE load balancing auxiliary loss')

    # 【新增】ProMoE 正交惩罚 Loss 权重
    parser.add_argument('--ortho_loss_weight', type=float, default=0.1, help='Weight for orthogonal gating penalty loss in ProMoE')

    # ==================== 6.5. DTS 调度器配置 (论文级重构) ====================
    parser.add_argument('--dts_scheduler_type', type=str, default='gradient',
                        help='DTS scheduler: gradient (论文公式), cosine (余弦退火), magnitude (Loss比例)')
    parser.add_argument('--dts_eta', type=float, default=0.01, help='DTS gradient scheduler learning rate')
    parser.add_argument('--dts_momentum', type=float, default=0.9, help='EMA momentum for gradient smoothing')
    parser.add_argument('--dts_warmup', type=int, default=2, help='Warmup epochs before DTS gradient kicks in')

    # ==================== 7. 其他遗留图/对比学习参数 ====================
    # (保持原样以防其他模块调用)
    parser.add_argument('--core', type=int, default=5, help='5-core for warm-start; 0-core for cold start')
    parser.add_argument('--topk', type=int, default=10, help='K value of k-NN sparsification')  
    parser.add_argument('--lambda_coeff', type=float, default=0.9, help='Lambda value of skip connection')
    parser.add_argument('--cl_rate', type=float, default=0.03, help='Control the effect of the contrastive auxiliary task')
    parser.add_argument('--metapath_threshold', default=2, type=int, help='metapath_threshold')
    parser.add_argument('--sc', type=float, default=1.0, help='GCN self connection')
    parser.add_argument('--ssl_c_rate', type=float, default=1.3, help='ssl_c_rate')
    parser.add_argument('--ssl_s_rate', type=float, default=0.8, help='ssl_s_rate')
    parser.add_argument('--g_rate', type=float, default=0.000029, help='ssl_s_rate')
    parser.add_argument('--sample_num', default=1, type=int, help='sample_num')
    parser.add_argument('--sample_num_neg', default=1, type=int, help='sample_num')
    parser.add_argument('--sample_num_ii', default=8, type=int, help='sample_num')
    parser.add_argument('--sample_num_co', default=2, type=int, help='sample_num')
    parser.add_argument('--mask_rate', default=0.75, type=float, help='sample_num')
    parser.add_argument('--gss_rate', default=0.85, type=float, help='gene_self_subgraph_rate')
    parser.add_argument('--anchor_rate', default=0.75, type=float, help='anchor_rate')
    parser.add_argument('--ad1_rate', default=0.2, type=float, help='ad1_rate')
    parser.add_argument('--ad2_rate', default=0.2, type=float, help='ad1_rate')
    parser.add_argument('--ad_sampNum', type=int, default=1, help='ad topk')
    parser.add_argument('--ad_topk_multi_num', type=int, default=100, help='ad topk')
    parser.add_argument('--fake_gene_rate', default=0.0001, type=float, help='fake_gene_rate')
    parser.add_argument('--ID_layers', type=int, default=1, help='Number of item graph conv layers')
    parser.add_argument('--reward_rate', default=1, type=float, help='fake_gene_rate')
    parser.add_argument('--G_embed_size', type=int, default=32, help='Embedding size.')
    parser.add_argument('--model_num', default=2, type=float, help='fake_gene_rate')
    parser.add_argument('--negrate', default=0.01, type=float, help='item_neg_sample_rate')
    parser.add_argument('--cis', default=25, type=int, help='')
    parser.add_argument('--confidence', default=0.5, type=float, help='')
    parser.add_argument('--tau', default=0.5, type=float, help='')
    parser.add_argument('--geneGraph_rate', default=0.1, type=float, help='')
    parser.add_argument('--geneGraph_rate_pos', default=2, type=float, help='')
    parser.add_argument('--geneGraph_rate_neg', default=-1, type=float, help='')
    parser.add_argument('--ii_it', default=15, type=int, help='')
    parser.add_argument('--G_drop1', default=0.31, type=float, help='')
    parser.add_argument('--G_drop2', default=0.5, type=float, help='')
    parser.add_argument('--gp_rate', default=1, type=float, help='')
    parser.add_argument('--real_data_tau', default=0.002, type=float, help='')
    parser.add_argument('--weight_decay', default=1e-4, type=float, help='')
    parser.add_argument('--L2_alpha', default=1e-3, type=float, help='')
    parser.add_argument('--emm', default=1.1e-3, type=float, help='')
    parser.add_argument('--id_cat_rate', type=float, default=0.36, help='id_cat_rate')
    parser.add_argument('--id_cat_rate1', type=float, default=0.36, help='id_cat_rate')
    parser.add_argument('--T', default=2, type=int, help='it for ui update')
    parser.add_argument('--m_topk_rate', default=0.02, type=float, help='it for ui update')

    return parser.parse_args()

args = parse_args()


# 定义针对不同数据集的参数解析器
# 注意：代码中有多个 parse_args() 定义，Python 会执行最后一个被定义的函数。
# 假设我们运行的是 Amazon 数据集（文件末尾的那个 parser）
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#---netflix-----------------------------------------------------------------------------------------------------------------------------------------------------------------------
# parser = argparse.ArgumentParser(description='Deep Learning')
# parser.add_argument('--dataset', type=str, default='netflix', help='netflix, tiktok, amazon')

# parser.add_argument('--data_path', nargs='?', default='/home/weiw/Code/MM/KDMM/data/', help='Input data path.')  # /home/weiw/Code/MM/MICRO2Ours/data/     /home/weiw/Datasets/MM/LATTICE/    /home/weiw/Code/MM/KDMM/data/
# parser.add_argument('--Ks', nargs='?', default='[10, 20, 40, 50]', help='K value of ndcg/recall @ k')
# parser.add_argument('--seed', type=int, default=2022, help='Random seed')
# parser.add_argument('--verbose', type=int, default=5, help='Interval of evaluation.')
# parser.add_argument('--sparse', type=int, default=1, help='Sparse or dense adjacency matrix')   
# parser.add_argument('--debug', action='store_true')  
# parser.add_argument('--test_flag', nargs='?', default='part', help='Specify the test type from {part, full}, indicating whether the reference is done in mini-batch')
# parser.add_argument('--ssl_c_rate', type=float, default=None, help='ssl_c_rate')
# parser.add_argument('--ssl_s_rate', type=float, default=None, help='ssl_s_rate')
# parser.add_argument('--sample_num', default=None, type=int, help='sample_num') 
# parser.add_argument('--sample_num_neg', default=None, type=int, help='sample_num') 
# parser.add_argument('--sample_num_ii', default=None, type=int, help='sample_num') 
# parser.add_argument('--anchor_rate', default=None, type=float, help='anchor_rate') 
# parser.add_argument('--ad_topk_multi_num', type=int, default=None, help='ad topk')  
# parser.add_argument('--head_num', default=None, type=int, help='head_num_of_multihead_attention. For multi-model relation.')  #
# parser.add_argument('--point', default='ours', type=str, help='point')  

# # train
# parser.add_argument('--batch_size', type=int, default=1024, help='Batch size.')  # [1024:4096]
# parser.add_argument('--epoch', type=int, default=1000, help='Number of epoch.')  #default: 1000
# parser.add_argument('--cf_model', nargs='?', default='light_init', help='Downstream Collaborative Filtering model {mf, ngcf, lightgcn, vbpr, hafr}')   
# parser.add_argument('--early_stopping_patience', type=int, default=7, help='') 
# parser.add_argument('--gpu_id', type=int, default=0, help='GPU id')
# parser.add_argument('--regs', nargs='?', default='[1e-5,1e-5,1e-2]', help='Regularizations.')  #default: '[1e-5,1e-5,1e-2]'
# parser.add_argument('--emb_reg', default=1e-7, type=float, help='weight decay regularizer')
# #teacher
# parser.add_argument('--model_cat_rate', type=float, default=0.55, help='model_cat_rate')  #[0.55:0.05]
# parser.add_argument('--weight_size', nargs='?', default='[64, 64]', help='Output sizes of every layer')  #default: '[64, 64]'
# parser.add_argument('--embed_size', type=int, default=32, help='Embedding size.')  #    
# parser.add_argument('--drop_rate', type=float, default=0.4, help='dropout rate')
# parser.add_argument('--t_weight_decay', type=float, default=0.001, help='T_weight_decay')
# parser.add_argument('--lr', type=float, default=0.0005, help='Learning rate.')  #【0.0005:0.00005】
# parser.add_argument('--teacher_reg_rate', type=float, default=1, help='')  # 
# parser.add_argument('--t_feat_mf_rate', type=float, default=1, help='model_cat_rate')
# parser.add_argument('--feat_reg_decay', default=1e-5, type=float, help='feat_reg_decay') 
# parser.add_argument('--layers', type=int, default=1, help='Number of item graph conv layers')  
# parser.add_argument('--mess_dropout', nargs='?', default='[0.1, 0.1]', help='Keep probability w.r.t. message dropout (i.e., 1-dropout_ratio) for each deep layer. 1: no dropout.')
# # kd
# parser.add_argument('--student_embed_size', type=int, default=32, help='Embedding size.')  # 16, 32        
# parser.add_argument('--student_lr', type=float, default=0.00002, help='Learning rate.')  #0.002 0.001, 0.00001  0.00002
# parser.add_argument('--student_reg_rate', type=float, default=1, help='')  # 
# parser.add_argument('--student_n_layers', type=int, default=1, help='Number of item graph conv layers')  
# parser.add_argument('--student_tau', type=float, default=5, help='Learning rate.')  #0.002 0.001, 0.00001    
# parser.add_argument('--neg_sample_num', type=int, default=10, help='Learning rate.')  # 1,5,10
# parser.add_argument('--list_wise_loss_rate', type=float, default=1, help='Learning rate.')  # 0,1,8,9,10 
# parser.add_argument('--if_train_teacher', default=True, type=bool, help='')
# parser.add_argument('--kd_loss_rate', default=5000000000, type=float, help='')  # 800000
# parser.add_argument('--kd_loss_image_rate', default=500000, type=float, help='')  #
# parser.add_argument('--kd_loss_text_rate', default=500000, type=float, help='')  #
# parser.add_argument('--kd_loss_list_rate', default=1000000, type=float, help='')  # 1000000
# parser.add_argument('--student_drop_rate', type=float, default=0.3, help='dropout rate')
# parser.add_argument('--student_model_type', type=str, default='mm_light', help='')     
# parser.add_argument('--kd_loss_feat_rate', type=float, default=0.9, help='dropout rate')
# parser.add_argument("--alpha_l", type=float, default=2, help="`pow`inddex for `sce` loss")
# parser.add_argument("--tip_rate_feat", type=float, default=0, help="")  #0.2 ! ^ ~    
# parser.add_argument('--feat_loss_type', type=str, default='sce') # mse, sce
# # prompt 
# parser.add_argument('--hard_token_type', type=str, default='pca', help='pca, ica, isomap, tsne, lda')
# parser.add_argument('--soft_token_rate', default=0.005, type=float, help='')  # 0.0001 0.001, 0.00012, 0.05
# parser.add_argument('--feat_soft_token_rate', default=1, type=float, help='')  # 0.0001 0.001, 0.00012, 0.05
# parser.add_argument('--t_prompt_rate1', default=100, type=float, help='')  #
# parser.add_argument('--t_prompt_rate2', default=1, type=float, help='')  #
# parser.add_argument('--t_prompt_rate3', default=1, type=float, help='')  #
# parser.add_argument('--prompt_dropout', default=0, type=float, help='')  #
# # 
# parser.add_argument('--decouple_alpha', default=100, type=float, help='')  #
# parser.add_argument('--decouple_beta', default=1, type=float, help='')  #
# parser.add_argument('--decouple_t', default=1, type=float, help='')  #

# args = parser.parse_args()
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#---netflix-----------------------------------------------------------------------------------------------------------------------------------------------------------------------



#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#---tiktok-----------------------------------------------------------------------------------------------------------------------------------------------------------------------
# parser = argparse.ArgumentParser(description='Deep Learning')
# parser.add_argument('--dataset', type=str, default='tiktok', help='netflix, tiktok, amazon')

# parser.add_argument('--data_path', nargs='?', default='/home/weiw/Code/MM/KDMM/data/', help='Input data path.')  # /home/weiw/Code/MM/MICRO2Ours/data/     /home/weiw/Datasets/MM/LATTICE/    /home/weiw/Code/MM/KDMM/data/
# parser.add_argument('--Ks', nargs='?', default='[10, 20, 40, 50]', help='K value of ndcg/recall @ k')
# parser.add_argument('--seed', type=int, default=2022, help='Random seed')
# parser.add_argument('--verbose', type=int, default=5, help='Interval of evaluation.')
# parser.add_argument('--sparse', type=int, default=1, help='Sparse or dense adjacency matrix')   
# parser.add_argument('--debug', action='store_true')  
# parser.add_argument('--test_flag', nargs='?', default='part', help='Specify the test type from {part, full}, indicating whether the reference is done in mini-batch')
# parser.add_argument('--ssl_c_rate', type=float, default=None, help='ssl_c_rate')
# parser.add_argument('--ssl_s_rate', type=float, default=None, help='ssl_s_rate')
# parser.add_argument('--sample_num', default=None, type=int, help='sample_num') 
# parser.add_argument('--sample_num_neg', default=None, type=int, help='sample_num') 
# parser.add_argument('--sample_num_ii', default=None, type=int, help='sample_num') 
# parser.add_argument('--anchor_rate', default=None, type=float, help='anchor_rate') 
# parser.add_argument('--ad_topk_multi_num', type=int, default=None, help='ad topk')  
# parser.add_argument('--head_num', default=None, type=int, help='head_num_of_multihead_attention. For multi-model relation.')  #
# parser.add_argument('--point', default='ours', type=str, help='point')  

# # train
# parser.add_argument('--batch_size', type=int, default=1024, help='Batch size.')
# parser.add_argument('--epoch', type=int, default=1000, help='Number of epoch.')  #default: 1000
# parser.add_argument('--cf_model', nargs='?', default='light_init', help='Downstream Collaborative Filtering model {mf, ngcf, lightgcn, vbpr, hafr}')   
# parser.add_argument('--early_stopping_patience', type=int, default=8, help='') 
# parser.add_argument('--gpu_id', type=int, default=2, help='GPU id')
# parser.add_argument('--regs', nargs='?', default='[1e-5,1e-5,1e-2]', help='Regularizations.')  #default: '[1e-5,1e-5,1e-2]'
# parser.add_argument('--emb_reg', default=1e-7, type=float, help='weight decay regularizer')
# #teacher
# parser.add_argument('--model_cat_rate', type=float, default=0.028, help='model_cat_rate') #[0.2, 0.001, 0.1, 0.022, 0.028]
# parser.add_argument('--weight_size', nargs='?', default='[64, 64]', help='Output sizes of every layer')  #default: '[64, 64]'
# parser.add_argument('--embed_size', type=int, default=32, help='Embedding size.')  #    
# parser.add_argument('--drop_rate', type=float, default=0.4, help='dropout rate')
# parser.add_argument('--t_weight_decay', type=float, default=0.001, help='T_weight_decay')
# parser.add_argument('--lr', type=float, default=0.0011, help='Learning rate.')
# parser.add_argument('--teacher_reg_rate', type=float, default=1, help='')  # 
# parser.add_argument('--t_feat_mf_rate', type=float, default=0.001, help='model_cat_rate')
# parser.add_argument('--feat_reg_decay', default=1e-5, type=float, help='feat_reg_decay') 
# parser.add_argument('--layers', type=int, default=1, help='Number of item graph conv layers')  
# parser.add_argument('--mess_dropout', nargs='?', default='[0.1, 0.1]', help='Keep probability w.r.t. message dropout (i.e., 1-dropout_ratio) for each deep layer. 1: no dropout.')
# # kd
# parser.add_argument('--student_embed_size', type=int, default=32, help='Embedding size.')  # 16, 32        
# parser.add_argument('--student_lr', type=float, default=0.002, help='Learning rate.')  #0.002 0.001, 0.00001 
# parser.add_argument('--student_reg_rate', type=float, default=1, help='')  # 
# parser.add_argument('--student_n_layers', type=int, default=1, help='Number of item graph conv layers')  
# parser.add_argument('--student_tau', type=float, default=5, help='Learning rate.')  #0.002 0.001, 0.00001    
# parser.add_argument('--neg_sample_num', type=int, default=10, help='Learning rate.')  # 1,5,10
# parser.add_argument('--list_wise_loss_rate', type=float, default=1, help='Learning rate.')  # 0,1,8,9,10 
# parser.add_argument('--if_train_teacher', default=True, type=bool, help='')
# parser.add_argument('--kd_loss_rate', default=0.01, type=float, help='')  # 500000
# parser.add_argument('--kd_loss_image_rate', default=500000, type=float, help='')  #
# parser.add_argument('--kd_loss_text_rate', default=500000, type=float, help='')  #
# parser.add_argument('--kd_loss_list_rate', default=0.01, type=float, help='')  #1000000
# parser.add_argument('--student_drop_rate', type=float, default=0.2, help='dropout rate')
# parser.add_argument('--student_model_type', type=str, default='lightgcn', help='')  
# parser.add_argument('--kd_loss_feat_rate', type=float, default=0.1, help='dropout rate')
# parser.add_argument("--alpha_l", type=float, default=2, help="`pow`inddex for `sce` loss")
# parser.add_argument("--tip_rate_feat", type=float, default=0, help="")  #0.2 ! ^ ~    
# parser.add_argument('--feat_loss_type', type=str, default='sce') # mse, sce   
# # prompt
# parser.add_argument('--hard_token_type', type=str, default='pca', help='pca, ica, isomap, tsne, lda')
# parser.add_argument('--soft_token_rate', default=0.1, type=float, help='')  # 0.0001 0.001, 0.00012
# parser.add_argument('--feat_soft_token_rate', default=9, type=float, help='')  # 0.0001 0.001, 0.00012, 0.05
# parser.add_argument('--t_prompt_rate1', default=10000000000, type=float, help='')  #
# parser.add_argument('--t_prompt_rate2', default=1000, type=float, help='')  #
# parser.add_argument('--t_prompt_rate3', default=1, type=float, help='')  #
# parser.add_argument('--prompt_dropout', default=0, type=float, help='')  #
# # 
# parser.add_argument('--decouple_alpha', default=100, type=float, help='')  #
# parser.add_argument('--decouple_beta', default=1, type=float, help='')  #
# parser.add_argument('--decouple_t', default=1, type=float, help='')  #

# args = parser.parse_args()
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#---tiktok-----------------------------------------------------------------------------------------------------------------------------------------------------------------------



#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#---amazon-----------------------------------------------------------------------------------------------------------------------------------------------------------------------
# parser = argparse.ArgumentParser(description='Deep Learning')
# # 基础配置
# parser.add_argument('--dataset', type=str, default='amazon', help='netflix, tiktok, amazon')
# parser.add_argument('--data_path', nargs='?', default='/home/weiw/Code/MM/KDMM/data/', help='Input data path.')  # /home/weiw/Code/MM/MICRO2Ours/data/     /home/weiw/Datasets/MM/LATTICE/    /home/weiw/Code/MM/KDMM/data/
# parser.add_argument('--Ks', nargs='?', default='[10, 20, 40, 50]', help='K value of ndcg/recall @ k')
# parser.add_argument('--seed', type=int, default=2022, help='Random seed')
# parser.add_argument('--verbose', type=int, default=5, help='Interval of evaluation.')
# parser.add_argument('--sparse', type=int, default=1, help='Sparse or dense adjacency matrix')   
# parser.add_argument('--debug', action='store_true')  
# parser.add_argument('--test_flag', nargs='?', default='part', help='Specify the test type from {part, full}, indicating whether the reference is done in mini-batch')
# parser.add_argument('--ssl_c_rate', type=float, default=None, help='ssl_c_rate')
# parser.add_argument('--ssl_s_rate', type=float, default=None, help='ssl_s_rate')
# parser.add_argument('--sample_num', default=None, type=int, help='sample_num') 
# parser.add_argument('--sample_num_neg', default=None, type=int, help='sample_num') 
# parser.add_argument('--sample_num_ii', default=None, type=int, help='sample_num') 
# parser.add_argument('--anchor_rate', default=None, type=float, help='anchor_rate') 
# parser.add_argument('--ad_topk_multi_num', type=int, default=None, help='ad topk')  
# parser.add_argument('--head_num', default=None, type=int, help='head_num_of_multihead_attention. For multi-model relation.')  #
# parser.add_argument('--point', default='', type=str, help='point')  

# # 训练配置
# parser.add_argument('--batch_size', type=int, default=512, help='Batch size.')
# parser.add_argument('--epoch', type=int, default=1000, help='Number of epoch.')  #default: 1000
# parser.add_argument('--cf_model', nargs='?', default='light_init', help='Downstream Collaborative Filtering model {mf, ngcf, lightgcn, vbpr, hafr}')   
# parser.add_argument('--early_stopping_patience', type=int, default=8, help='') 
# parser.add_argument('--gpu_id', type=int, default=2, help='GPU id')
# parser.add_argument('--regs', nargs='?', default='[1e-5,1e-5,1e-2]', help='Regularizations.')  #default: '[1e-5,1e-5,1e-2]'
# parser.add_argument('--emb_reg', default=1e-7, type=float, help='weight decay regularizer')

# # 教师模型参数
# parser.add_argument('--model_cat_rate', type=float, default=0.8, help='model_cat_rate')
# parser.add_argument('--weight_size', nargs='?', default='[64,64,64]', help='Output sizes of every layer')  #default: '[64, 64]'
# parser.add_argument('--embed_size', type=int, default=32, help='Embedding size.')  #    
# parser.add_argument('--drop_rate', type=float, default=0.6, help='dropout rate')
# parser.add_argument('--t_weight_decay', type=float, default=0.001, help='T_weight_decay')
# parser.add_argument('--lr', type=float, default=0.001, help='Learning rate.')
# parser.add_argument('--teacher_reg_rate', type=float, default=1, help='')  # 
# parser.add_argument('--t_feat_mf_rate', type=float, default=0, help='model_cat_rate')
# parser.add_argument('--feat_reg_decay', default=1e-5, type=float, help='feat_reg_decay') 
# parser.add_argument('--layers', type=int, default=1, help='Number of item graph conv layers')  
# parser.add_argument('--mess_dropout', nargs='?', default='[0.1, 0.1]', help='Keep probability w.r.t. message dropout (i.e., 1-dropout_ratio) for each deep layer. 1: no dropout.')

# # 蒸馏与学生模型参数
# parser.add_argument('--student_embed_size', type=int, default=32, help='Embedding size.')  # 16, 32        
# parser.add_argument('--student_lr', type=float, default=0.00002, help='Learning rate.')  #0.002 0.001, 0.00001 
# parser.add_argument('--student_reg_rate', type=float, default=1, help='')  # 
# parser.add_argument('--student_n_layers', type=int, default=1, help='Number of item graph conv layers')  
# parser.add_argument('--student_tau', type=float, default=5, help='Learning rate.')  #0.002 0.001, 0.00001    
# parser.add_argument('--neg_sample_num', type=int, default=10, help='Learning rate.')  # 1,5,10
# parser.add_argument('--list_wise_loss_rate', type=float, default=1, help='Learning rate.')  # 0,1,8,9,10 
# parser.add_argument('--if_train_teacher', default=True , type=bool, help='')
# parser.add_argument('--kd_loss_rate', default=1000000, type=float, help='')  #
# parser.add_argument('--kd_loss_image_rate', default=500000, type=float, help='')  #
# parser.add_argument('--kd_loss_text_rate', default=500000, type=float, help='')  #
# parser.add_argument('--kd_loss_list_rate', default=1000000, type=float, help='')  #
# parser.add_argument('--student_drop_rate', type=float, default=0.2, help='dropout rate')
# parser.add_argument('--student_model_type', type=str, default='lightgcn', help='')    
# parser.add_argument('--kd_loss_feat_rate', type=float, default=0.1, help='dropout rate')
# parser.add_argument("--alpha_l", type=float, default=2, help="`pow`inddex for `sce` loss")
# parser.add_argument("--tip_rate_feat", type=float, default=0, help="")  #0.2 ! ^ ~    
# parser.add_argument('--feat_loss_type', type=str, default='sce') # mse, sce

# # Prompt 参数
# parser.add_argument('--hard_token_type', type=str, default='pca', help='pca, ica, isomap, tsne, lda')
# parser.add_argument('--soft_token_rate', default=0.01, type=float, help='')  # 0.0001 0.001, 0.00012
# parser.add_argument('--feat_soft_token_rate', default=0.07, type=float, help='')  # 0.0001 0.001, 0.00012, 0.05
# parser.add_argument('--t_prompt_rate1', default=70, type=float, help='')  #
# parser.add_argument('--t_prompt_rate2', default=1, type=float, help='')  #
# parser.add_argument('--t_prompt_rate3', default=1, type=float, help='')  #
# parser.add_argument('--prompt_dropout', default=0, type=float, help='')  #
# # 
# parser.add_argument('--decouple_alpha', default=100, type=float, help='')  #
# parser.add_argument('--decouple_beta', default=1, type=float, help='')  #
# parser.add_argument('--decouple_t', default=1, type=float, help='')  #


# args = parser.parse_args()
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#---amazon-----------------------------------------------------------------------------------------------------------------------------------------------------------------------





def select_dataset():
    pass


# def select_dataset():
    
#     if args.dataset == 'netflix':
#         # train
#         args.regs = '[1e-5,1e-5,1e-2]'
#         args.batch_size = 1024
#         args.epoch = 1000
#         args.cf_model = 'light_init'
#         args.early_stopping_patience = 7
#         args.emb_reg = 1e-7
#         # teacher
#         args.model_cat_rate = 0.55
#         args.weight_size = '[64, 64]'
#         args.embed_size = 32
#         args.drop_rate = 0.2
#         args.lr = 0.0005
#         args.teacher_reg_rate = 1
#         args.t_feat_mf_rate = 1
#         args.feat_reg_decay = 1e-5
#         args.layers = 1
#         args.mess_dropout = '[0.1, 0.1]'

#         # kd
#         args.student_embed_size = 32
#         args.student_lr = 0.002
#         args.student_reg_rate = 1
#         args.student_n_layers = 1
#         args.student_tau = 5
#         args.neg_sample_num = 10
#         args.list_wise_loss_rate = 1
#         args.if_train_teacher = True
#         args.kd_loss_rate = 500000
#         args.kd_loss_image_rate = 500000
#         args.kd_loss_text_rate = 500000
#         args.kd_loss_list_rate = 1000000
#         args.student_drop_rate = 0.2
#         args.student_model_type = 'lightgcn'


#         # prompt
#         args.hard_token_type = 'pca' # ['pca']
#         args.soft_token_rate = 10
#         args.t_prompt_rate1 = 1
#         args.t_prompt_rate2 = 1
#         args.t_prompt_rate3 = 1

#         # gnn

#     elif args.dataset == 'tiktok':


        # #train
        # args.regs = '[1e-5,1e-5,1e-2]'
        # args.batch_size = 512
        # args.epoch = 1000
        # args.cf_model = 'mmgcn'
        # args.early_stopping_patience = 7
        # args.emb_reg = 1e-7


        # #teacher
        # args.model_cat_rate = 0.2
        # args.weight_size = '[64, 64, 64]'
        # args.embed_size = 32
        # args.lr = 0.0009
        # args.drop_rate = 0.2
        # args.teacher_reg_rate = 1
        # args.t_feat_mf_rate = 1
        # args.feat_reg_decay = 1e-5
        # args.layers = 1
        # args.mess_dropout = '[0.1, 0.1]'

        # # kd
        # args.student_embed_size = 32
        # args.student_lr = 0.002
        # args.student_reg_rate = 1
        # args.student_n_layers = 1
        # args.student_tau = 5
        # args.neg_sample_num = 10
        # args.list_wise_loss_rate = 1
        # args.if_train_teacher = True
        # args.kd_loss_rate = 500000
        # args.kd_loss_image_rate = 500000
        # args.kd_loss_text_rate = 500000
        # args.kd_loss_list_rate = 1000000
        # args.student_drop_rate = 0.2
        # args.student_model_type = 'gcn'

        # # promtpt
        # args.hard_token_type = 'pca'
        # args.soft_token_rate = 0.002 #[0.01]
        # args.t_prompt_rate1 = 10000000000
        # args.t_prompt_rate2 = 1000
        # args.t_prompt_rate3 = 1

    # elif args.dataset == 'amazon':

    #     # train
    #     args.regs = '[1e-5,1e-5,1e-2]'
    #     args.batch_size = 1024
    #     args.epoch = 1000
    #     args.cf_model = 'light_init'
    #     args.early_stopping_patience = 7
    #     args.emb_reg = 1e-7


    #     # teacher
    #     args.model_cat_rate = 0.8
    #     args.weight_size = '[64, 64]'
    #     args.embed_size = 32
    #     args.drop_rate = 0.2
    #     args.lr = 0.0005
    #     args.teacher_reg_rate = 1
    #     args.t_feat_mf_rate = 1
    #     args.feat_reg_decay = 1e-5
    #     args.layers = 1
    #     args.mess_dropout = '[0.1, 0.1]'

    #     # kd
    #     args.student_embed_size = 32
    #     args.student_lr = 0.002
    #     args.student_reg_rate = 1
    #     args.student_n_layers = 1
    #     args.student_tau = 5
    #     args.neg_sample_num = 10
    #     args.list_wise_loss_rate = 1
    #     args.if_train_teacher = True
    #     args.kd_loss_rate = 1000000
    #     args.kd_loss_image_rate = 500000
    #     args.kd_loss_text_rate = 500000
    #     args.kd_loss_list_rate = 1000000
    #     args.student_drop_rate = 0.2
    #     args.student_model_type = 'gcn'

    #     # prompt
    #     args.hard_token_type = 'pca'
    #     args.soft_token_rate = 0.1
    #     args.t_prompt_rate1 = 1
    #     args.t_prompt_rate2 = 1
    #     args.t_prompt_rate3 = 1

    # else:
    #     raise ValueError('Invalid dataset name')
    







# parser.add_argument('--Ks', nargs='?', default='[10, 20, 40, 50]', help='K value of ndcg/recall @ k')
# parser.add_argument('--data_path', nargs='?', default='/home/weiw/Code/MM/KDMM/data/', help='Input data path.')  # /home/weiw/Code/MM/MICRO2Ours/data/     /home/weiw/Datasets/MM/LATTICE/    /home/weiw/Code/MM/KDMM/data/
# parser.add_argument('--batch_size', type=int, default=1024, help='Batch size.')
# # parser.add_argument('--data_path', nargs='?', default='/home/weiw/Code/MM/KDMM/data/', help='Input data path.')  #/home/weiw/Code/MM/MICRO2Ours/data/   /home/weiw/Code/MM/KDMM/data/
# parser.add_argument('--seed', type=int, default=2022, help='Random seed')
# # parser.add_argument('--dataset', nargs='?', default='tiktok', help='Choose a dataset from {sports, baby, clothing, tiktok, allrecipes}')
# parser.add_argument('--verbose', type=int, default=5, help='Interval of evaluation.')
# parser.add_argument('--epoch', type=int, default=1000, help='Number of epoch.')  #default: 1000
# # parser.add_argument('--batch_size', type=int, default=1024, help='Batch size.')
# parser.add_argument('--cf_model', nargs='?', default='mmgcn', help='Downstream Collaborative Filtering model {mf, ngcf, lightgcn, vbpr, hafr}')   
# parser.add_argument('--early_stopping_patience', type=int, default=7, help='') 
# parser.add_argument('--gpu_id', type=int, default=2, help='GPU id')

# parser.add_argument('--core', type=int, default=5, help='5-core for warm-start; 0-core for cold start')
# parser.add_argument('--topk', type=int, default=10, help='K value of k-NN sparsification')  
# parser.add_argument('--lambda_coeff', type=float, default=0.9, help='Lambda value of skip connection')
# parser.add_argument('--sparse', type=int, default=1, help='Sparse or dense adjacency matrix')   
# parser.add_argument('--debug', action='store_true')  
# parser.add_argument('--cl_rate', type=float, default=0.03, help='Control the effect of the contrastive auxiliary task')        
# parser.add_argument('--norm_type', nargs='?', default='sym', help='Adjacency matrix normalization operation') 
# parser.add_argument('--test_flag', nargs='?', default='part', help='Specify the test type from {part, full}, indicating whether the reference is done in mini-batch')

# parser.add_argument('--metapath_threshold', default=2, type=int, help='metapath_threshold') 
# parser.add_argument('--sc', type=float, default=1.0, help='GCN self connection')
# parser.add_argument('--ssl_c_rate', type=float, default=1.3, help='ssl_c_rate')
# parser.add_argument('--ssl_s_rate', type=float, default=0.8, help='ssl_s_rate')
# parser.add_argument('--g_rate', type=float, default=0.000029, help='ssl_s_rate')
# parser.add_argument('--sample_num', default=1, type=int, help='sample_num') 
# parser.add_argument('--sample_num_neg', default=1, type=int, help='sample_num') 
# parser.add_argument('--sample_num_ii', default=8, type=int, help='sample_num') 
# parser.add_argument('--sample_num_co', default=2, type=int, help='sample_num') 
# parser.add_argument('--mask_rate', default=0.75, type=float, help='sample_num') 
# parser.add_argument('--gss_rate', default=0.85, type=float, help='gene_self_subgraph_rate') 
# parser.add_argument('--anchor_rate', default=0.75, type=float, help='anchor_rate') 
# parser.add_argument('--ad1_rate', default=0.2, type=float, help='ad1_rate') 
# parser.add_argument('--ad2_rate', default=0.2, type=float, help='ad1_rate') 
# parser.add_argument('--ad_sampNum', type=int, default=1, help='ad topk')  
# parser.add_argument('--ad_topk_multi_num', type=int, default=100, help='ad topk')  
# parser.add_argument('--fake_gene_rate', default=0.0001, type=float, help='fake_gene_rate') 
# parser.add_argument('--ID_layers', type=int, default=1, help='Number of item graph conv layers')  
# parser.add_argument('--reward_rate', default=1, type=float, help='fake_gene_rate') 
# parser.add_argument('--G_embed_size', type=int, default=64, help='Embedding size.')   
# parser.add_argument('--model_num', default=2, type=float, help='fake_gene_rate') 
# parser.add_argument('--negrate', default=0.01, type=float, help='item_neg_sample_rate')
# parser.add_argument('--cis', default=25, type=int, help='') 
# parser.add_argument('--confidence', default=0.5, type=float, help='') 

# parser.add_argument('--ii_it', default=15, type=int, help='') 
# parser.add_argument('--weight_decay', default=1e-4, type=float, help='')  #
# parser.add_argument('--L2_alpha', default=1e-3, type=float, help='')  #
# parser.add_argument('--emm', default=1e-3, type=float, help='')  #
# parser.add_argument('--isload', default=False , type=bool, help='whether load model')  #布尔值加引号...直接编译为True
# parser.add_argument('--isJustTest', default=False , type=bool, help='whether load model')
# parser.add_argument('--loadModelPath', default='/home/ww/Code/work3/BSTRec/Model/retailrocket/for_meta_hidden_dim_dim__8_retailrocket_2021_07_10__18_35_32_lr_0.0003_reg_0.01_batch_size_1024_gnn_layer_[16,16,16].pth', type=str, help='loadModelPath')
# parser.add_argument('--title', default="try_to_draw_line", type=str, help='')  #

# #teacher
# parser.add_argument('--model_cat_rate', type=float, default=0.2, help='model_cat_rate')
# parser.add_argument('--weight_size', nargs='?', default='[64, 64, 64]', help='Output sizes of every layer')  #default: '[64, 64]'
# parser.add_argument('--embed_size', type=int, default=32, help='Embedding size.')  #    
# parser.add_argument('--drop_rate', type=float, default=0.2, help='dropout rate')
# parser.add_argument('--lr', type=float, default=0.0009, help='Learning rate.')
# parser.add_argument('--teacher_reg_rate', type=float, default=1, help='')  # 
# parser.add_argument('--t_feat_mf_rate', type=float, default=1, help='model_cat_rate')
# parser.add_argument('--feat_reg_decay', default=1e-5, type=float, help='feat_reg_decay') 
# parser.add_argument('--layers', type=int, default=1, help='Number of item graph conv layers')  
# parser.add_argument('--mess_dropout', nargs='?', default='[0.1, 0.1]', help='Keep probability w.r.t. message dropout (i.e., 1-dropout_ratio) for each deep layer. 1: no dropout.')
# parser.add_argument('--regs', nargs='?', default='[1e-5,1e-5,1e-2]', help='Regularizations.')  #default: '[1e-5,1e-5,1e-2]'

# # kd
# parser.add_argument('--student_embed_size', type=int, default=32, help='Embedding size.')  # 16, 32        
# parser.add_argument('--student_lr', type=float, default=0.002, help='Learning rate.')  #0.002 0.001, 0.00001 
# parser.add_argument('--student_reg_rate', type=float, default=1, help='')  # 
# parser.add_argument('--student_n_layers', type=int, default=1, help='Number of item graph conv layers')  
# parser.add_argument('--student_tau', type=float, default=5, help='Learning rate.')  #0.002 0.001, 0.00001    
# parser.add_argument('--neg_sample_num', type=int, default=10, help='Learning rate.')  # 1,5,10
# parser.add_argument('--list_wise_loss_rate', type=float, default=1, help='Learning rate.')  # 0,1,8,9,10 
# parser.add_argument('--if_train_teacher', default=False , type=bool, help='')
# parser.add_argument('--kd_loss_rate', default=500000, type=float, help='')  #
# parser.add_argument('--kd_loss_image_rate', default=500000, type=float, help='')  #
# parser.add_argument('--kd_loss_text_rate', default=500000, type=float, help='')  #
# parser.add_argument('--kd_loss_list_rate', default=1000000, type=float, help='')  #
# parser.add_argument('--student_drop_rate', type=float, default=0.2, help='dropout rate')
# parser.add_argument('--student_model_type', type=str, default='lightgcn', help='')     
# parser.add_argument('--emb_reg', default=1e-7, type=float, help='weight decay regularizer')

# # prompt
# parser.add_argument('--hard_token_type', type=str, default='pca', help='pca, ica, isomap, tsne, lda')
# parser.add_argument('--soft_token_rate', default=0.002, type=float, help='')  # 0.0001 0.001, 0.00012
# parser.add_argument('--t_prompt_rate1', default=10000000000, type=float, help='')  #
# parser.add_argument('--t_prompt_rate2', default=1000, type=float, help='')  #
# parser.add_argument('--t_prompt_rate3', default=1, type=float, help='')  #
 
# #GNN
# parser.add_argument('--id_cat_rate', type=float, default=0.36, help='before GNNs')
# parser.add_argument('--id_cat_rate1', type=float, default=0.36, help='id_cat_rate')
# parser.add_argument('--head_num', default=4, type=int, help='head_num_of_multihead_attention. For multi-model relation.')  #


# train 
# parser.add_argument('--D_lr', type=float, default=3e-4, help='Learning rate.')
# #GAN
# parser.add_argument('--G_rate', default=0.0018, type=float, help='for D model1')  #
# parser.add_argument('--G_drop1', default=0.31, type=float, help='for D model2')  #
# parser.add_argument('--G_drop2', default=0.5, type=float, help='')  #
# parser.add_argument('--gp_rate', default=1, type=float, help='gradient penal')  #
# parser.add_argument('--real_data_tau', default=0.002, type=float, help='for real_data soft')  #
# parser.add_argument('--ui_pre_scale', default=100, type=int, help='ui_pre_scale')  
# parser.add_argument('--log_log_scale', default=0.00001, type=int, help='log_log_scale')  
# #cl
# parser.add_argument('--T', default=1, type=int, help='it for ui update')  
# parser.add_argument('--tau', default=0.5, type=float, help='')  #
# parser.add_argument('--geneGraph_rate', default=0.1, type=float, help='')  #
# parser.add_argument('--geneGraph_rate_pos', default=2, type=float, help='')  #
# parser.add_argument('--geneGraph_rate_neg', default=-1, type=float, help='')  #     
# parser.add_argument('--m_topk_rate', default=0.01, type=float, help='for reconstruct')  #0.022
# parser.add_argument('--point', default='', type=str, help='point')  






    # if args.dataset == 'netflix':
    #     # parser.add_argument('--data_path', nargs='?', default='/home/weiw/Code/MM/KDMM/data/', help='Input data path.')  # /home/weiw/Code/MM/MICRO2Ours/data/     /home/weiw/Datasets/MM/LATTICE/    /home/weiw/Code/MM/KDMM/data/
    #     parser.add_argument('--seed', type=int, default=2022,
    #                         help='Random seed')
    #     # parser.add_argument('--dataset', nargs='?', default='netflix',
    #     #                     help='Choose a dataset from {sports, baby, clothing, tiktok, allrecipes}')
    #     parser.add_argument('--verbose', type=int, default=5,
    #                         help='Interval of evaluation.')
    #     parser.add_argument('--epoch', type=int, default=1000,
    #                         help='Number of epoch.')  #default: 1000
    #     # parser.add_argument('--batch_size', type=int, default=1024,
    #                         # help='Batch size.')
    #     parser.add_argument('--regs', nargs='?', default='[1e-5,1e-5,1e-2]',
    #                         help='Regularizations.')  #default: '[1e-5,1e-5,1e-2]'
    #     parser.add_argument('--lr', type=float, default=0.0005,
    #                         help='Learning rate.')
    #     parser.add_argument('--D_lr', type=float, default=3e-4, help='Learning rate.')

    #     parser.add_argument('--embed_size', type=int, default=32,
    #                         help='Embedding size.')                     
    #     parser.add_argument('--weight_size', nargs='?', default='[64, 64]',
    #                         help='Output sizes of every layer')  #default: '[64, 64]'
    #     parser.add_argument('--core', type=int, default=5,
    #                         help='5-core for warm-start; 0-core for cold start')
    #     parser.add_argument('--topk', type=int, default=10, help='K value of k-NN sparsification')  
    #     parser.add_argument('--lambda_coeff', type=float, default=0.9,
    #                         help='Lambda value of skip connection')
    #     parser.add_argument('--cf_model', nargs='?', default='light_init',
    #                         help='Downstream Collaborative Filtering model {mf, ngcf, lightgcn, vbpr, hafr, ngcf_init, light_init}')   #light_init
    #     parser.add_argument('--early_stopping_patience', type=int, default=7,
    #                         help='') 
    #     parser.add_argument('--layers', type=int, default=1,
    #                         help='Number of item graph conv layers')  
    #     parser.add_argument('--mess_dropout', nargs='?', default='[0.1, 0.1]',
    #                         help='Keep probability w.r.t. message dropout (i.e., 1-dropout_ratio) for each deep layer. 1: no dropout.')

    #     parser.add_argument('--sparse', type=int, default=1, help='Sparse or dense adjacency matrix')   
    #     parser.add_argument('--debug', action='store_true')  
    #     parser.add_argument('--cl_rate', type=float, default=0.03, help='Control the effect of the contrastive auxiliary task')        
    #     parser.add_argument('--norm_type', nargs='?', default='sym', help='Adjacency matrix normalization operation') 
    #     parser.add_argument('--gpu_id', type=int, default=2, help='GPU id')
    #     # parser.add_argument('--Ks', nargs='?', default='[10, 20, 40, 50]', help='K value of ndcg/recall @ k')
    #     parser.add_argument('--test_flag', nargs='?', default='part',
    #                         help='Specify the test type from {part, full}, indicating whether the reference is done in mini-batch')

    #     parser.add_argument('--metapath_threshold', default=2, type=int, help='metapath_threshold') 
    #     parser.add_argument('--sc', type=float, default=1.0, help='GCN self connection')
    #     parser.add_argument('--drop_rate', type=float, default=0.2, help='dropout rate')
    #     parser.add_argument('--model_cat_rate', type=float, default=0.55, help='model_cat_rate')
    #     parser.add_argument('--ssl_c_rate', type=float, default=1.3, help='ssl_c_rate')
    #     parser.add_argument('--ssl_s_rate', type=float, default=0.8, help='ssl_s_rate')
    #     parser.add_argument('--g_rate', type=float, default=0.000029, help='ssl_s_rate')
    #     parser.add_argument('--sample_num', default=1, type=int, help='sample_num') 
    #     parser.add_argument('--sample_num_neg', default=1, type=int, help='sample_num') 
    #     parser.add_argument('--sample_num_ii', default=8, type=int, help='sample_num') 
    #     parser.add_argument('--sample_num_co', default=2, type=int, help='sample_num') 
    #     parser.add_argument('--mask_rate', default=0.75, type=float, help='sample_num') 
    #     parser.add_argument('--gss_rate', default=0.85, type=float, help='gene_self_subgraph_rate') 
    #     parser.add_argument('--anchor_rate', default=0.75, type=float, help='anchor_rate') 
    #     parser.add_argument('--feat_reg_decay', default=1e-5, type=float, help='feat_reg_decay') 
    #     parser.add_argument('--ad1_rate', default=0.2, type=float, help='ad1_rate') 
    #     parser.add_argument('--ad2_rate', default=0.2, type=float, help='ad1_rate') 
    #     parser.add_argument('--ad_sampNum', type=int, default=1, help='ad topk')  
    #     parser.add_argument('--ad_topk_multi_num', type=int, default=100, help='ad topk')  
    #     parser.add_argument('--fake_gene_rate', default=0.0001, type=float, help='fake_gene_rate') 
    #     parser.add_argument('--ID_layers', type=int, default=1, help='Number of item graph conv layers')  
    #     parser.add_argument('--reward_rate', default=1, type=float, help='fake_gene_rate') 
    #     parser.add_argument('--G_embed_size', type=int, default=32, help='Embedding size.')   
    #     parser.add_argument('--model_num', default=2, type=float, help='fake_gene_rate') 
    #     parser.add_argument('--negrate', default=0.01, type=float, help='item_neg_sample_rate')
    #     parser.add_argument('--cis', default=25, type=int, help='') 
    #     parser.add_argument('--confidence', default=0.5, type=float, help='') 
    #     parser.add_argument('--tau', default=0.5, type=float, help='')  #
    #     parser.add_argument('--geneGraph_rate', default=0.1, type=float, help='')  #
    #     parser.add_argument('--geneGraph_rate_pos', default=2, type=float, help='')  #
    #     parser.add_argument('--geneGraph_rate_neg', default=-1, type=float, help='')  #     

    #     parser.add_argument('--G_rate', default=0.0001, type=float, help='')  #
    #     parser.add_argument('--G_drop1', default=0.31, type=float, help='')  #
    #     parser.add_argument('--G_drop2', default=0.5, type=float, help='')  #
    #     parser.add_argument('--gp_rate', default=1, type=float, help='')  #
    #     parser.add_argument('--real_data_tau', default=0.002, type=float, help='')  #
    #     parser.add_argument('--L2_alpha', default=1e-3, type=float, help='')  #
    #     parser.add_argument('--emm', default=1.1e-3, type=float, help='')  #
    #     parser.add_argument('--isload', default=False , type=bool, help='whether load model')  #布尔值加引号...直接编译为True
    #     parser.add_argument('--isJustTest', default=False , type=bool, help='whether load model')
    #     parser.add_argument('--loadModelPath', default='/home/ww/Code/work3/BSTRec/Model/retailrocket/for_meta_hidden_dim_dim__8_retailrocket_2021_07_10__18_35_32_lr_0.0003_reg_0.01_batch_size_1024_gnn_layer_[16,16,16].pth', type=str, help='loadModelPath')
    #     parser.add_argument('--title', default="try_to_draw_line", type=str, help='')  #
    #     parser.add_argument('--head_num', default=4, type=int, help='head_num_of_multihead_attention')  #
    #     parser.add_argument('--id_cat_rate', type=float, default=0.36, help='id_cat_rate')
    #     parser.add_argument('--id_cat_rate1', type=float, default=0.36, help='id_cat_rate')
    #     parser.add_argument('--T', default=2, type=int, help='it for ui update')  
    #     parser.add_argument('--m_topk_rate', default=0.02, type=float, help='it for ui update')
    #     parser.add_argument('--point', default='', type=str, help='point')  

    #     # kd
    #     parser.add_argument('--kd_loss_rate', default=500000, type=float, help='')  #
    #     parser.add_argument('--student_embed_size', type=int, default=32, help='Embedding size.')  # 16, 32        
    #     parser.add_argument('--student_lr', type=float, default=0.002, help='Learning rate.')  #0.002 0.001, 0.00001   
    #     parser.add_argument('--student_n_layers', type=int, default=1, help='Number of item graph conv layers')  # 1, 2, 3, 4
    #     parser.add_argument('--student_tau', type=float, default=5, help='Learning rate.')  #0.002 0.001, 0.00001  
    #     parser.add_argument('--kd_loss_image_rate', default=500000, type=float, help='')  #
    #     parser.add_argument('--kd_loss_text_rate', default=500000, type=float, help='')  #     
                

    # elif args.dataset == 'tiktok':
        # # parser.add_argument('--data_path', nargs='?', default='/home/weiw/Code/MM/KDMM/data/', help='Input data path.')  #/home/weiw/Code/MM/MICRO2Ours/data/   /home/weiw/Code/MM/KDMM/data/
        # parser.add_argument('--seed', type=int, default=2022, help='Random seed')
        # # parser.add_argument('--dataset', nargs='?', default='tiktok', help='Choose a dataset from {sports, baby, clothing, tiktok, allrecipes}')
        # parser.add_argument('--verbose', type=int, default=5, help='Interval of evaluation.')
        # parser.add_argument('--epoch', type=int, default=1000, help='Number of epoch.')  #default: 1000
        # # parser.add_argument('--batch_size', type=int, default=1024, help='Batch size.')
        # parser.add_argument('--regs', nargs='?', default='[1e-5,1e-5,1e-2]', help='Regularizations.')  #default: '[1e-5,1e-5,1e-2]'
        # parser.add_argument('--D_lr', type=float, default=3e-4, help='Learning rate.')

        # parser.add_argument('--embed_size', type=int, default=32, help='Embedding size.')  #    
        # parser.add_argument('--core', type=int, default=5, help='5-core for warm-start; 0-core for cold start')
        # parser.add_argument('--topk', type=int, default=10, help='K value of k-NN sparsification')  
        # parser.add_argument('--lambda_coeff', type=float, default=0.9, help='Lambda value of skip connection')
        # parser.add_argument('--cf_model', nargs='?', default='mmgcn', help='Downstream Collaborative Filtering model {mf, ngcf, lightgcn, vbpr, hafr}')   
        # parser.add_argument('--early_stopping_patience', type=int, default=7, help='') 
        # parser.add_argument('--layers', type=int, default=1, help='Number of item graph conv layers')  
        # parser.add_argument('--mess_dropout', nargs='?', default='[0.1, 0.1]', help='Keep probability w.r.t. message dropout (i.e., 1-dropout_ratio) for each deep layer. 1: no dropout.')

        # parser.add_argument('--sparse', type=int, default=1, help='Sparse or dense adjacency matrix')   
        # parser.add_argument('--debug', action='store_true')  
        # parser.add_argument('--cl_rate', type=float, default=0.03, help='Control the effect of the contrastive auxiliary task')        
        # parser.add_argument('--norm_type', nargs='?', default='sym', help='Adjacency matrix normalization operation') 
        # parser.add_argument('--gpu_id', type=int, default=2, help='GPU id')
        # # parser.add_argument('--Ks', nargs='?', default='[10, 20, 40, 50]', help='K value of ndcg/recall @ k')
        # parser.add_argument('--test_flag', nargs='?', default='part', help='Specify the test type from {part, full}, indicating whether the reference is done in mini-batch')

        # parser.add_argument('--metapath_threshold', default=2, type=int, help='metapath_threshold') 
        # parser.add_argument('--sc', type=float, default=1.0, help='GCN self connection')
        # parser.add_argument('--ssl_c_rate', type=float, default=1.3, help='ssl_c_rate')
        # parser.add_argument('--ssl_s_rate', type=float, default=0.8, help='ssl_s_rate')
        # parser.add_argument('--g_rate', type=float, default=0.000029, help='ssl_s_rate')
        # parser.add_argument('--sample_num', default=1, type=int, help='sample_num') 
        # parser.add_argument('--sample_num_neg', default=1, type=int, help='sample_num') 
        # parser.add_argument('--sample_num_ii', default=8, type=int, help='sample_num') 
        # parser.add_argument('--sample_num_co', default=2, type=int, help='sample_num') 
        # parser.add_argument('--mask_rate', default=0.75, type=float, help='sample_num') 
        # parser.add_argument('--gss_rate', default=0.85, type=float, help='gene_self_subgraph_rate') 
        # parser.add_argument('--anchor_rate', default=0.75, type=float, help='anchor_rate') 
        # parser.add_argument('--ad1_rate', default=0.2, type=float, help='ad1_rate') 
        # parser.add_argument('--ad2_rate', default=0.2, type=float, help='ad1_rate') 
        # parser.add_argument('--ad_sampNum', type=int, default=1, help='ad topk')  
        # parser.add_argument('--ad_topk_multi_num', type=int, default=100, help='ad topk')  
        # parser.add_argument('--fake_gene_rate', default=0.0001, type=float, help='fake_gene_rate') 
        # parser.add_argument('--ID_layers', type=int, default=1, help='Number of item graph conv layers')  
        # parser.add_argument('--reward_rate', default=1, type=float, help='fake_gene_rate') 
        # # parser.add_argument('--G_embed_size', type=int, default=64, help='Embedding size.')   
        # parser.add_argument('--model_num', default=2, type=float, help='fake_gene_rate') 
        # parser.add_argument('--negrate', default=0.01, type=float, help='item_neg_sample_rate')
        # parser.add_argument('--cis', default=25, type=int, help='') 
        # parser.add_argument('--confidence', default=0.5, type=float, help='') 

        # parser.add_argument('--ii_it', default=15, type=int, help='') 
        # parser.add_argument('--L2_alpha', default=1e-3, type=float, help='')  #
        # parser.add_argument('--emm', default=1e-3, type=float, help='')  #
        # parser.add_argument('--isload', default=False , type=bool, help='whether load model')  #布尔值加引号...直接编译为True
        # parser.add_argument('--isJustTest', default=False , type=bool, help='whether load model')
        # parser.add_argument('--loadModelPath', default='/home/ww/Code/work3/BSTRec/Model/retailrocket/for_meta_hidden_dim_dim__8_retailrocket_2021_07_10__18_35_32_lr_0.0003_reg_0.01_batch_size_1024_gnn_layer_[16,16,16].pth', type=str, help='loadModelPath')
        # parser.add_argument('--title', default="try_to_draw_line", type=str, help='')  #

        # #GNN
        # parser.add_argument('--id_cat_rate', type=float, default=0.36, help='before GNNs')
        # parser.add_argument('--id_cat_rate1', type=float, default=0.36, help='id_cat_rate')
        # parser.add_argument('--head_num', default=4, type=int, help='head_num_of_multihead_attention. For multi-model relation.')  #


        # #GAN
        # parser.add_argument('--G_rate', default=0.0018, type=float, help='for D model1')  #
        # parser.add_argument('--G_drop1', default=0.31, type=float, help='for D model2')  #
        # parser.add_argument('--G_drop2', default=0.5, type=float, help='')  #
        # parser.add_argument('--gp_rate', default=1, type=float, help='gradient penal')  #

        # parser.add_argument('--real_data_tau', default=0.002, type=float, help='for real_data soft')  #
        # parser.add_argument('--ui_pre_scale', default=100, type=int, help='ui_pre_scale')  
        # parser.add_argument('--log_log_scale', default=0.00001, type=int, help='log_log_scale')  


        # #cl
        # parser.add_argument('--T', default=1, type=int, help='it for ui update')  
        # parser.add_argument('--tau', default=0.5, type=float, help='')  #
        # parser.add_argument('--geneGraph_rate', default=0.1, type=float, help='')  #
        # parser.add_argument('--geneGraph_rate_pos', default=2, type=float, help='')  #
        # parser.add_argument('--geneGraph_rate_neg', default=-1, type=float, help='')  #     
        # parser.add_argument('--m_topk_rate', default=0.01, type=float, help='for reconstruct')  #0.022
        # parser.add_argument('--point', default='', type=str, help='point')  


        # #teacher
        # parser.add_argument('--model_cat_rate', type=float, default=0.2, help='model_cat_rate')
        # parser.add_argument('--weight_size', nargs='?', default='[64, 64, 64]', help='Output sizes of every layer')  #default: '[64, 64]'
        # parser.add_argument('--drop_rate', type=float, default=0.2, help='dropout rate')
        # parser.add_argument('--lr', type=float, default=0.0009, help='Learning rate.')
        # parser.add_argument('--teacher_reg_rate', type=float, default=1, help='')  # 
        # parser.add_argument('--t_feat_mf_rate', type=float, default=1, help='model_cat_rate')
        # parser.add_argument('--feat_reg_decay', default=1e-5, type=float, help='feat_reg_decay') 


        # # kd
        # parser.add_argument('--student_embed_size', type=int, default=32, help='Embedding size.')  # 16, 32        
        # parser.add_argument('--student_lr', type=float, default=0.002, help='Learning rate.')  #0.002 0.001, 0.00001 
        # parser.add_argument('--student_reg_rate', type=float, default=1, help='')  # 
        # parser.add_argument('--student_n_layers', type=int, default=1, help='Number of item graph conv layers')  
        # parser.add_argument('--student_tau', type=float, default=5, help='Learning rate.')  #0.002 0.001, 0.00001    
        # parser.add_argument('--neg_sample_num', type=int, default=10, help='Learning rate.')  # 1,5,10
        # parser.add_argument('--list_wise_loss_rate', type=float, default=1, help='Learning rate.')  # 0,1,8,9,10 
        # parser.add_argument('--if_train_teacher', default=False , type=bool, help='')
        # parser.add_argument('--kd_loss_rate', default=500000, type=float, help='')  #
        # parser.add_argument('--kd_loss_image_rate', default=500000, type=float, help='')  #
        # parser.add_argument('--kd_loss_text_rate', default=500000, type=float, help='')  #
        # parser.add_argument('--kd_loss_list_rate', default=1000000, type=float, help='')  #
        # parser.add_argument('--student_drop_rate', type=float, default=0.2, help='dropout rate')
        # parser.add_argument('--student_model_type', type=str, default='lightgcn', help='')     
        # parser.add_argument('--emb_reg', default=1e-7, type=float, help='weight decay regularizer')

        # # prompt
        # parser.add_argument('--hard_token_type', type=str, default='pca', help='pca, ica, isomap, tsne, lda')
        # parser.add_argument('--soft_token_rate', default=0.002, type=float, help='')  # 0.0001 0.001, 0.00012
        # parser.add_argument('--t_prompt_rate1', default=10000000000, type=float, help='')  #
        # parser.add_argument('--t_prompt_rate2', default=1000, type=float, help='')  #
        # parser.add_argument('--t_prompt_rate3', default=1, type=float, help='')  #
    
    # elif args.dataset == 'amazon':
    #     # parser.add_argument('--data_path', nargs='?', default='/home/weiw/Code/MM/KDMM/data/',
    #                         # help='Input data path.')  # /home/weiw/Code/MM/MICRO2Ours/data/     /home/weiw/Datasets/MM/LATTICE/    /home/weiw/Code/MM/KDMM/data/
    #     parser.add_argument('--seed', type=int, default=2022,
    #                         help='Random seed')
    #     # parser.add_argument('--dataset', nargs='?', default='sports', help='Choose a dataset from {sports, baby, clothing, tiktok, allrecipes}')
    #     parser.add_argument('--verbose', type=int, default=5,
    #                         help='Interval of evaluation.')
    #     parser.add_argument('--epoch', type=int, default=1000,
    #                         help='Number of epoch.')  #default: 1000
    #     # parser.add_argument('--batch_size', type=int, default=1024,
    #                         # help='Batch size.')
    #     parser.add_argument('--regs', nargs='?', default='[1e-5,1e-5,1e-2]',
    #                         help='Regularizations.')  #default: '[1e-5,1e-5,1e-2]'
    #     parser.add_argument('--D_lr', type=float, default=3e-4, help='Learning rate.')

    #     parser.add_argument('--embed_size', type=int, default=32,
    #                         help='Embedding size.')                     
    #     parser.add_argument('--core', type=int, default=5,
    #                         help='5-core for warm-start; 0-core for cold start')
    #     parser.add_argument('--topk', type=int, default=10, help='K value of k-NN sparsification')  
    #     parser.add_argument('--lambda_coeff', type=float, default=0.9,
    #                         help='Lambda value of skip connection')
    #     parser.add_argument('--cf_model', nargs='?', default='light_init',
    #                         help='Downstream Collaborative Filtering model {mf, ngcf, lightgcn, vbpr, hafr, ngcf_init, light_init}')   #light_init
    #     parser.add_argument('--early_stopping_patience', type=int, default=7,
    #                         help='') 
    #     parser.add_argument('--layers', type=int, default=1,
    #                         help='Number of item graph conv layers')  
    #     parser.add_argument('--mess_dropout', nargs='?', default='[0.1, 0.1]',
    #                         help='Keep probability w.r.t. message dropout (i.e., 1-dropout_ratio) for each deep layer. 1: no dropout.')

        # parser.add_argument('--sparse', type=int, default=1, help='Sparse or dense adjacency matrix')   
        # parser.add_argument('--debug', action='store_true')  
        # parser.add_argument('--cl_rate', type=float, default=0.03, help='Control the effect of the contrastive auxiliary task')        
        # parser.add_argument('--norm_type', nargs='?', default='sym', help='Adjacency matrix normalization operation') 
        # parser.add_argument('--gpu_id', type=int, default=2, help='GPU id')
        # # parser.add_argument('--Ks', nargs='?', default='[10, 20, 40, 50]', help='K value of ndcg/recall @ k')
        # parser.add_argument('--test_flag', nargs='?', default='part',
        #                     help='Specify the test type from {part, full}, indicating whether the reference is done in mini-batch')

        # parser.add_argument('--metapath_threshold', default=2, type=int, help='metapath_threshold') 
        # parser.add_argument('--sc', type=float, default=1.0, help='GCN self connection')
        # parser.add_argument('--ssl_c_rate', type=float, default=1.3, help='ssl_c_rate')
        # parser.add_argument('--ssl_s_rate', type=float, default=0.8, help='ssl_s_rate')
        # parser.add_argument('--g_rate', type=float, default=0.000029, help='ssl_s_rate')
        # parser.add_argument('--sample_num', default=1, type=int, help='sample_num') 
        # parser.add_argument('--sample_num_neg', default=1, type=int, help='sample_num') 
        # parser.add_argument('--sample_num_ii', default=8, type=int, help='sample_num') 
        # parser.add_argument('--sample_num_co', default=2, type=int, help='sample_num') 
        # parser.add_argument('--mask_rate', default=0.75, type=float, help='sample_num') 
        # parser.add_argument('--gss_rate', default=0.85, type=float, help='gene_self_subgraph_rate') 
        # parser.add_argument('--anchor_rate', default=0.75, type=float, help='anchor_rate') 
        # parser.add_argument('--feat_reg_decay', default=1e-5, type=float, help='feat_reg_decay') 
        # parser.add_argument('--ad1_rate', default=0.2, type=float, help='ad1_rate') 
        # parser.add_argument('--ad2_rate', default=0.2, type=float, help='ad1_rate') 
        # parser.add_argument('--ad_sampNum', type=int, default=1, help='ad topk')  
        # parser.add_argument('--ad_topk_multi_num', type=int, default=100, help='ad topk')  
        # parser.add_argument('--fake_gene_rate', default=0.0001, type=float, help='fake_gene_rate') 
        # parser.add_argument('--ID_layers', type=int, default=1, help='Number of item graph conv layers')  
        # parser.add_argument('--reward_rate', default=1, type=float, help='fake_gene_rate') 
        # parser.add_argument('--G_embed_size', type=int, default=32, help='Embedding size.')   
        # parser.add_argument('--model_num', default=2, type=float, help='fake_gene_rate') 
        # parser.add_argument('--negrate', default=0.01, type=float, help='item_neg_sample_rate')
        # parser.add_argument('--cis', default=25, type=int, help='') 
        # parser.add_argument('--confidence', default=0.5, type=float, help='') 
        # parser.add_argument('--tau', default=0.5, type=float, help='')  #
        # parser.add_argument('--geneGraph_rate', default=0.1, type=float, help='')  #
        # parser.add_argument('--geneGraph_rate_pos', default=2, type=float, help='')  #
        # parser.add_argument('--geneGraph_rate_neg', default=-1, type=float, help='')  #     

        # parser.add_argument('--ii_it', default=15, type=int, help='') 
        # parser.add_argument('--G_rate', default=0.0001, type=float, help='')  #
        # parser.add_argument('--G_drop1', default=0.31, type=float, help='')  #
        # parser.add_argument('--G_drop2', default=0.5, type=float, help='')  #
        # parser.add_argument('--gp_rate', default=1, type=float, help='')  #
        # parser.add_argument('--real_data_tau', default=0.002, type=float, help='')  #
        # parser.add_argument('--L2_alpha', default=1e-3, type=float, help='')  #
        # parser.add_argument('--emm', default=1.1e-3, type=float, help='')  #
        # parser.add_argument('--isload', default=False , type=bool, help='whether load model')  #布尔值加引号...直接编译为True
        # parser.add_argument('--isJustTest', default=False , type=bool, help='whether load model')
        # parser.add_argument('--loadModelPath', default='/home/ww/Code/work3/BSTRec/Model/retailrocket/for_meta_hidden_dim_dim__8_retailrocket_2021_07_10__18_35_32_lr_0.0003_reg_0.01_batch_size_1024_gnn_layer_[16,16,16].pth', type=str, help='loadModelPath')
        # parser.add_argument('--title', default="try_to_draw_line", type=str, help='')  #
        # parser.add_argument('--head_num', default=4, type=int, help='head_num_of_multihead_attention')  #
        # parser.add_argument('--id_cat_rate', type=float, default=0.36, help='id_cat_rate')
        # parser.add_argument('--id_cat_rate1', type=float, default=0.36, help='id_cat_rate')
        # parser.add_argument('--T', default=2, type=int, help='it for ui update')  
        # parser.add_argument('--m_topk_rate', default=0.02, type=float, help='it for ui update')
        # parser.add_argument('--point', default='', type=str, help='point')  

        # #teacher
        # parser.add_argument('--model_cat_rate', type=float, default=0.8, help='model_cat_rate')
        # parser.add_argument('--weight_size', nargs='?', default='[64, 64]', help='Output sizes of every layer')  #default: '[64, 64]'
        # parser.add_argument('--drop_rate', type=float, default=0.2, help='dropout rate')
        # parser.add_argument('--lr', type=float, default=0.0005, help='Learning rate.')
        # parser.add_argument('--teacher_reg_rate', type=float, default=1, help='')  # 
        # parser.add_argument('--t_feat_mf_rate', type=float, default=1, help='model_cat_rate')

        # # kd
        # parser.add_argument('--student_embed_size', type=int, default=32, help='Embedding size.')  # 16, 32        
        # parser.add_argument('--student_lr', type=float, default=0.002, help='Learning rate.')  #0.002 0.001, 0.00001 
        # parser.add_argument('--student_reg_rate', type=float, default=1, help='')  # 
        # parser.add_argument('--student_n_layers', type=int, default=1, help='Number of item graph conv layers')  
        # parser.add_argument('--student_tau', type=float, default=5, help='Learning rate.')  #0.002 0.001, 0.00001    
        # parser.add_argument('--neg_sample_num', type=int, default=10, help='Learning rate.')  # 1,5,10
        # parser.add_argument('--list_wise_loss_rate', type=float, default=1, help='Learning rate.')  # 0,1,8,9,10 
        # parser.add_argument('--if_train_teacher', default=True, type=bool, help='')
        # # parser.add_argument('--if_train_teacher', action='store_false')
        # parser.add_argument('--kd_loss_rate', default=1000000, type=float, help='')  #
        # parser.add_argument('--kd_loss_image_rate', default=500000, type=float, help='')  #
        # parser.add_argument('--kd_loss_text_rate', default=500000, type=float, help='')  #
        # parser.add_argument('--kd_loss_list_rate', default=1000000, type=float, help='')  #
        # parser.add_argument('--student_drop_rate', type=float, default=0.2, help='dropout rate')
        # # parser.add_argument('--student_model_type', nargs='?', default='lightgcn')
        # parser.add_argument('--student_model_type', type=str, default='mlp')
        # parser.add_argument('--emb_reg', default=1e-7, type=float, help='weight decay regularizer')

        # # prompt
        # parser.add_argument('--hard_token_type', type=str, default='pca', help='pca, ica, isomap, tsne, lda')
        # parser.add_argument('--soft_token_rate', default=1, type=float, help='')  #
        # parser.add_argument('--t_prompt_rate1', default=1, type=float, help='')  #
        # parser.add_argument('--t_prompt_rate2', default=1, type=float, help='')  #
        # parser.add_argument('--t_prompt_rate3', default=1, type=float, help='')  #


    # else:
    #     raise ValueError('Invalid dataset name')
