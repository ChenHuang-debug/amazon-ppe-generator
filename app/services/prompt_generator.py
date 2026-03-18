from app.schemas import PPEGenerateRequest
from app.services.clients.base import BaseLLMClient


def generate_prompts(
    payload: PPEGenerateRequest,
    analysis: dict[str, object],
    llm_client: BaseLLMClient,
) -> list[dict[str, str]]:
    return llm_client.generate_image_prompts(payload, analysis)
