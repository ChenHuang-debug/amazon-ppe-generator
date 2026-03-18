from app.schemas import GeneratedImage, PPEGenerateRequest
from app.services.clients.base import BaseImageClient


def generate_images(
    request_id: str,
    prompts: list[dict[str, str]],
    payload: PPEGenerateRequest,
    image_client: BaseImageClient,
) -> list[GeneratedImage]:
    return image_client.generate_images(request_id, prompts, payload)
