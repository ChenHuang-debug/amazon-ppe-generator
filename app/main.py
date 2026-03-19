import io
import zipfile

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response

from app.config.settings import get_settings
from app.schemas import PPEGenerateRequest, PPEGenerateResponse
from app.services.output_repository import (
    list_recent_outputs,
    load_manifest,
    resolve_artifact_file,
    resolve_manifest_artifacts,
)
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


@app.get('/outputs')
def list_outputs(limit: int = Query(20, ge=1, le=200)) -> dict:
    settings = get_settings()
    items = list_recent_outputs(settings.outputs_dir, limit=limit)
    return {'count': len(items), 'items': items}


@app.get('/outputs/{request_id}/manifest')
def get_output_manifest(request_id: str) -> dict:
    settings = get_settings()
    manifest = load_manifest(settings.outputs_dir, request_id)
    if not manifest:
        raise HTTPException(status_code=404, detail='Request output not found')
    return manifest


@app.get('/outputs/{request_id}/files/{filename}')
def get_output_file(request_id: str, filename: str, download: bool = False) -> FileResponse:
    settings = get_settings()
    file_path = resolve_artifact_file(settings.outputs_dir, request_id, filename)
    if not file_path:
        if '/' in filename or '\\' in filename:
            raise HTTPException(status_code=400, detail='Invalid filename')
        raise HTTPException(status_code=404, detail='Output file not found')
    return FileResponse(
        path=str(file_path),
        filename=file_path.name if download else None,
        media_type='application/octet-stream',
    )


@app.get('/outputs/{request_id}/download')
def download_output_package(request_id: str) -> Response:
    settings = get_settings()
    resolved = resolve_manifest_artifacts(settings.outputs_dir, request_id)
    if not resolved:
        raise HTTPException(status_code=404, detail='Request output not found')

    files, missing = resolved
    if missing:
        raise HTTPException(status_code=404, detail='Missing artifact files: ' + ', '.join(missing))
    if not files:
        raise HTTPException(status_code=404, detail='No artifacts found for request')

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in files:
            zf.write(file_path, arcname=file_path.name)

    zip_bytes = buffer.getvalue()
    headers = {'Content-Disposition': f'attachment; filename={request_id}_artifacts.zip'}
    return Response(content=zip_bytes, media_type='application/zip', headers=headers)
