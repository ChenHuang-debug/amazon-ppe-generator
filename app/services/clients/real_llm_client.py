import json
from urllib import error, request

from app.config.settings import Settings
from app.schemas import GeneratedImage, PPEGenerateRequest
from app.services.clients.base import BaseLLMClient
from app.services.clients.mock_llm_client import MockLLMClient


class RealLLMClient(BaseLLMClient):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._fallback = MockLLMClient()

    def generate_product_analysis(self, payload: PPEGenerateRequest) -> dict[str, object]:
        return self._fallback.generate_product_analysis(payload)

    def generate_image_prompts(
        self,
        payload: PPEGenerateRequest,
        analysis: dict[str, object],
    ) -> list[dict[str, str]]:
        if not self._settings.openai_api_key:
            return self._fallback.generate_image_prompts(payload, analysis)

        color_text = ', '.join(payload.colors)
        feature_text = ', '.join(payload.features)
        scenario_text = ', '.join(payload.scenarios)
        user_prompt = (
            'Generate JSON only with key \"images\" as an array of 7 objects. '
            'Each object must include: index (int 1-7), name, purpose, positive_prompt, negative_prompt.\\n'
            f'Product name: {payload.product_name}\\n'
            f'Category: {payload.category.value}\\n'
            f'Colors: {color_text}\\n'
            f'Reflective type: {payload.reflective_type}\\n'
            f'Certification: {payload.certification}\\n'
            f'Features: {feature_text}\\n'
            f'Scenarios: {scenario_text}\\n'
            f'Analysis: {json.dumps(analysis)}'
        )
        body = {
            'model': self._settings.llm_model,
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are an e-commerce image prompt engineer. Return valid JSON only.',
                },
                {'role': 'user', 'content': user_prompt},
            ],
            'response_format': {'type': 'json_object'},
            'temperature': 0.4,
        }

        try:
            endpoint = f'{self._settings.openai_base_url}/chat/completions'
            req = request.Request(
                endpoint,
                data=json.dumps(body).encode('utf-8'),
                headers={
                    'Authorization': f'Bearer {self._settings.openai_api_key}',
                    'Content-Type': 'application/json',
                },
                method='POST',
            )
            with request.urlopen(req, timeout=60) as resp:
                raw = json.loads(resp.read().decode('utf-8'))
            content = raw['choices'][0]['message']['content']
            parsed = json.loads(content)
            images = parsed.get('images', [])
            if isinstance(images, list) and len(images) == 7:
                normalized: list[dict[str, str]] = []
                for i, item in enumerate(images, start=1):
                    normalized.append({
                        'index': str(item.get('index', i)),
                        'name': str(item.get('name', f'Image {i}')),
                        'purpose': str(item.get('purpose', 'PPE product image')),
                        'positive_prompt': str(item.get('positive_prompt', '')),
                        'negative_prompt': str(item.get('negative_prompt', 'text, watermark, logo')),
                    })
                return normalized
        except (error.URLError, error.HTTPError, TimeoutError, KeyError, json.JSONDecodeError, ValueError):
            pass

        return self._fallback.generate_image_prompts(payload, analysis)

    def generate_usage_guide(
        self,
        payload: PPEGenerateRequest,
        images: list[GeneratedImage],
    ) -> str:
        return self._fallback.generate_usage_guide(payload, images)
