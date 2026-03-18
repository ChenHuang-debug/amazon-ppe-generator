from fastapi import FastAPI

from app.schemas import PPEGenerateRequest, PPEGenerateResponse
from app.workflows.pipeline import run_generation_pipeline

app = FastAPI(
    title='Amazon PPE Generator API',
    version='0.3.0',
    description='MVP backend for PPE image generation (mock pipeline).',
)


@app.get('/')
def root() -> dict[str, str]:
    return {'service': 'amazon-ppe-generator', 'version': '0.3.0'}


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}


@app.post('/generate', response_model=PPEGenerateResponse)
def generate(payload: PPEGenerateRequest) -> PPEGenerateResponse:
    return run_generation_pipeline(payload)
