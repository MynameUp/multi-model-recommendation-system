""" Author: AI Assistant Desc: LLM配置文件 """
#LLM配置
LLM_CONFIG = {
# 默认LLM类型 "default_type": "fallback",
# ChatGLM配置
"chatglm": {
    "model_path": "THUDM/chatglm3-6b",  # 模型路径
    "device": "auto"  # cpu/cuda/auto
},

# Qwen配置
"qwen": {
    "model_path": "Qwen/Qwen-7B-Chat",
    "device": "auto"
},

# 阿里云DashScope配置
"dashscope": {
    "api_key": "",  # 在这里填写你的API Key
    "model_name": "qwen-turbo"  # qwen-turbo/qwen-plus/qwen-max
},

# 智谱AI配置
"zhipuai": {
    "api_key": "",  # 在这里填写你的API Key
    "model_name": "glm-4"  # glm-4/glm-3-turbo
}
}
#问答配置
QA_CONFIG = { "max_context_length": 4000, # 最大上下文长度
              "max_answer_length": 512, # 最大答案长度
              "temperature": 0.7, # 温度参数
              "top_k_related_news": 5, # 返回的相关新闻数量
              "enable_qa_history": True # 是否启用问答历史
            }