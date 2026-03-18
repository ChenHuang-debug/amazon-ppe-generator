from app.schemas import PPEGenerateRequest
from app.services.clients.base import BaseLLMClient


def analyze_product(payload: PPEGenerateRequest, llm_client: BaseLLMClient) -> dict[str, object]:
    return llm_client.generate_product_analysis(payload)
