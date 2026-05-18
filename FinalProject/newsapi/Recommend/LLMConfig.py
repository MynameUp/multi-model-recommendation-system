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
DEFAULT_LLM_TYPE = "dashscope"

# 是否启用自动降级（当魔塔社区API失败时自动切换到fallback）
ENABLE_AUTO_FALLBACK = True

# ==================== 阿里云百炼（DashScope）配置 ====================
DASHSCOPE_CONFIG = {
    # API Key（阿里云百炼）
    # 获取方式：https://bailian.console.aliyun.com/ → API-KEY管理
    "api_key": "sk-9ff50721101548e3aac9e06497a5438e",

    # 可用的对话模型列表
    "models": {
        "qwen3-vl-thinking": "qwen3-vl-235b-a22b-thinking",  # 视觉语言模型，超强推理（默认）
        "qwen-math-turbo": "qwen-math-turbo",  # 数学推理专用，适合计算和逻辑
        "qwen-plus": "qwen-plus",  # 高性价比，适合大多数场景
        "qwen-max": "qwen-max",  # 最强性能，适合复杂任务
        "qwen-turbo": "qwen-turbo",  # 速度快，成本低
        "qwen-long": "qwen-long",  # 支持超长上下文（128K）
    },

    # 默认使用的模型（使用qwen3-vl-235b-a22b-thinking）
    "default_model": "qwen3-vl-235b-a22b-thinking",

    # 调用参数
    "generation_params": {
        "max_tokens": 2000,  # 最大生成长度（思考型模型需要更长输出）
        "temperature": 0.7,  # 温度参数（0-1，越高越随机）
        "top_p": 0.8,  # 核采样参数
        "enable_thinking": True,  # 启用思考模式（如果支持）
    },

    # API端点（OpenAI兼容接口）
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
}

# ==================== 魔塔社区（ModelScope）配置 ====================
MODELSCOPE_CONFIG = {
    # API Token（请确保已替换为真实Token）
    "api_token": "",

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
        llm_type: LLM类型（支持 dashscope, modelscope 或 fallback）

    Returns:
        tuple: (llm_type, config_dict)
    """
    if llm_type is None:
        llm_type = DEFAULT_LLM_TYPE

    if llm_type.lower() == "dashscope":
        return llm_type, DASHSCOPE_CONFIG
    elif llm_type.lower() == "modelscope":
        return llm_type, MODELSCOPE_CONFIG
    else:
        return llm_type, {}


def get_qa_config():
    """获取问答系统配置"""
    return QA_CONFIG

def print_config_status():
    """打印配置状态（用于调试）"""
    print("\n" + "=" * 60)
    print("LLM Configuration Status")
    print("=" * 60)

    print(f"\n[DEFAULT] LLM Type: {DEFAULT_LLM_TYPE}")
    print(f"[DEFAULT] Auto Fallback: {'Enabled' if ENABLE_AUTO_FALLBACK else 'Disabled'}")

    # 显示阿里云百炼配置状态
    print("\n--- DashScope (阿里云百炼) ---")
    api_key = DASHSCOPE_CONFIG.get('api_key', '')
    if not api_key or api_key == 'sk-your-dashscope-api-key-here':
        print("[WARN] API Key: Not configured")
    elif len(api_key) < 10:
        print(f"[ERROR] API Key: Invalid format (length: {len(api_key)})")
    else:
        masked = api_key[:8] + "..." + api_key[-4:]
        print(f"[OK] API Key: {masked}")
    print(f"[INFO] Default Model: {DASHSCOPE_CONFIG.get('default_model')}")

    # 显示魔塔社区配置状态
    print("\n--- ModelScope (魔塔社区) ---")
    token = MODELSCOPE_CONFIG.get('api_token', '')
    if not token or token == 'your_modelscope_token_here':
        print("[WARN] Token: Not configured")
    elif len(token) < 10:
        print(f"[ERROR] Token: Invalid format (length: {len(token)})")
    else:
        masked = token[:5] + "..." + token[-5:]
        print(f"[OK] Token: {masked}")
    print(f"[INFO] Default Model: {MODELSCOPE_CONFIG.get('default_model')}")

    print("\n" + "=" * 60 + "\n")

