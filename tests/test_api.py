import io
import json
import shutil
import zipfile
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def _valid_payload() -> dict:
    return {
        'product_name': 'High Visibility Reflective Safety Vest',
        'category': 'vest',
        'colors': ['Yellow', 'Silver'],
        'reflective_type': '2-inch silver reflective strips',
        'certification': 'ANSI/ISEA 107 Class 2',
        'features': ['6 pockets', 'zipper front', 'adjustable waist straps'],
        'scenarios': ['construction', 'road work', 'traffic control'],
        'price_level': 'mid-range',
        'image_url': 'https://example.com/reference/vest.jpg',
    }


def _test_output_root() -> Path:
    root = Path('test_outputs') / uuid4().hex
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_health_returns_200() -> None:
    client = TestClient(app)
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_generate_mock_mode_returns_200_and_7_images(monkeypatch) -> None:
    output_root = _test_output_root()
    try:
        monkeypatch.setenv('APP_MODE', 'MOCK')
        monkeypatch.delenv('OPENAI_API_KEY', raising=False)
        monkeypatch.setenv('OUTPUTS_DIR', str(output_root))
        client = TestClient(app)
        response = client.post('/generate', json=_valid_payload())
        body = response.json()
        assert response.status_code == 200
        assert len(body['images']) == 7
        assert body['images'][0]['image_url'].startswith('https://mock-cdn.local/')
        assert set(body.keys()) == {
            'status', 'product_name', 'product_category', 'images',
            'usage_guide', 'product_analysis', 'meta',
        }
    finally:
        shutil.rmtree(output_root, ignore_errors=True)


def test_generate_real_mode_without_key_uses_fallback_urls(monkeypatch) -> None:
    output_root = _test_output_root()
    try:
        monkeypatch.setenv('APP_MODE', 'REAL')
        monkeypatch.delenv('OPENAI_API_KEY', raising=False)
        monkeypatch.setenv('OUTPUTS_DIR', str(output_root))
        client = TestClient(app)
        response = client.post('/generate', json=_valid_payload())
        body = response.json()
        assert response.status_code == 200
        assert len(body['images']) == 7
        assert body['images'][0]['image_url'].startswith('https://real-images.example/')
    finally:
        shutil.rmtree(output_root, ignore_errors=True)


def test_generate_without_image_url_returns_422(monkeypatch) -> None:
    monkeypatch.setenv('APP_MODE', 'MOCK')
    client = TestClient(app)
    payload = _valid_payload()
    payload.pop('image_url')
    response = client.post('/generate', json=payload)
    assert response.status_code == 422

def test_generate_persists_output_files(monkeypatch) -> None:
    output_root = _test_output_root()
    try:
        monkeypatch.setenv('APP_MODE', 'MOCK')
        monkeypatch.delenv('OPENAI_API_KEY', raising=False)
        monkeypatch.setenv('OUTPUTS_DIR', str(output_root))
        client = TestClient(app)
        response = client.post('/generate', json=_valid_payload())
        assert response.status_code == 200

        request_dirs = [p for p in output_root.iterdir() if p.is_dir()]
        assert len(request_dirs) == 1
        request_dir = request_dirs[0]

        manifest_file = request_dir / '00_manifest.json'
        response_file = request_dir / '10_response_payload.json'
        prompts_file = request_dir / '30_image_prompts.json'
        outputs_file = request_dir / '40_image_outputs.json'
        guide_file = request_dir / '20_usage_guide.md'
        legacy_response_file = request_dir / 'response.json'
        legacy_guide_file = request_dir / 'usage_guide_and_prompts.md'
        assert manifest_file.exists()
        assert response_file.exists()
        assert prompts_file.exists()
        assert outputs_file.exists()
        assert guide_file.exists()
        assert legacy_response_file.exists()
        assert legacy_guide_file.exists()

        saved = json.loads(response_file.read_text(encoding='utf-8'))
        assert set(saved.keys()) == {
            'status', 'product_name', 'product_category', 'images',
            'usage_guide', 'product_analysis', 'meta',
        }
        manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
        assert manifest['manifest_version'] == '1.2'
        assert manifest['request_id'] == saved['meta']['request_id']
        assert isinstance(manifest['files'], list)
        names = {item['name'] for item in manifest['files']}
        assert '00_manifest.json' in names
        assert '10_response_payload.json' in names
        assert '20_usage_guide.md' in names
        assert '30_image_prompts.json' in names
        assert '40_image_outputs.json' in names
    finally:
        shutil.rmtree(output_root, ignore_errors=True)


def test_outputs_endpoints_list_manifest_and_file(monkeypatch) -> None:
    output_root = _test_output_root()
    try:
        monkeypatch.setenv('APP_MODE', 'MOCK')
        monkeypatch.setenv('OUTPUTS_DIR', str(output_root))
        monkeypatch.delenv('OPENAI_API_KEY', raising=False)
        client = TestClient(app)
        generated = client.post('/generate', json=_valid_payload()).json()
        request_id = generated['meta']['request_id']

        listed = client.get('/outputs?limit=10')
        assert listed.status_code == 200
        items = listed.json()['items']
        assert any(item['request_id'] == request_id for item in items)

        manifest_resp = client.get(f'/outputs/{request_id}/manifest')
        assert manifest_resp.status_code == 200
        manifest = manifest_resp.json()
        assert manifest['request_id'] == request_id

        file_resp = client.get(f'/outputs/{request_id}/files/10_response_payload.json')
        assert file_resp.status_code == 200
        payload_json = json.loads(file_resp.text)
        assert payload_json['meta']['request_id'] == request_id
    finally:
        shutil.rmtree(output_root, ignore_errors=True)


def test_outputs_endpoints_missing_resources_return_404(monkeypatch) -> None:
    output_root = _test_output_root()
    try:
        monkeypatch.setenv('APP_MODE', 'MOCK')
        monkeypatch.setenv('OUTPUTS_DIR', str(output_root))
        client = TestClient(app)
        missing_manifest = client.get('/outputs/not_found_request/manifest')
        assert missing_manifest.status_code == 404
        generated = client.post('/generate', json=_valid_payload()).json()
        request_id = generated['meta']['request_id']
        missing_file = client.get(f'/outputs/{request_id}/files/not_exists.txt')
        assert missing_file.status_code == 404
    finally:
        shutil.rmtree(output_root, ignore_errors=True)

def test_outputs_download_zip_returns_package(monkeypatch) -> None:
    output_root = _test_output_root()
    try:
        monkeypatch.setenv('APP_MODE', 'MOCK')
        monkeypatch.setenv('OUTPUTS_DIR', str(output_root))
        monkeypatch.delenv('OPENAI_API_KEY', raising=False)
        client = TestClient(app)
        generated = client.post('/generate', json=_valid_payload()).json()
        request_id = generated['meta']['request_id']
        resp = client.get(f'/outputs/{request_id}/download')
        assert resp.status_code == 200
        assert resp.headers['content-type'].startswith('application/zip')
        assert f'{request_id}_artifacts.zip' in resp.headers.get('content-disposition', '')
        z = zipfile.ZipFile(io.BytesIO(resp.content))
        names = set(z.namelist())
        assert '00_manifest.json' in names
        assert '10_response_payload.json' in names
        assert '20_usage_guide.md' in names
        assert '30_image_prompts.json' in names
    finally:
        shutil.rmtree(output_root, ignore_errors=True)


def test_outputs_download_zip_missing_request_returns_404(monkeypatch) -> None:
    output_root = _test_output_root()
    try:
        monkeypatch.setenv('APP_MODE', 'MOCK')
        monkeypatch.setenv('OUTPUTS_DIR', str(output_root))
        client = TestClient(app)
        resp = client.get('/outputs/not_found_request/download')
        assert resp.status_code == 404
    finally:
        shutil.rmtree(output_root, ignore_errors=True)


def test_manifest_image_outputs_metadata_mock_statuses(monkeypatch) -> None:
    output_root = _test_output_root()
    try:
        monkeypatch.setenv('APP_MODE', 'MOCK')
        monkeypatch.setenv('OUTPUTS_DIR', str(output_root))
        monkeypatch.delenv('OPENAI_API_KEY', raising=False)
        client = TestClient(app)
        client.post('/generate', json=_valid_payload())
        request_dir = [p for p in output_root.iterdir() if p.is_dir()][0]
        manifest = json.loads((request_dir / '00_manifest.json').read_text(encoding='utf-8'))
        image_outputs = manifest['image_outputs']
        assert image_outputs['total_images'] == 7
        assert image_outputs['status_counts']['mock'] == 7
        assert image_outputs['status_counts']['fallback'] == 0
        assert image_outputs['status_counts']['real'] == 0
        assert len(image_outputs['records']) == 7
    finally:
        shutil.rmtree(output_root, ignore_errors=True)


def test_manifest_image_outputs_metadata_real_fallback_statuses(monkeypatch) -> None:
    output_root = _test_output_root()
    try:
        monkeypatch.setenv('APP_MODE', 'REAL')
        monkeypatch.setenv('OUTPUTS_DIR', str(output_root))
        monkeypatch.delenv('OPENAI_API_KEY', raising=False)
        client = TestClient(app)
        client.post('/generate', json=_valid_payload())
        request_dir = [p for p in output_root.iterdir() if p.is_dir()][0]
        manifest = json.loads((request_dir / '00_manifest.json').read_text(encoding='utf-8'))
        image_outputs = manifest['image_outputs']
        assert image_outputs['total_images'] == 7
        assert image_outputs['status_counts']['fallback'] == 7
        assert image_outputs['status_counts']['real'] == 0
        assert image_outputs['status_counts']['mock'] == 0
        first = image_outputs['records'][0]
        assert first['output_status'] == 'fallback'
        assert first['provider_url'] is None
        assert isinstance(first['fallback_url'], str)
        assert first['fallback_url'].startswith('https://real-images.example/')
    finally:
        shutil.rmtree(output_root, ignore_errors=True)
 
 
def test_outputs_list_includes_frontend_summary_fields(monkeypatch) -> None: 
    output_root = _test_output_root() 
    try: 
        monkeypatch.setenv('APP_MODE', 'MOCK') 
        monkeypatch.setenv('OUTPUTS_DIR', str(output_root)) 
        monkeypatch.delenv('OPENAI_API_KEY', raising=False) 
        client = TestClient(app) 
        generated = client.post('/generate', json=_valid_payload()).json() 
        request_id = generated['meta']['request_id'] 
 
        listed = client.get('/outputs?limit=10') 
        assert listed.status_code == 200 
        items = listed.json()['items'] 
        summary = next(item for item in items if item['request_id'] == request_id) 
        assert summary['generated_at'] 
        assert summary['mode'] == 'mock' 
        assert summary['product_name'] == _valid_payload()['product_name'] 
        assert summary['total_images'] == 7  
        assert summary['image_status_counts'] == {'mock': 7, 'fallback': 0, 'real': 0} 
        assert isinstance(summary['available_artifacts'], list) 
        assert 'manifest' in summary['available_artifacts'] 
        assert 'response_payload' in summary['available_artifacts'] 
    finally: 
        shutil.rmtree(output_root, ignore_errors=True)
 
 
def test_outputs_folder_name_not_template_literal(monkeypatch): 
    output_root = _test_output_root() 
    try: 
        monkeypatch.setenv('APP_MODE', 'MOCK') 
        monkeypatch.setenv('OUTPUTS_DIR', str(output_root)) 
        monkeypatch.delenv('OPENAI_API_KEY', raising=False) 
        client = TestClient(app) 
        generated = client.post('/generate', json=_valid_payload()).json() 
        request_id = generated['meta']['request_id'] 
        listed = client.get('/outputs?limit=10') 
        assert listed.status_code == 200 
        item = next(x for x in listed.json()['items'] if x['request_id'] == request_id) 
        assert item['folder'].endswith('_' + request_id) 
        assert '%%Y%%m%%dT%%H%%M%%SZ' not in item['folder'] 
        assert '%%' not in item['folder'] 
    finally: 
        shutil.rmtree(output_root, ignore_errors=True)
 
 
def test_outputs_infers_mode_from_image_outputs_when_manifest_mode_inconsistent(monkeypatch): 
    output_root = _test_output_root() 
    try: 
        monkeypatch.setenv('OUTPUTS_DIR', str(output_root)) 
        folder = output_root / '20260101T000000Z_inconsistent123' 
        folder.mkdir(parents=True, exist_ok=True) 
        manifest = { 
            'request_id': 'inconsistent123', 
            'generated_at': '2026-01-01T00:00:00Z', 
            'mode': 'mock', 
            'product_name': 'Legacy PPE', 
            'files': [{'name': '40_image_outputs.json', 'role': 'image_outputs'}], 
            'image_outputs': {'total_images': 0, 'status_counts': {'mock': 0, 'fallback': 0, 'real': 0}}, 
        } 
        image_outputs = {'images': [{'index': i, 'output_status': 'fallback', 'final_url': f'https://real-images.example/inconsistent123/image_{i}.jpg'} for i in range(1, 8)]} 
        (folder / '00_manifest.json').write_text(json.dumps(manifest), encoding='utf-8') 
        (folder / '40_image_outputs.json').write_text(json.dumps(image_outputs), encoding='utf-8') 
        client = TestClient(app) 
        listed = client.get('/outputs?limit=10') 
        assert listed.status_code == 200 
        item = next(x for x in listed.json()['items'] if x['request_id'] == 'inconsistent123') 
        assert item['mode'] == 'real' 
        assert item['total_images'] == 7  
        assert item['image_status_counts'] == {'mock': 0, 'fallback': 7, 'real': 0} 
    finally: 
        shutil.rmtree(output_root, ignore_errors=True)
 
 
def test_outputs_legacy_manifest_uses_response_images_for_counts(monkeypatch): 
    output_root = _test_output_root() 
    try: 
        monkeypatch.setenv('OUTPUTS_DIR', str(output_root)) 
        folder = output_root / '20260102T000000Z_legacy123' 
        folder.mkdir(parents=True, exist_ok=True) 
        manifest = { 
            'request_id': 'legacy123', 
            'generated_at': '2026-01-02T00:00:00Z', 
            'mode': 'mock', 
            'product_name': 'Legacy PPE 2', 
            'files': [{'name': '10_response_payload.json', 'role': 'response_payload'}], 
            'image_outputs': {'total_images': 0, 'status_counts': {'mock': 0, 'fallback': 0, 'real': 0}}, 
        } 
        response_payload = {'images': [{'image_url': f'https://mock-cdn.local/legacy123/image_{i}.jpg'} for i in range(1, 8)]} 
        (folder / '00_manifest.json').write_text(json.dumps(manifest), encoding='utf-8') 
        (folder / '10_response_payload.json').write_text(json.dumps(response_payload), encoding='utf-8') 
        client = TestClient(app) 
        listed = client.get('/outputs?limit=10') 
        assert listed.status_code == 200 
        item = next(x for x in listed.json()['items'] if x['request_id'] == 'legacy123') 
        assert item['mode'] == 'mock' 
        assert item['total_images'] == 7  
        assert item['image_status_counts'] == {'mock': 7, 'fallback': 0, 'real': 0} 
    finally: 
        shutil.rmtree(output_root, ignore_errors=True)
 
 
def test_generate_persists_image_artifact_records(monkeypatch): 
    output_root = _test_output_root() 
    try: 
        monkeypatch.setenv('APP_MODE', 'MOCK') 
        monkeypatch.setenv('OUTPUTS_DIR', str(output_root)) 
        monkeypatch.delenv('OPENAI_API_KEY', raising=False) 
        client = TestClient(app) 
        response = client.post('/generate', json=_valid_payload()) 
        assert response.status_code == 200 
        request_dir = [p for p in output_root.iterdir() if p.is_dir()][0] 
 
        for i in range(1, 8): 
            artifact_file = request_dir / f'50_image_{i:02d}_artifact.json' 
            pointer_file = request_dir / f'60_image_{i:02d}.url' 
            assert artifact_file.exists() 
            assert pointer_file.exists() 
 
        manifest = json.loads((request_dir / '00_manifest.json').read_text(encoding='utf-8')) 
        assert manifest['manifest_version'] == '1.2' 
        first_record = manifest['image_artifacts']['records'][0] 
        assert first_record['artifact_file'] == '50_image_01_artifact.json' 
        assert first_record['url_pointer_file'] == '60_image_01.url' 
        assert first_record['local_image_status'] == 'not_saved' 
        assert first_record['local_image_file'] is None 
 
        outputs_payload = json.loads((request_dir / '40_image_outputs.json').read_text(encoding='utf-8')) 
        first_output = outputs_payload['images'][0] 
        assert first_output['artifact_file'] == '50_image_01_artifact.json' 
        assert first_output['url_pointer_file'] == '60_image_01.url' 
    finally: 
        shutil.rmtree(output_root, ignore_errors=True)
