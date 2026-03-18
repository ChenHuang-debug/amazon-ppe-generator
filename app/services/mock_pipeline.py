from datetime import datetime, timezone
from uuid import uuid4

from app.schemas import (
    GenerateMeta,
    GeneratedImage,
    PPEGenerateRequest,
    PPEGenerateResponse,
)


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


def _build_product_analysis(payload: PPEGenerateRequest) -> dict[str, object]:
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


def _build_image_items(payload: PPEGenerateRequest, request_id: str) -> list[GeneratedImage]:
    images: list[GeneratedImage] = []
    feature_text = ', '.join(payload.features)
    color_text = ', '.join(payload.colors)
    for idx, (name, purpose) in enumerate(zip(IMAGE_NAMES, IMAGE_PURPOSES), start=1):
        positive_prompt = (
            f'Based on the reference product image, {color_text} {payload.category.value}, '
            f'{name.lower()}, pure white background, product occupies at least 85% of frame, '
            f'professional studio lighting, reflective type: {payload.reflective_type}, '
            f'certification: {payload.certification}, key features: {feature_text}, photorealistic.'
        )
        negative_prompt = 'text, watermark, logo, human, dark background, blur, low quality'
        image_url = f'https://mock-cdn.local/{request_id}/image_{idx}.jpg'
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


def _build_usage_guide() -> str:
    return (
        'Image 1 should be used as the hero image for the listing.\\n'
        'Images 2 to 7 should be used as supporting gallery images for feature storytelling.\\n'
        'Upload JPG or PNG at 1600px+; keep image 1 as real photo, AI images are better for images 2-7.'
    )


def run_mock_pipeline(payload: PPEGenerateRequest) -> PPEGenerateResponse:
    request_id = uuid4().hex[:12]
    analysis = _build_product_analysis(payload)
    images = _build_image_items(payload, request_id)
    meta = GenerateMeta(
        request_id=request_id,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
    return PPEGenerateResponse(
        product_name=payload.product_name,
        product_category=payload.category,
        images=images,
        usage_guide=_build_usage_guide(),
        product_analysis=analysis,
        meta=meta,
    )
