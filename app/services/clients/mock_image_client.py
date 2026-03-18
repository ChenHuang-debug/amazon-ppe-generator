from app.schemas import GeneratedImage, PPEGenerateRequest
from app.services.clients.base import BaseImageClient


class MockImageClient(BaseImageClient):
    def generate_images(
        self,
        request_id: str,
        prompts: list[dict[str, str]],
        payload: PPEGenerateRequest,
    ) -> list[GeneratedImage]:
        del payload
        images: list[GeneratedImage] = []
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
        return images
