import json
from urllib import error, request

from app.config.settings import Settings
from app.schemas import GeneratedImage, PPEGenerateRequest
from app.services.clients.base import BaseImageClient


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
        images: list[GeneratedImage] = []
        for prompt in prompts:
            idx = int(prompt['index'])
            image_url = self._generate_image_url(idx, prompt['positive_prompt'], request_id)
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

    def _generate_image_url(self, idx: int, positive_prompt: str, request_id: str) -> str:
        if not self._settings.openai_api_key:
            return f'https://real-images.example/{request_id}/image_{idx}.png'

        body = {
            'model': self._settings.image_model,
            'prompt': positive_prompt,
            'size': '1024x1024',
            'n': 1,
        }
        try:
            endpoint = f'{self._settings.openai_base_url}/images/generations'
            req = request.Request(
                endpoint,
                data=json.dumps(body).encode('utf-8'),
                headers={
                    'Authorization': f'Bearer {self._settings.openai_api_key}',
                    'Content-Type': 'application/json',
                },
                method='POST',
            )
            with request.urlopen(req, timeout=90) as resp:
                raw = json.loads(resp.read().decode('utf-8'))
            data = raw.get('data', [])
            if data and data[0].get('url'):
                return str(data[0]['url'])
        except (error.URLError, error.HTTPError, TimeoutError, KeyError, json.JSONDecodeError, ValueError):
            pass

        return f'https://real-images.example/{request_id}/image_{idx}.png'
