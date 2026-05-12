"""
    Author: AI Assistant
    Desc: 大语言模型接口抽象层 - 支持多种LLM接入
    Features:
        - 统一的LLM调用接口
        - 支持多种模型（ChatGLM、Qwen、通义千问API等）
        - 自动降级机制
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional
from dashscope import Generation
logger = logging.getLogger(__name__)


class LLMBase(ABC):
    """LLM基类"""

    @abstractmethod
    def generate(self, prompt: str, max_length: int = 1024, temperature: float = 0.7) -> str:
        """
        生成文本

        Args:
            prompt: 输入提示词
            max_length: 最大生成长度
            temperature: 温度参数（控制随机性）

        Returns:
            生成的文本
        """
        pass

    @abstractmethod
    def chat(self, messages: list, max_length: int = 1024, temperature: float = 0.7) -> str:
        """
        对话式生成

        Args:
            messages: 消息列表，格式为 [{"role": "user/assistant", "content": "..."}]
            max_length: 最大生成长度
            temperature: 温度参数

        Returns:
            生成的回复
        """
        pass


class ChatGLMLLM(LLMBase):
    """
    ChatGLM本地模型实现

    使用前需要安装：
    pip install transformers torch accelerate sentencepiece

    模型下载：
    from transformers import AutoModel, AutoTokenizer
    model = AutoModel.from_pretrained("THUDM/chatglm3-6b", trust_remote_code=True)
    tokenizer = AutoTokenizer.from_pretrained("THUDM/chatglm3-6b", trust_remote_code=True)
    """

    def __init__(self, model_path: str = "THUDM/chatglm3-6b", device: str = "auto"):
        """
        初始化ChatGLM模型

        Args:
            model_path: 模型路径或名称
            device: 运行设备（cpu/cuda/auto）
        """
        try:
            from transformers import AutoModel, AutoTokenizer
            import torch

            logger.info(f"正在加载ChatGLM模型: {model_path}")

            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True
            )

            if device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"

            self.model = AutoModel.from_pretrained(
                model_path,
                trust_remote_code=True
            ).to(device)

            self.model = self.model.eval()
            self.device = device

            logger.info(f"ChatGLM模型加载成功，运行在: {device}")

        except ImportError as e:
            error_msg = f"缺少依赖库: {e}，请运行: pip install transformers torch accelerate sentencepiece"
            logger.error(error_msg)
            raise ImportError(error_msg)
        except Exception as e:
            logger.error(f"ChatGLM模型加载失败: {e}")
            raise

    def generate(self, prompt: str, max_length: int = 1024, temperature: float = 0.7) -> str:
        """生成文本"""
        try:
            response, _ = self.model.chat(
                self.tokenizer,
                prompt,
                history=[],
                max_length=max_length,
                temperature=temperature
            )
            return response
        except Exception as e:
            logger.error(f"ChatGLM生成失败: {e}")
            return ""

    def chat(self, messages: list, max_length: int = 1024, temperature: float = 0.7) -> str:
        """对话式生成"""
        try:
            # 转换消息格式为ChatGLM的history格式
            history = []
            for msg in messages[:-1]:
                if msg["role"] == "user":
                    history.append((msg["content"], ""))
                elif msg["role"] == "assistant" and history:
                    history[-1] = (history[-1][0], msg["content"])

            current_prompt = messages[-1]["content"] if messages else ""

            response, _ = self.model.chat(
                self.tokenizer,
                current_prompt,
                history=history,
                max_length=max_length,
                temperature=temperature
            )
            return response
        except Exception as e:
            logger.error(f"ChatGLM对话失败: {e}")
            return ""


class QwenLLM(LLMBase):
    """
    通义千问本地模型实现

    使用前需要安装：
    pip install transformers torch accelerate tiktoken

    模型下载：
    from transformers import AutoModelForCausalLM, AutoTokenizer
    model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen-7B-Chat", trust_remote_code=True)
    """

    def __init__(self, model_path: str = "Qwen/Qwen-7B-Chat", device: str = "auto"):
        """
        初始化Qwen模型

        Args:
            model_path: 模型路径或名称
            device: 运行设备
        """
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch

            logger.info(f"正在加载Qwen模型: {model_path}")

            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True
            )

            if device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"

            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                trust_remote_code=True,
                device_map="auto" if device == "cuda" else None
            )

            if device != "cuda":
                self.model = self.model.to(device)

            self.model = self.model.eval()
            self.device = device

            logger.info(f"Qwen模型加载成功，运行在: {device}")

        except ImportError as e:
            error_msg = f"缺少依赖库: {e}，请运行: pip install transformers torch accelerate tiktoken"
            logger.error(error_msg)
            raise ImportError(error_msg)
        except Exception as e:
            logger.error(f"Qwen模型加载失败: {e}")
            raise

    def generate(self, prompt: str, max_length: int = 1024, temperature: float = 0.7) -> str:
        """生成文本"""
        try:
            response, history = self.model.chat(
                self.tokenizer,
                prompt,
                history=None,
                max_length=max_length,
                temperature=temperature
            )
            return response
        except Exception as e:
            logger.error(f"Qwen生成失败: {e}")
            return ""

    def chat(self, messages: list, max_length: int = 1024, temperature: float = 0.7) -> str:
        """对话式生成"""
        try:
            # 构建完整的对话历史
            history = []
            for msg in messages[:-1]:
                role = "USER" if msg["role"] == "user" else "ASSISTANT"
                history.append((msg["content"], "" if role == "USER" else msg["content"]))

            current_prompt = messages[-1]["content"] if messages else ""

            response, _ = self.model.chat(
                self.tokenizer,
                current_prompt,
                history=history,
                max_length=max_length,
                temperature=temperature
            )
            return response
        except Exception as e:
            logger.error(f"Qwen对话失败: {e}")
            return ""


class DashScopeLLM(LLMBase):
    """
    阿里云通义千问API实现（无需本地GPU）

    使用前需要：
    1. 注册阿里云账号并开通DashScope服务
    2. 获取API Key
    3. 安装SDK: pip install dashscope
    """

    def __init__(self, api_key: str, model_name: str = "qwen-turbo"):
        """
        初始化DashScope API

        Args:
            api_key: 阿里云API Key
            model_name: 模型名称（qwen-turbo/qwen-plus/qwen-max）
        """
        try:
            import dashscope
            dashscope.api_key = api_key

            self.model_name = model_name
            self.api_key = api_key

            logger.info(f"DashScope API初始化成功，使用模型: {model_name}")

        except ImportError:
            error_msg = "未安装dashscope库，请运行: pip install dashscope"
            logger.error(error_msg)
            raise ImportError(error_msg)
        except Exception as e:
            logger.error(f"DashScope API初始化失败: {e}")
            raise

    def generate(self, prompt: str, max_length: int = 1024, temperature: float = 0.7) -> str:
        """生成文本"""
        try:
            response = Generation.call(
                model=self.model_name,
                prompt=prompt,
                max_tokens=max_length,
                temperature=temperature
            )

            if response.status_code == 200:
                return response.output.text
            else:
                logger.error(f"DashScope API调用失败: {response.message}")
                return ""

        except Exception as e:
            logger.error(f"DashScope生成失败: {e}")
            return ""

    def chat(self, messages: list, max_length: int = 1024, temperature: float = 0.7) -> str:
        """对话式生成"""
        try:
            from dashscope import Generation

            # 转换消息格式
            dashscope_messages = []
            for msg in messages:
                dashscope_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            response = Generation.call(
                model=self.model_name,
                messages=dashscope_messages,
                max_tokens=max_length,
                temperature=temperature
            )

            if response.status_code == 200:
                return response.output.text
            else:
                logger.error(f"DashScope API调用失败: {response.message}")
                return ""

        except Exception as e:
            logger.error(f"DashScope对话失败: {e}")
            return ""


class ZhipuAILLM(LLMBase):
    """
    智谱AI GLM API实现

    使用前需要：
    1. 注册智谱AI账号并获取API Key
    2. 安装SDK: pip install zhipuai
    """

    def __init__(self, api_key: str, model_name: str = "glm-4"):
        """
        初始化智谱AI API

        Args:
            api_key: 智谱AI API Key
            model_name: 模型名称（glm-4/glm-3-turbo）
        """
        try:
            from zhipuai import ZhipuAI

            self.client = ZhipuAI(api_key=api_key)
            self.model_name = model_name

            logger.info(f"智谱AI API初始化成功，使用模型: {model_name}")

        except ImportError:
            error_msg = "未安装zhipuai库，请运行: pip install zhipuai"
            logger.error(error_msg)
            raise ImportError(error_msg)
        except Exception as e:
            logger.error(f"智谱AI API初始化失败: {e}")
            raise

    def generate(self, prompt: str, max_length: int = 1024, temperature: float = 0.7) -> str:
        """生成文本"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_length,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"智谱AI生成失败: {e}")
            return ""

    def chat(self, messages: list, max_length: int = 1024, temperature: float = 0.7) -> str:
        """对话式生成"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_length,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"智谱AI对话失败: {e}")
            return ""


class FallbackLLM(LLMBase):
    """
    降级LLM实现（当其他模型不可用时使用）
    使用规则-based方法生成答案
    """

    def __init__(self):
        logger.warning("使用降级LLM（规则-based），答案质量可能较低")

    def generate(self, prompt: str, max_length: int = 1024, temperature: float = 0.7) -> str:
        """使用规则生成简单答案"""
        return self._rule_based_answer(prompt)

    def chat(self, messages: list, max_length: int = 1024, temperature: float = 0.7) -> str:
        """使用规则生成简单答案"""
        if messages:
            return self._rule_based_answer(messages[-1]["content"])
        return ""

    def _rule_based_answer(self, question: str) -> str:
        """基于规则的简单答案生成"""
        return f"抱歉，当前无法连接到智能模型。关于您的问题：{question[:50]}...，建议您查阅相关新闻原文获取详细信息。"


def create_llm(llm_type: str = "fallback", **kwargs) -> LLMBase:
    """
    工厂函数：创建LLM实例

    Args:
        llm_type: LLM类型
            - "chatglm": ChatGLM本地模型
            - "qwen": 通义千问本地模型
            - "dashscope": 阿里云通义千问API
            - "zhipuai": 智谱AI API
            - "fallback": 降级方案（规则-based）
        **kwargs: 其他参数

    Returns:
        LLM实例
    """
    llm_registry = {
        "chatglm": ChatGLMLLM,
        "qwen": QwenLLM,
        "dashscope": DashScopeLLM,
        "zhipuai": ZhipuAILLM,
        "fallback": FallbackLLM
    }

    llm_class = llm_registry.get(llm_type.lower())

    if not llm_class:
        logger.warning(f"未知的LLM类型: {llm_type}，使用降级方案")
        return FallbackLLM()

    try:
        return llm_class(**kwargs)
    except Exception as e:
        logger.error(f"创建LLM实例失败: {e}，使用降级方案")
        return FallbackLLM()
