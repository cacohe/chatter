from typing import Dict, Any, List
import os

from langchain_community.chat_models import ChatTongyi, ChatOpenAI, ChatOllama
from langchain_core.messages import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from ...infra.log.logger import logger


class ModelManager:
    """统一管理多种大语言模型"""

    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.current_model = "qwen"
        self.setup_models()

    def setup_models(self):
        """初始化所有可用模型"""
        # 通义千问模型
        logger.info("正在加载通义千问模型...")
        if os.getenv("DASHSCOPE_API_KEY"):
            try:
                self.models["qwen"] = ChatTongyi(
                    model="qwen-turbo",
                    temperature=0.7
                )
                logger.info("通义千问模型加载成功")
            except Exception as e:
                logger.warning(f"通义千问模型加载失败: {e}")
        else:
            logger.warning("通义千问模型未配置，请在环境变量中设置 DASHSCOPE_API_KEY")
        
        # OpenAI模型
        logger.info("正在加载OpenAI模型...")
        if os.getenv("OPENAI_API_KEY"):
            try:
                self.models["openai"] = ChatOpenAI(
                    model_name="gpt-3.5-turbo",
                    temperature=0.7,
                    streaming=True
                )
                self.models["openai-4"] = ChatOpenAI(
                    model_name="gpt-4",
                    temperature=0.7,
                    streaming=True
                )
                logger.info("OpenAI模型加载成功")
            except Exception as e:
                logger.warning(f"OpenAI模型加载失败: {e}")
        else:
            logger.warning("OpenAI模型未配置，请在环境变量中设置 OPENAI_API_KEY")

        # Google Gemini模型
        logger.info("正在加载Google Gemini模型...")
        if os.getenv("GOOGLE_API_KEY"):
            try:
                self.models["gemini"] = ChatGoogleGenerativeAI(
                    model="gemini-pro",
                    temperature=0.7
                )
                logger.info("Google Gemini模型加载成功")
            except Exception as e:
                logger.warning(f"Google Gemini模型加载失败: {e}")
        else:
            logger.warning("Google Gemini模型未配置，请在环境变量中设置 GOOGLE_API_KEY")

        # 本地Ollama模型
        try:
            self.models["llama"] = ChatOllama(
                model="llama2:7b",
                temperature=0.7
            )
            self.models["mistral"] = ChatOllama(
                model="mistral:7b",
                temperature=0.7
            )
            logger.info("Ollama模型加载成功")
        except Exception as e:
            logger.warning(f"Ollama模型未就绪: {e}")

    def list_available_models(self) -> List[str]:
        """获取可用模型列表"""
        return list(self.models.keys())

    def switch_model(self, model_name: str) -> bool:
        """切换当前模型"""
        if model_name in self.models:
            self.current_model = model_name
            return True
        return False

    def get_model(self, model_name: str = None):
        """获取指定模型实例"""
        if model_name is None:
            model_name = self.current_model
        return self.models.get(model_name)

    async def generate_response(self, messages: List[BaseMessage], **kwargs) -> str:
        """使用当前模型生成回复"""
        model = self.get_model()
        if not model:
            return "错误：没有可用的模型"

        try:
            response = await model.ainvoke(messages, **kwargs)
            return response.content
        except Exception as e:
            logger.error(f"模型调用失败: {e}")
            return f"模型调用失败: {model.model_name}"
