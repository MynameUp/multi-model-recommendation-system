"""
    Desc: 大语言模型接口抽象层 - 支持阿里云百炼和魔塔社区API
    Features:
        - 统一的LLM调用接口
        - 默认使用阿里云百炼API（DashScope）
        - 支持魔塔社区API（备用方案）
        - 自动降级机制
        - 支持流式输出
        - 原生messages格式支持

    支持的LLM类型：
        - "dashscope": 阿里云百炼API（默认，推荐）
        - "modelscope": 魔塔社区API（备用）
        - "fallback": 降级方案（规则-based）
"""
import logging
import requests
import json
from abc import ABC, abstractmethod
from typing import Optional, Generator

from Recommend.LLMConfig import MODELSCOPE_CONFIG, DASHSCOPE_CONFIG

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
            messages: 消息列表，格式为 [{"role": "user/assistant/system", "content": "..."}]
            max_length: 最大生成长度
            temperature: 温度参数

        Returns:
            生成的回复
        """
        pass

    def chat_stream(self, messages: list, max_length: int = 1024, temperature: float = 0.7) -> Generator[str, None, None]:
        """
        流式对话生成（可选实现）

        Args:
            messages: 消息列表
            max_length: 最大生成长度
            temperature: 温度参数

        Yields:
            逐块生成的文本
        """
        raise NotImplementedError("流式输出未在此LLM中实现")


class DashScopeLLM(LLMBase):
    """
    阿里云百炼（DashScope）API实现 - 使用OpenAI兼容接口

    阿里云百炼是阿里云提供的大模型服务平台，支持通义千问系列模型。

    优势：
        - 国内访问稳定，速度快
        - OpenAI API标准兼容，易于迁移
        - 通义千问系列模型中文能力强
        - 支持多种模型（qwen-plus, qwen-max, qwen-turbo等）
        - 无需本地GPU，无需下载模型
        - 原生支持messages格式和流式输出
        - 提供丰富的API功能（联网搜索、函数调用等）

    使用前需要：
        1. 注册阿里云账号: https://www.aliyun.com/
        2. 开通百炼服务: https://bailian.console.aliyun.com/
        3. 创建API-KEY（API-KEY管理 → 创建API-KEY）
        4. 安装OpenAI SDK: pip install openai

    支持的模型：
        - qwen-plus（推荐）：平衡性能和成本
        - qwen-max：最强性能，适合复杂任务
        - qwen-turbo：速度快，成本低
        - qwen-long：支持超长上下文（128K）
    """

    def __init__(self, api_key: str, model_name: str = "qwen-plus"):
        """
        初始化阿里云百炼API（OpenAI兼容接口）

        Args:
            api_key: 阿里云百炼 API Key
            model_name: 模型名称（如 qwen-plus, qwen-max, qwen-turbo）
        """
        try:
            from openai import OpenAI

            self.api_key = api_key
            self.model_name = model_name
            self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

            # 验证API Key是否有效
            if not api_key or api_key == 'sk-your-dashscope-api-key-here':
                logger.warning("未提供有效的阿里云百炼API Key，将使用降级方案")
                raise ValueError("Invalid API key")

            # 初始化OpenAI客户端（使用阿里云百炼的OpenAI兼容接口）
            self.client = OpenAI(
                api_key=api_key,
                base_url=self.base_url
            )

            logger.info(f"阿里云百炼API初始化成功（OpenAI兼容接口）")
            logger.info(f"使用模型: {model_name}")
            logger.info(f"API端点: {self.base_url}")

        except ImportError:
            logger.error("未安装openai库，请运行: pip install openai")
            raise
        except Exception as e:
            logger.error(f"阿里云百炼API初始化失败: {e}")
            raise

    def generate(self, prompt: str, max_length: int = 1024, temperature: float = 0.7) -> str:
        """
        生成文本（兼容旧接口，内部转换为messages格式）

        Args:
            prompt: 输入提示词
            max_length: 最大生成长度
            temperature: 温度参数

        Returns:
            生成的文本
        """
        try:
            # 将prompt转换为messages格式
            messages = [
                {"role": "user", "content": prompt}
            ]

            # 调用chat方法
            return self.chat(messages, max_length, temperature)

        except Exception as e:
            logger.error(f"阿里云百炼生成失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return ""

    def chat(self, messages: list, max_length: int = 1024, temperature: float = 0.7) -> str:
        """
        对话式生成（使用OpenAI兼容接口）

        Args:
            messages: 消息列表，格式为 [{"role": "user/assistant/system", "content": "..."}]
            max_length: 最大生成长度
            temperature: 温度参数

        Returns:
            生成的回复
        """
        try:
            logger.info(f"调用阿里云百炼API，模型: {self.model_name}")

            # 第一次尝试
            response = self._make_api_call(messages, max_length, temperature)

            # 检查响应是否有效
            if response and len(response.strip()) > 10:
                logger.info(f"阿里云百炼API调用成功，生成长度: {len(response)}")
                return response

            # 如果第一次返回空，尝试重试一次
            logger.warning("第一次调用返回空响应，尝试重试...")
            response = self._make_api_call(messages, max_length, temperature)

            if response and len(response.strip()) > 10:
                logger.info(f"重试成功，生成长度: {len(response)}")
                return response

            logger.error("两次调用都返回空响应")
            return ""

        except Exception as e:
            logger.error(f"阿里云百炼对话失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return ""

    def _make_api_call(self, messages: list, max_length: int, temperature: float) -> str:
        """执行单次API调用"""
        try:
            # 调用OpenAI兼容接口
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_length,
                temperature=temperature,
                top_p=0.8,
                stream=False
            )

            # 详细记录响应
            logger.debug(f"API响应对象: {response}")
            logger.debug(f"Choices: {response.choices}")

            # 提取生成的文本
            if response.choices and len(response.choices) > 0:
                choice = response.choices[0]
                logger.debug(f"Choice: {choice}")

                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    generated_text = choice.message.content
                    if generated_text:
                        return generated_text
                    else:
                        logger.warning("Content字段为空")
                        return ""
                else:
                    logger.error(f"Choice结构异常: {choice}")
                    return ""
            else:
                logger.error("API返回空choices")
                return ""

        except Exception as e:
            logger.error(f"API调用异常: {e}")
            raise

    def chat_stream(self, messages: list, max_length: int = 1024, temperature: float = 0.7) -> Generator[str, None, None]:
        """
        流式对话生成（实时输出）

        Args:
            messages: 消息列表
            max_length: 最大生成长度
            temperature: 温度参数

        Yields:
            逐块生成的文本片段
        """
        try:
            logger.info(f"调用阿里云百炼API（流式），模型: {self.model_name}")

            # 调用流式接口
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_length,
                temperature=temperature,
                top_p=0.8,
                stream=True  # 启用流式模式
            )

            # 逐块返回生成的文本
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta_content = chunk.choices[0].delta.content
                    if delta_content:
                        yield delta_content

        except Exception as e:
            logger.error(f"阿里云百炼流式对话失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            yield ""


class ModelScopeLLM(LLMBase):
    """
    魔塔社区（ModelScope）API实现 - 使用OpenAI兼容接口

    使用官方推荐的OpenAI SDK调用方式，无需本地GPU或下载模型

    优势：
        - 国内访问稳定，无SSL问题
        - OpenAI API标准兼容，易于迁移
        - 丰富的模型选择（Qwen、ChatGLM等）
        - 免费额度充足
        - 无需本地GPU，无需下载模型
        - 原生支持messages格式和流式输出

    使用前需要：
        1. 注册魔塔社区账号: https://modelscope.cn/
        2. 获取 API Token（个人中心 → Access Token）
        3. 确保网络可以访问 modelscope.cn
        4. 安装OpenAI SDK: pip install openai

    支持的模型（完整列表见魔塔社区）：
        - qwen/Qwen-7B-Chat（推荐，平衡性能）
        - qwen/Qwen-14B-Chat（更强性能）
        - qwen/Qwen-72B-Chat（最强性能）
        - ZhipuAI/chatglm3-6b
        - Qwen/Qwen2.5-Coder-32B-Instruct（代码专用）
    """

    def __init__(self, api_token: str, model_name: str = "qwen/Qwen-7B-Chat"):
        """
        初始化魔塔社区API（OpenAI兼容接口）

        Args:
            api_token: 魔塔社区 API Token
            model_name: 模型名称（完整路径，如 qwen/Qwen-7B-Chat）
        """
        try:
            from openai import OpenAI

            self.api_token = api_token
            self.model_name = model_name

            # 验证Token是否有效
            if not api_token or api_token == 'your_modelscope_token_here':
                logger.warning("未提供有效的魔塔社区Token，将使用降级方案")
                raise ValueError("Invalid API token")

            # 初始化OpenAI客户端（使用魔塔社区的OpenAI兼容接口）
            self.client = OpenAI(
                api_key=api_token,
                base_url="https://api-inference.modelscope.cn/v1/"
            )

            logger.info(f"魔塔社区API初始化成功（OpenAI兼容接口）")
            logger.info(f"使用模型: {model_name}")
            logger.info(f"API端点: https://api-inference.modelscope.cn/v1/")

        except ImportError:
            logger.error("未安装openai库，请运行: pip install openai")
            raise
        except Exception as e:
            logger.error(f"魔塔社区API初始化失败: {e}")
            raise

    def generate(self, prompt: str, max_length: int = 1024, temperature: float = 0.7) -> str:
        """
        生成文本（兼容旧接口，内部转换为messages格式）

        Args:
            prompt: 输入提示词
            max_length: 最大生成长度
            temperature: 温度参数

        Returns:
            生成的文本
        """
        try:
            # 将prompt转换为messages格式
            messages = [
                {"role": "user", "content": prompt}
            ]

            # 调用chat方法
            return self.chat(messages, max_length, temperature)

        except Exception as e:
            logger.error(f"魔塔社区生成失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return ""

    def chat(self, messages: list, max_length: int = 1024, temperature: float = 0.7) -> str:
        """
        对话式生成（使用OpenAI兼容接口）

        Args:
            messages: 消息列表，格式为 [{"role": "user/assistant/system", "content": "..."}]
            max_length: 最大生成长度
            temperature: 温度参数

        Returns:
            生成的回复
        """
        try:
            logger.info(f"调用魔塔社区API，模型: {self.model_name}")

            # 第一次尝试
            response = self._make_api_call(messages, max_length, temperature)

            # 检查响应是否有效
            if response and len(response.strip()) > 10:
                logger.info(f"魔塔社区API调用成功，生成长度: {len(response)}")
                return response

            # 如果第一次返回空，尝试重试一次
            logger.warning("第一次调用返回空响应，尝试重试...")
            response = self._make_api_call(messages, max_length, temperature)

            if response and len(response.strip()) > 10:
                logger.info(f"重试成功，生成长度: {len(response)}")
                return response

            logger.error("两次调用都返回空响应")
            return ""

        except Exception as e:
            logger.error(f"魔塔社区对话失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return ""

    def _make_api_call(self, messages: list, max_length: int, temperature: float) -> str:
        """执行单次API调用"""
        try:
            # 调用OpenAI兼容接口
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_length,
                temperature=temperature,
                top_p=0.8,
                stream=False
            )

            # 详细记录响应
            logger.debug(f"API响应对象: {response}")
            logger.debug(f"Choices: {response.choices}")

            # 提取生成的文本
            if response.choices and len(response.choices) > 0:
                choice = response.choices[0]
                logger.debug(f"Choice: {choice}")

                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    generated_text = choice.message.content
                    if generated_text:
                        return generated_text
                    else:
                        logger.warning("Content字段为空")
                        return ""
                else:
                    logger.error(f"Choice结构异常: {choice}")
                    return ""
            else:
                logger.error("API返回空choices")
                return ""

        except Exception as e:
            logger.error(f"API调用异常: {e}")
            raise


    def chat_stream(self, messages: list, max_length: int = 1024, temperature: float = 0.7) -> Generator[str, None, None]:
        """
        流式对话生成（实时输出）

        Args:
            messages: 消息列表
            max_length: 最大生成长度
            temperature: 温度参数

        Yields:
            逐块生成的文本片段
        """
        try:
            logger.info(f"调用魔塔社区API（流式），模型: {self.model_name}")

            # 调用流式接口
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_length,
                temperature=temperature,
                top_p=0.8,
                stream=True  # 启用流式模式
            )

            # 逐块返回生成的文本
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta_content = chunk.choices[0].delta.content
                    if delta_content:
                        yield delta_content

        except Exception as e:
            logger.error(f"魔塔社区流式对话失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            yield ""


class FallbackLLM(LLMBase):
    """
    降级LLM实现（当魔塔社区API不可用时使用）
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


def create_llm(llm_type: str = "dashscope", **kwargs) -> LLMBase:
    """
    工厂函数：创建LLM实例

    Args:
        llm_type: LLM类型
            - "dashscope": 阿里云百炼API（默认，推荐使用）
            - "modelscope": 魔塔社区API（备用方案）
            - "fallback": 降级方案（规则-based）

        **kwargs: 其他参数
            - api_key: 阿里云百炼API Key（dashscope模式必填）
            - api_token: 魔塔社区Token（modelscope模式必填）
            - model_name: 模型名称（可选）

    Returns:
        LLM实例

    Examples:
        # 使用阿里云百炼（推荐）
        >>> llm = create_llm(
        ...     llm_type='dashscope',
        ...     api_key='sk-your-api-key',
        ...     model_name='qwen-plus'
        ... )

        # 使用魔塔社区
        >>> llm = create_llm(
        ...     llm_type='modelscope',
        ...     api_token='your_token',
        ...     model_name='ZhipuAI/GLM-5.1'
        ... )

        # 使用降级方案
        >>> llm = create_llm(llm_type='fallback')
    """
    llm_registry = {
        "dashscope": DashScopeLLM,
        "modelscope": ModelScopeLLM,
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
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return FallbackLLM()



def get_qa_params():
    """
    获取问答系统的默认参数

    Returns:
        dict: 问答参数字典
    """
    from Recommend.LLMConfig import QA_CONFIG
    return {
        'max_length': QA_CONFIG.get('max_answer_length', 512),
        'temperature': QA_CONFIG.get('temperature', 0.7),
        'top_k_related': QA_CONFIG.get('top_k_related_news', 5),
    }


def validate_llm_config(llm_type: str = "dashscope") -> dict:
    """
    验证LLM配置是否完整

    Args:
        llm_type: LLM类型

    Returns:
        dict: {
            'valid': bool,
            'missing_fields': list,
            'message': str
        }
    """
    if llm_type.lower() == "fallback":
        return {
            'valid': True,
            'missing_fields': [],
            'message': '配置有效'
        }

    if llm_type.lower() == "dashscope":
        from Recommend.LLMConfig import DASHSCOPE_CONFIG
        api_key = DASHSCOPE_CONFIG.get('api_key', '')

        if not api_key or api_key == 'sk-your-dashscope-api-key-here':
            return {
                'valid': False,
                'missing_fields': ['api_key'],
                'message': '缺少阿里云百炼 API Key，请在 LLMConfig.py 中填写'
            }

        return {
            'valid': True,
            'missing_fields': [],
            'message': '配置有效'
        }

    if llm_type.lower() == "modelscope":
        from Recommend.LLMConfig import MODELSCOPE_CONFIG
        api_token = MODELSCOPE_CONFIG.get('api_token', '')

        if not api_token or api_token == 'your_modelscope_token_here':
            return {
                'valid': False,
                'missing_fields': ['api_token'],
                'message': '缺少魔塔社区 API Token，请在 LLMConfig.py 中填写'
            }

        return {
            'valid': True,
            'missing_fields': [],
            'message': '配置有效'
        }

    return {
        'valid': False,
        'missing_fields': [],
        'message': f'不支持的LLM类型: {llm_type}'
    }


