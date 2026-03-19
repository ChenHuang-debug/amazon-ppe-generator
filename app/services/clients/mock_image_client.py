from app.schemas import GeneratedImage, PPEGenerateRequest
from app.services.clients.base import BaseImageClient


class MockImageClient(BaseImageClient):
    def __init__(self) -> None:
        self._last_image_outputs: list[dict] = []

    def generate_images(
        self,
        request_id: str,
        prompts: list[dict[str, str]],
        payload: PPEGenerateRequest,
    ) -> list[GeneratedImage]:
        del payload
        images: list[GeneratedImage] = []
        self._last_image_outputs = []
        for prompt in prompts:
            idx = int(prompt['index'])
            image_url = f'https://mock-cdn.local/{request_id}/image_{idx}.jpg'
            images.append(
                GeneratedImage(
                    index=idx,
                    name=prompt['name'],
                    purpose=prompt['purpose'],
                    image_url=image_url,
                    positive_prompt=prompt['positive_prompt'],
                    negative_prompt=prompt['negative_prompt'],
                )
            )
            self._last_image_outputs.append(
                {
                    'index': idx,
                    'name': prompt['name'],
                    'output_status': 'mock',
                    'final_url': image_url,
                    'provider_url': None,
                    'fallback_url': None,
                    'source': 'mock_provider',
                }
            )
        return images

    def get_last_image_outputs(self) -> list[dict]:
        return list(self._last_image_outputs)
