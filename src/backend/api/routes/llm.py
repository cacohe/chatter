from fastapi import APIRouter, status
from fastapi.params import Depends

from src.backend.api.deps import get_llm_service
from src.backend.app.services.llm import LLMService
from src.shared.schemas import llm as llm_schema


llm_router = APIRouter(prefix="/api/v1.0/llm", tags=["Model Management"])


@llm_router.get("/list",
                status_code=status.HTTP_200_OK,
                response_model=llm_schema.LLMListResponse)
async def get_models(service: LLMService = Depends(get_llm_service)) -> llm_schema.LLMListResponse:
    return await service.get_models()


@llm_router.post("/switch",
                 status_code=status.HTTP_202_ACCEPTED,
                 response_model=llm_schema.ModelSwitchResponse)
async def switch_model(
        request: llm_schema.ModelSwitchRequest,
        service: LLMService = Depends(get_llm_service),
) -> llm_schema.ModelSwitchResponse:
    return await service.switch_model(request)
