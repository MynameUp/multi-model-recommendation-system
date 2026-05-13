"""
    Author: AI Assistant
    Desc: LLM配置文件 - 仅支持魔塔社区API

    使用说明：
        1. 填写魔塔社区的 API Token
        2. 选择合适的模型
        3. DEFAULT_LLM_TYPE 固定为 "modelscope"
"""

# ==================== 全局配置 ====================
# 默认使用的LLM类型（固定为魔塔社区）
DEFAULT_LLM_TYPE = "modelscope"

# 是否启用自动降级（当魔塔社区API失败时自动切换到fallback）
ENABLE_AUTO_FALLBACK = True


# ==================== 魔塔社区（ModelScope）配置 ====================
MODELSCOPE_CONFIG = {
    # API Token（请确保已替换为真实Token）
    "api_token": "ms-7e6bbbc2-b6d0-485c-b366-45d2a0e5c70b",

    # 可用的对话模型列表（基于魔塔社区模型库截图）
    "models": {
        # # 通义千问 Qwen3 系列（强烈推荐）
        # "qwen3-8b": "Qwen/Qwen3-8B",  # ⭐ 首选：最新、速度快、中文好
        # "qwen3-35b": "Qwen/Qwen3.5-35B-A3B",  # 更强性能
        # "qwen3-27b": "Qwen/Qwen3.5-27B",  # 平衡性能
        #
        # # DeepSeek 系列（推荐）
        # "deepseek-v4-flash": "deepseek-ai/DeepSeek-V4-Flash",  # 速度快
        # "deepseek-v4-pro": "deepseek-ai/DeepSeek-V4-Pro",  # 专业版

        # 智谱AI 系列
        "glm-5.1": "ZhipuAI/GLM-5.1",  # 智谱最新模型
    },

    # 默认使用的模型（使用唯一可用的GLM-5.1）
    "default_model": "ZhipuAI/GLM-5.1",

    # 调用参数
    "generation_params": {
        "max_length": 1024,  # 最大生成长度
        "temperature": 0.7,  # 温度参数（0-1，越高越随机）
        "top_p": 0.8,  # 核采样参数
        "repetition_penalty": 1.1,  # 重复惩罚
    }
}

# ==================== 问答系统配置 ====================
QA_CONFIG = {
    # 上下文控制
    "max_context_length": 4000,  # 最大上下文长度（字符数）
    "max_answer_length": 512,  # 最大答案长度（字符数）

    # 生成参数
    "temperature": 0.7,  # 温度参数（0-1）
    "top_k_related_news": 5,  # 返回的相关新闻数量

    # 功能开关
    "enable_qa_history": True,  # 是否启用问答历史记录
    "enable_rag": True,  # 是否启用RAG检索增强

    # 降级策略
    "fallback_enabled": True,  # 是否启用降级机制
    "fallback_timeout": 10,  # 超时时间（秒）
}


def get_llm_config(llm_type=None):
    """
    获取指定LLM类型的配置

    Args:
        llm_type: LLM类型（仅支持 modelscope 或 fallback）

    Returns:
        tuple: (llm_type, config_dict)
    """
    if llm_type is None:
        llm_type = DEFAULT_LLM_TYPE

    if llm_type.lower() == "modelscope":
        return llm_type, MODELSCOPE_CONFIG
    else:
        return llm_type, {}


def get_qa_config():
    """获取问答系统配置"""
    return QA_CONFIG

def print_config_status():
    """打印配置状态（用于调试）"""
    print("\n" + "=" * 60)
    print("ModelScope Configuration Status")
    print("=" * 60)

    token = MODELSCOPE_CONFIG.get('api_token', '')
    if not token or token == 'your_modelscope_token_here':
        print("[ERROR] Token: Not configured")
    elif len(token) < 10:
        print(f"[ERROR] Token: Invalid format (length: {len(token)})")
    else:
        masked = token[:5] + "..." + token[-5:]
        print(f"[OK] Token: {masked}")

    print(f"[INFO] Default Model: {MODELSCOPE_CONFIG.get('default_model')}")
    print(f"[INFO] Auto Fallback: {'Enabled' if ENABLE_AUTO_FALLBACK else 'Disabled'}")
    print("=" * 60 + "\n")

