import json

from app.config.settings import Settings
from app.schemas import GeneratedImage, PPEGenerateRequest
from app.services.clients.base import BaseLLMClient
from app.services.clients.mock_llm_client import IMAGE_NAMES, IMAGE_PURPOSES, MockLLMClient
from app.services.clients.provider_utils import normalize_prompt_items, parse_chat_content, post_json


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
            'Generate JSON only with key \"images\" as an array of exactly 7 objects. '
            'Each object must include index, name, purpose, positive_prompt, negative_prompt.\\n'
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
        endpoint = f'{self._settings.openai_base_url}/chat/completions'
        raw = post_json(endpoint, body, self._settings.openai_api_key, timeout=60)
        if not raw:
            return self._fallback.generate_image_prompts(payload, analysis)

        content = parse_chat_content(raw)
        if not content:
            return self._fallback.generate_image_prompts(payload, analysis)

        try:
            parsed = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return self._fallback.generate_image_prompts(payload, analysis)

        raw_items = parsed.get('images', []) if isinstance(parsed, dict) else []
        if not isinstance(raw_items, list):
            raw_items = []
        normalized = normalize_prompt_items(raw_items, IMAGE_NAMES, IMAGE_PURPOSES)

        has_positive_prompt = any(item.get('positive_prompt') for item in normalized)
        if not has_positive_prompt:
            return self._fallback.generate_image_prompts(payload, analysis)

        return normalized

    def generate_usage_guide(
        self,
        payload: PPEGenerateRequest,
        images: list[GeneratedImage],
    ) -> str:
        return self._fallback.generate_usage_guide(payload, images)
