from app.schemas import GeneratedImage, PPEGenerateRequest
from app.services.clients.base import BaseLLMClient


def generate_guide(
    payload: PPEGenerateRequest,
    images: list[GeneratedImage],
    llm_client: BaseLLMClient,
) -> str:
    return llm_client.generate_usage_guide(payload, images)
