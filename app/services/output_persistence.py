import json 
from datetime import datetime, timezone 
from pathlib import Path 
 
from app.schemas import PPEGenerateResponse 
 
MANIFEST_FILE = '00_manifest.json' 
RESPONSE_FILE = '10_response_payload.json' 
GUIDE_FILE = '20_usage_guide.md' 
PROMPTS_FILE = '30_image_prompts.json' 
IMAGE_OUTPUTS_FILE = '40_image_outputs.json' 
 
# Backward-compatible files retained for previous integrations/tests. 
LEGACY_RESPONSE_FILE = 'response.json' 
LEGACY_GUIDE_FILE = 'usage_guide_and_prompts.md' 
 
IMAGE_ARTIFACT_FILE_TEMPLATE = '50_image_{index:02d}_artifact.json' 
IMAGE_URL_POINTER_FILE_TEMPLATE = '60_image_{index:02d}.url' 
 
 
def _build_output_dir(base_dir, request_id): 
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') 
    return Path(base_dir) / f'{timestamp}_{request_id}' 
 
 
def _write_json(path, payload): 
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8') 
 
 
def _build_prompts_payload(response): 
    prompts = [] 
    for image in response.images: 
        prompts.append({'index': image.index, 'name': image.name, 'purpose': image.purpose, 'positive_prompt': image.positive_prompt, 'negative_prompt': image.negative_prompt, 'image_url': str(image.image_url)}) 
    return {'request_id': response.meta.request_id, 'images': prompts}
 
 
def _build_default_image_outputs(response): 
    outputs = [] 
    for image in response.images: 
        url = str(image.image_url) 
        status = 'real' 
        source = 'provider_url' 
        fallback_url = None 
        provider_url = url 
        if url.startswith('https://mock-cdn.local/'): 
            status = 'mock' 
            source = 'mock_provider' 
            provider_url = None 
        elif url.startswith('https://real-images.example/'): 
            status = 'fallback' 
            source = 'fallback_url' 
            provider_url = None 
            fallback_url = url 
        outputs.append({'index': image.index, 'name': image.name, 'output_status': status, 'final_url': url, 'provider_url': provider_url, 'fallback_url': fallback_url, 'source': source, 'provider_error': None}) 
    return outputs 
 
 
def _normalize_image_outputs(response, image_outputs): 
    provided = image_outputs if isinstance(image_outputs, list) else [] 
    if not provided: 
        return _build_default_image_outputs(response) 
 
    normalized = [] 
    by_index = {} 
    for item in provided: 
        if not isinstance(item, dict): 
            continue 
        idx = item.get('index') 
        if isinstance(idx, int): 
            by_index[idx] = item 
 
    for image in response.images: 
        item = by_index.get(image.index, {}) 
        url = str(image.image_url) 
        normalized.append({'index': image.index, 'name': image.name, 'output_status': str(item.get('output_status') or 'real'), 'final_url': str(item.get('final_url') or url), 'provider_url': item.get('provider_url'), 'fallback_url': item.get('fallback_url'), 'source': str(item.get('source') or 'provider_url'), 'provider_error': item.get('provider_error')}) 
    return normalized
 
 
def _build_guide_markdown(response): 
    lines = ['# Usage Guide', '', f'- request_id: {response.meta.request_id}', f'- generated_at: {response.meta.generated_at}', '', response.usage_guide, ''] 
    return '\n'.join(lines) 
 
 
def _build_legacy_guide_with_prompts(response): 
    lines = ['# Usage Guide and Prompts', '', f'- request_id: {response.meta.request_id}', f'- generated_at: {response.meta.generated_at}', '', '## Usage Guide', response.usage_guide, '', '## Image Prompts'] 
    for image in response.images: 
        lines.extend([f'### Image {image.index}: {image.name}', f'Purpose: {image.purpose}', '', 'Positive Prompt:', image.positive_prompt, '', 'Negative Prompt:', image.negative_prompt, '']) 
    return '\n'.join(lines) 
 
 
def _image_artifact_filename(index): 
    return IMAGE_ARTIFACT_FILE_TEMPLATE.format(index=index) 
 
 
def _image_url_pointer_filename(index): 
    return IMAGE_URL_POINTER_FILE_TEMPLATE.format(index=index) 
 
 
def _build_image_artifact_record(output): 
    idx = int(output.get('index') or 0) 
    final_url = str(output.get('final_url') or '') 
    artifact_file = _image_artifact_filename(idx) 
    url_pointer_file = _image_url_pointer_filename(idx) 
    return {'index': idx, 'name': str(output.get('name') or f'Image {idx}'), 'output_status': str(output.get('output_status') or 'real'), 'source': str(output.get('source') or 'provider_url'), 'final_url': final_url, 'provider_url': output.get('provider_url'), 'fallback_url': output.get('fallback_url'), 'provider_error': output.get('provider_error'), 'artifact_file': artifact_file, 'url_pointer_file': url_pointer_file, 'local_image_file': None, 'local_image_status': 'not_saved'}
 
 
def _persist_image_artifact_files(output_dir, normalized_outputs): 
    records = [] 
    for output in normalized_outputs: 
        if not isinstance(output, dict): 
            continue 
        record = _build_image_artifact_record(output) 
        _write_json(output_dir / record['artifact_file'], record) 
        pointer_url = record['final_url'] if isinstance(record['final_url'], str) else '' 
        (output_dir / record['url_pointer_file']).write_text(pointer_url + '\n', encoding='utf-8') 
        records.append(record) 
    return records 
 
 
def _build_image_outputs_payload(response, normalized_outputs, artifact_records): 
    by_index = {} 
    for record in artifact_records: 
        if isinstance(record, dict): 
            by_index[int(record.get('index') or 0)] = record 
 
    images = [] 
    for output in normalized_outputs: 
        if not isinstance(output, dict): 
            continue 
        idx = int(output.get('index') or 0) 
        artifact = by_index.get(idx, {}) 
        item = dict(output) 
        item['artifact_file'] = artifact.get('artifact_file') 
        item['url_pointer_file'] = artifact.get('url_pointer_file') 
        item['local_image_file'] = artifact.get('local_image_file') 
        item['local_image_status'] = artifact.get('local_image_status') 
        images.append(item) 
 
    return {'request_id': response.meta.request_id, 'generated_at': response.meta.generated_at, 'images': images} 
 
 
def _build_manifest(output_dir, response, image_outputs, artifact_records): 
    files = [] 
    for filename, role, content_type in [(MANIFEST_FILE, 'manifest', 'application/json'), (RESPONSE_FILE, 'response_payload', 'application/json'), (PROMPTS_FILE, 'image_prompts', 'application/json'), (GUIDE_FILE, 'usage_guide', 'text/markdown'), (IMAGE_OUTPUTS_FILE, 'image_outputs', 'application/json'), (LEGACY_RESPONSE_FILE, 'legacy_response_payload', 'application/json'), (LEGACY_GUIDE_FILE, 'legacy_usage_guide_and_prompts', 'text/markdown')]: 
        file_path = output_dir / filename 
        files.append({'name': filename, 'role': role, 'content_type': content_type, 'bytes': file_path.stat().st_size if file_path.exists() else 0}) 
 
    for record in artifact_records: 
        artifact_name = record.get('artifact_file') 
        pointer_name = record.get('url_pointer_file') 
        if isinstance(artifact_name, str) and artifact_name: 
            artifact_path = output_dir / artifact_name 
            files.append({'name': artifact_name, 'role': 'image_artifact_record', 'content_type': 'application/json', 'bytes': artifact_path.stat().st_size if artifact_path.exists() else 0}) 
        if isinstance(pointer_name, str) and pointer_name: 
            pointer_path = output_dir / pointer_name 
            files.append({'name': pointer_name, 'role': 'image_url_pointer', 'content_type': 'text/plain', 'bytes': pointer_path.stat().st_size if pointer_path.exists() else 0}) 
 
    status_counts = {'mock': 0, 'fallback': 0, 'real': 0} 
    for item in image_outputs: 
        if not isinstance(item, dict): 
            continue 
        status = str(item.get('output_status') or '') 
        if status in status_counts: 
            status_counts[status] += 1
 
    return {'manifest_version': '1.2', 'request_id': response.meta.request_id, 'generated_at': response.meta.generated_at, 'mode': response.meta.mode, 'product_name': response.product_name, 'product_category': response.product_category, 'output_dir': output_dir.name, 'files': files, 'image_outputs': {'total_images': len(image_outputs), 'status_counts': status_counts, 'records': image_outputs}, 'image_artifacts': {'total': len(artifact_records), 'records': artifact_records}}
 
 
def persist_generation_output(response, base_dir, image_outputs=None): 
    try: 
        output_dir = _build_output_dir(base_dir, response.meta.request_id) 
        output_dir.mkdir(parents=True, exist_ok=True) 
 
        payload = response.model_dump(mode='json') 
        prompts_payload = _build_prompts_payload(response) 
        normalized_outputs = _normalize_image_outputs(response, image_outputs) 
        artifact_records = _persist_image_artifact_files(output_dir, normalized_outputs) 
        outputs_payload = _build_image_outputs_payload(response, normalized_outputs, artifact_records) 
        guide_text = _build_guide_markdown(response) 
        legacy_guide_text = _build_legacy_guide_with_prompts(response) 
 
        _write_json(output_dir / RESPONSE_FILE, payload) 
        _write_json(output_dir / PROMPTS_FILE, prompts_payload) 
        _write_json(output_dir / IMAGE_OUTPUTS_FILE, outputs_payload) 
        (output_dir / GUIDE_FILE).write_text(guide_text, encoding='utf-8') 
 
        _write_json(output_dir / LEGACY_RESPONSE_FILE, payload) 
        (output_dir / LEGACY_GUIDE_FILE).write_text(legacy_guide_text, encoding='utf-8') 
 
        manifest = _build_manifest(output_dir, response, normalized_outputs, artifact_records) 
        _write_json(output_dir / MANIFEST_FILE, manifest) 
        return output_dir 
    except Exception: 
        return None
