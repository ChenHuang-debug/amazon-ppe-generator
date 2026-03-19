from datetime import datetime, timezone
from uuid import uuid4

from app.config.settings import AppMode, Settings, get_settings
from app.schemas import GenerateMeta, PPEGenerateRequest, PPEGenerateResponse
from app.services.clients.base import BaseImageClient, BaseLLMClient
from app.services.clients.mock_image_client import MockImageClient
from app.services.clients.mock_llm_client import MockLLMClient
from app.services.clients.real_image_client import RealImageClient
from app.services.clients.real_llm_client import RealLLMClient
from app.services.guide_generator import generate_guide
from app.services.image_generator import generate_images
from app.services.output_persistence import persist_generation_output
from app.services.product_analysis import analyze_product
from app.services.prompt_generator import generate_prompts


def _build_clients(settings: Settings) -> tuple[BaseLLMClient, BaseImageClient]:
    if settings.mode == AppMode.MOCK:
        return MockLLMClient(), MockImageClient()
    if settings.mode == AppMode.REAL:
        return RealLLMClient(settings), RealImageClient(settings)

    return MockLLMClient(), MockImageClient()


def run_generation_pipeline(payload: PPEGenerateRequest) -> PPEGenerateResponse:
    settings = get_settings()
    request_id = uuid4().hex[:12]
    llm_client, image_client = _build_clients(settings)

    product_analysis = analyze_product(payload, llm_client)
    prompts = generate_prompts(payload, product_analysis, llm_client)
    images = generate_images(request_id, prompts, payload, image_client)
    usage_guide = generate_guide(payload, images, llm_client)

    meta = GenerateMeta(
        request_id=request_id,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )

    response = PPEGenerateResponse(
        product_name=payload.product_name,
        product_category=payload.category,
        images=images,
        usage_guide=usage_guide,
        product_analysis=product_analysis,
        meta=meta,
    )

    persist_generation_output(response, settings.outputs_dir, image_client.get_last_image_outputs())
    return response
