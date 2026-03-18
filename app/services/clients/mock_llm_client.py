from app.schemas import GeneratedImage, PPEGenerateRequest
from app.services.clients.base import BaseLLMClient

IMAGE_NAMES = [
    'Hero Shot - Front View',
    'Reflective Strip Detail',
    'Back View',
    'Feature Flat Lay',
    'Three-Quarter Angle',
    'Function Close-up Detail',
    'Hanging Display',
]

IMAGE_PURPOSES = [
    'Primary listing image showing full front appearance.',
    'Close-up to highlight reflective tape quality.',
    'Back view to show reflective strip layout.',
    'Flat lay showing functional components.',
    'Three-quarter angle to show volume and shape.',
    'Macro shot of one key feature detail.',
    'Hanging view to show overall silhouette.',
]


class MockLLMClient(BaseLLMClient):
    def generate_product_analysis(self, payload: PPEGenerateRequest) -> dict[str, object]:
        scenes = ', '.join(payload.scenarios)
        return {
            'product_summary': f'{payload.product_name} for {scenes}',
            'primary_buyer_persona': 'Safety-focused industrial buyers and procurement teams.',
            'key_pain_points': [
                'Need high daytime visibility',
                'Need reliable reflective performance at night',
                'Need comfort for long shifts',
            ],
            'must_show_features': payload.features[:3],
            'background_requirements': 'pure white background RGB(255,255,255)',
        }

    def generate_image_prompts(
        self,
        payload: PPEGenerateRequest,
        analysis: dict[str, object],
    ) -> list[dict[str, str]]:
        del analysis
        color_text = ', '.join(payload.colors)
        feature_text = ', '.join(payload.features)
        prompts: list[dict[str, str]] = []
        for idx, (name, purpose) in enumerate(zip(IMAGE_NAMES, IMAGE_PURPOSES), start=1):
            prompts.append({
                'index': str(idx),
                'name': name,
                'purpose': purpose,
                'positive_prompt': (
                    f'Based on the reference product image, {color_text} {payload.category.value}, '
                    f'{name.lower()}, pure white background, product occupies at least 85% of frame, '
                    f'professional studio lighting, reflective type: {payload.reflective_type}, '
                    f'certification: {payload.certification}, key features: {feature_text}, photorealistic.'
                ),
                'negative_prompt': 'text, watermark, logo, human, dark background, blur, low quality',
            })
        return prompts

    def generate_usage_guide(
        self,
        payload: PPEGenerateRequest,
        images: list[GeneratedImage],
    ) -> str:
        del payload
        del images
        return (
            'Image 1 should be used as the hero image for the listing.\\n'
            'Images 2 to 7 should be used as supporting gallery images for feature storytelling.\\n'
            'Upload JPG or PNG at 1600px+; keep image 1 as real photo, AI images are better for images 2-7.'
        )
