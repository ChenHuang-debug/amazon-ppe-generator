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
        self._last_image_outputs: list[dict] = []

    def generate_images(
        self,
        request_id: str,
        prompts: list[dict[str, str]],
        payload: PPEGenerateRequest,
    ) -> list[GeneratedImage]:
        del payload
        safe_prompts = prompts if isinstance(prompts, list) else []
        images: list[GeneratedImage] = []
        self._last_image_outputs = []

        for i in range(1, 8):
            raw = safe_prompts[i - 1] if i - 1 < len(safe_prompts) else {}
            item = raw if isinstance(raw, dict) else {}
            idx = safe_int(item.get('index'), i)
            name = str(item.get('name') or f'Image {i}')
            purpose = str(item.get('purpose') or 'PPE product image')
            positive_prompt = str(item.get('positive_prompt') or '')
            negative_prompt = str(item.get('negative_prompt') or 'text, watermark, logo, blur, low quality')

            image_result = self._generate_image_result(idx, positive_prompt, request_id)
            image_url = image_result['final_url']
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
            self._last_image_outputs.append(
                {
                    'index': idx,
                    'name': name,
                    'output_status': image_result['output_status'],
                    'final_url': image_result['final_url'],
                    'provider_url': image_result['provider_url'],
                    'fallback_url': image_result['fallback_url'],
                    'source': image_result['source'],
                    'provider_error': image_result.get('provider_error'),
                }
            )

        return images

    def _generate_image_result(self, idx: int, positive_prompt: str, request_id: str) -> dict:
        fallback_url = build_fallback_image_url(request_id, idx)

        if not self._settings.openai_api_key:
            return {
                'output_status': 'fallback',
                'final_url': fallback_url,
                'provider_url': None,
                'fallback_url': fallback_url,
                'source': 'fallback_missing_api_key',
                'provider_error': 'missing_openai_api_key',
            }
        if not positive_prompt:
            return {
                'output_status': 'fallback',
                'final_url': fallback_url,
                'provider_url': None,
                'fallback_url': fallback_url,
                'source': 'fallback_missing_prompt',
                'provider_error': 'missing_positive_prompt',
            }

        body = {
            'model': self._settings.image_model,
            'prompt': positive_prompt,
            'size': '1024x1024',
            'n': 1,
        }
        endpoint = f'{self._settings.openai_base_url}/images/generations'
        raw = post_json(endpoint, body, self._settings.openai_api_key, timeout=90)
        if not raw:
            return {
                'output_status': 'fallback',
                'final_url': fallback_url,
                'provider_url': None,
                'fallback_url': fallback_url,
                'source': 'fallback_provider_error',
                'provider_error': 'provider_request_failed',
            }

        provider_url = extract_image_url(raw)
        if provider_url:
            return {
                'output_status': 'real',
                'final_url': provider_url,
                'provider_url': provider_url,
                'fallback_url': fallback_url,
                'source': 'openai_images_api',
                'provider_error': None,
            }

        return {
            'output_status': 'fallback',
            'final_url': fallback_url,
            'provider_url': None,
            'fallback_url': fallback_url,
            'source': 'fallback_invalid_provider_response',
            'provider_error': 'missing_provider_image_url',
        }

    def get_last_image_outputs(self) -> list[dict]:
        return list(self._last_image_outputs)
