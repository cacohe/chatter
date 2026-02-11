from src.backend.domain.repository_interfaces.session import ISessionRepository
from src.shared.schemas import llm as llm_schema
from src.backend.domain.exceptions import BusinessException
from src.backend.infra.llm.registry import ModelRegistry
from src.shared.config import settings


class LLMService:
    def __init__(self, session_repo: ISessionRepository):
        # 需要 SessionRepo 来更新某个会话绑定的模型
        self.session_repo = session_repo

    async def get_models(self) -> llm_schema.LLMListResponse:
        """
        获取可用模型列表。
        """
        # 从注册中心获取所有已注册的模型 ID（只返回已配置 API Key 的模型）
        available_model_ids = ModelRegistry.get_available_model_ids()

        # 业务逻辑：如果是高级模型，可以在此处根据用户权限进行过滤（逻辑略）

        # 将字符串转换为 LLMInfo 对象
        models = []
        for model_id in available_model_ids:
            if model_id.startswith("gpt"):
                models.append(
                    llm_schema.LLMInfo(
                        id=model_id,
                        name=model_id.upper(),
                        provider=llm_schema.ModelProvider.OPENAI,
                        is_active=(model_id == settings.llm_settings.default_llm),
                    )
                )
            elif model_id.startswith("gemini"):
                models.append(
                    llm_schema.LLMInfo(
                        id=model_id,
                        name=model_id.replace("-", " ").title(),
                        provider=llm_schema.ModelProvider.GOOGLE,
                        is_active=(model_id == settings.llm_settings.default_llm),
                    )
                )
            elif model_id.startswith("deepseek"):
                models.append(
                    llm_schema.LLMInfo(
                        id=model_id,
                        name=model_id.replace("-", " ").title(),
                        provider=llm_schema.ModelProvider.DEEPSEEK,
                        is_active=(model_id == settings.llm_settings.default_llm),
                    )
                )
            elif model_id.startswith("qwen"):
                display_name = (
                    model_id.replace("qwen", "Qwen ")
                    .replace(".", "-")
                    .title()
                    .replace("-", ".")
                    .strip()
                )
                if model_id == "qwen3.5-plus":
                    display_name = "Qwen 3.5 Plus"
                elif model_id == "qwen3.5-flash":
                    display_name = "Qwen 3.5 Flash"
                elif model_id == "qwen-flash-character":
                    display_name = "Qwen Flash Character"
                models.append(
                    llm_schema.LLMInfo(
                        id=model_id,
                        name=display_name,
                        provider=llm_schema.ModelProvider.OPENAI,
                        is_active=(model_id == settings.llm_settings.default_llm),
                    )
                )
            else:
                models.append(
                    llm_schema.LLMInfo(
                        id=model_id,
                        name=model_id.upper(),
                        provider=llm_schema.ModelProvider.LOCAL,
                        is_active=(model_id == settings.llm_settings.default_llm),
                    )
                )

        return llm_schema.LLMListResponse(
            models=models,
            current_model_id=settings.llm_settings.default_llm,  # 默认值
        )

    async def switch_model(
        self, request: llm_schema.ModelSwitchRequest
    ) -> llm_schema.ModelSwitchResponse:
        """
        切换特定会话使用的模型
        """
        # 1. 校验模型是否存在
        if not ModelRegistry.exists(request.model_id):
            raise BusinessException(f"模型 {request.model_id} 不可用")

        # 2. 校验模型 API Key 是否配置
        if not ModelRegistry.is_model_available(request.model_id):
            raise BusinessException(f"模型 {request.model_id} 的 API Key 未配置")

        # 3. 持久化切换结果到数据库（Session表通常有一个字段记录所选模型）
        success = await self.session_repo.update_session_model(
            session_id=request.session_id, model_id=request.model_id
        )

        if not success:
            raise BusinessException("会话不存在，切换模型失败")

        return llm_schema.ModelSwitchResponse(
            session_id=request.session_id,
            active_model_id=request.model_id,
            success=True,
        )
