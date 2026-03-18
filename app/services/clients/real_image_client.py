from app.config.settings import Settings
from app.schemas import GeneratedImage, PPEGenerateRequest
from app.services.clients.base import BaseImageClient
from app.services.clients.provider_utils import (
    build_fallback_image_url,
    extract_image_url,
    post_json,
    safe_int,
)


class RealImageClient(BaseImageClient):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def generate_images(
        self,
        request_id: str,
        prompts: list[dict[str, str]],
        payload: PPEGenerateRequest,
    ) -> list[GeneratedImage]:
        del payload
        safe_prompts = prompts if isinstance(prompts, list) else []
        images: list[GeneratedImage] = []

        for i in range(1, 8):
            raw = safe_prompts[i - 1] if i - 1 < len(safe_prompts) else {}
            item = raw if isinstance(raw, dict) else {}
            idx = safe_int(item.get('index'), i)
            name = str(item.get('name') or f'Image {i}')
            purpose = str(item.get('purpose') or 'PPE product image')
            positive_prompt = str(item.get('positive_prompt') or '')
            negative_prompt = str(item.get('negative_prompt') or 'text, watermark, logo, blur, low quality')

            image_url = self._generate_image_url(idx, positive_prompt, request_id)
            images.append(
                GeneratedImage(
                    index=idx,
                    name=name,
                    purpose=purpose,
                    image_url=image_url,
                    positive_prompt=positive_prompt,
                    negative_prompt=negative_prompt,
                )
            )

        return images

    def _generate_image_url(self, idx: int, positive_prompt: str, request_id: str) -> str:
        fallback_url = build_fallback_image_url(request_id, idx)
        if not self._settings.openai_api_key:
            return fallback_url
        if not positive_prompt:
            return fallback_url

        body = {
            'model': self._settings.image_model,
            'prompt': positive_prompt,
            'size': '1024x1024',
            'n': 1,
        }
        endpoint = f'{self._settings.openai_base_url}/images/generations'
        raw = post_json(endpoint, body, self._settings.openai_api_key, timeout=90)
        if not raw:
            return fallback_url

        parsed_url = extract_image_url(raw)
        return parsed_url if parsed_url else fallback_url
