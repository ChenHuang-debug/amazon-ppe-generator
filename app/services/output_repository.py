import json 
from pathlib import Path 
 
MANIFEST_FILE = '00_manifest.json' 
RESPONSE_FILE = '10_response_payload.json' 
PROMPTS_FILE = '30_image_prompts.json' 
IMAGE_OUTPUTS_FILE = '40_image_outputs.json' 
 
 
def _outputs_root(base_dir): 
    return Path(base_dir) 
 
 
def _read_json_file(path): 
    if not path.exists() or not path.is_file(): 
        return None 
    try: 
        data = json.loads(path.read_text(encoding='utf-8')) 
        return data if isinstance(data, dict) else None 
    except (json.JSONDecodeError, ValueError): 
        return None 
 
 
def _extract_available_artifacts(files): 
    roles = [] 
    if isinstance(files, list): 
        for item in files: 
            if not isinstance(item, dict): 
                continue 
            role = item.get('role') 
            if isinstance(role, str) and role and role not in roles: 
                roles.append(role) 
    return roles 
 
 
def _classify_url_status(url): 
    if not isinstance(url, str) or not url: 
        return 'real' 
    if url.startswith('https://mock-cdn.local/'): 
        return 'mock' 
    if url.startswith('https://real-images.example/'): 
        return 'fallback' 
    return 'real' 
 
 
def _count_statuses(records): 
    counts = {'mock': 0, 'fallback': 0, 'real': 0} 
    total = 0  
    for rec in records: 
        if not isinstance(rec, dict): 
            continue 
        status = rec.get('output_status') 
        if not isinstance(status, str) or status not in counts: 
            url = rec.get('final_url') or rec.get('image_url') or '' 
            status = _classify_url_status(str(url)) 
        counts[status] += 1
        total += 1
    return counts, total
 
 
def _load_image_records(folder, manifest): 
    image_outputs_payload = _read_json_file(folder / IMAGE_OUTPUTS_FILE) 
    if isinstance(image_outputs_payload, dict): 
        images = image_outputs_payload.get('images') 
        if isinstance(images, list): 
            return [item for item in images if isinstance(item, dict)] 
 
    image_outputs = manifest.get('image_outputs') if isinstance(manifest, dict) else None 
    if isinstance(image_outputs, dict): 
        records = image_outputs.get('records') 
        if isinstance(records, list): 
            return [item for item in records if isinstance(item, dict)] 
 
    response_payload = _read_json_file(folder / RESPONSE_FILE) 
    if isinstance(response_payload, dict): 
        images = response_payload.get('images') 
        if isinstance(images, list): 
            normalized = [] 
            for item in images: 
                if not isinstance(item, dict): 
                    continue 
                normalized.append({'image_url': item.get('image_url')}) 
            return normalized 
 
    return [] 
 
 
def _fallback_total_from_prompts(folder): 
    prompts_payload = _read_json_file(folder / PROMPTS_FILE) 
    if not isinstance(prompts_payload, dict): 
        return 0  
    images = prompts_payload.get('images') 
    if isinstance(images, list): 
        return len([item for item in images if isinstance(item, dict)]) 
    return 0  
 
 
def _normalize_mode(mode): 
    if isinstance(mode, str) and mode: 
        lowered = mode.lower() 
        if lowered in ('mock', 'real'): 
            return lowered 
    return None 
 
 
def _derive_summary(folder, manifest): 
    records = _load_image_records(folder, manifest) 
    counts, total_images = _count_statuses(records) 
 
    if total_images == 0 and isinstance(manifest, dict): 
        image_outputs = manifest.get('image_outputs') 
        if isinstance(image_outputs, dict): 
            status_counts = image_outputs.get('status_counts') 
            if isinstance(status_counts, dict): 
                for key in ('mock', 'fallback', 'real'): 
                    value = status_counts.get(key) 
                    if isinstance(value, int) and not value < 0: 
                        counts[key] = value 
                total_images = counts['mock'] + counts['fallback'] + counts['real'] 
            raw_total = image_outputs.get('total_images') 
            if isinstance(raw_total, int) and not raw_total < 0 and total_images == 0: 
                total_images = raw_total 
 
    if total_images == 0: 
        total_images = _fallback_total_from_prompts(folder) 
 
    raw_mode = _normalize_mode(manifest.get('mode') if isinstance(manifest, dict) else None) 
    if counts['real'] > 0 or counts['fallback'] > 0: 
        mode = 'real' 
    elif counts['mock'] > 0: 
        mode = 'mock' 
    else: 
        mode = raw_mode 
 
    if mode == 'mock' and total_images > 0 and counts['mock'] == 0: 
        counts = {'mock': total_images, 'fallback': 0, 'real': 0} 
    elif mode == 'real' and total_images > 0 and counts['mock'] == 0 and counts['fallback'] == 0 and counts['real'] == 0: 
        counts = {'mock': 0, 'fallback': total_images, 'real': 0} 
 
    return mode, total_images, counts
 
 
def _find_request_dirs(base_dir, request_id): 
    root = _outputs_root(base_dir) 
    if not root.exists(): 
        return [] 
    matches = [p for p in root.iterdir() if p.is_dir() and p.name.endswith(f'_{request_id}')] 
    matches.sort(key=lambda x: x.name, reverse=True) 
    return matches 
 
 
def find_request_dir(base_dir, request_id): 
    matches = _find_request_dirs(base_dir, request_id) 
    return matches[0] if matches else None 
 
 
def list_recent_outputs(base_dir, limit=20): 
    root = _outputs_root(base_dir) 
    if not root.exists(): 
        return [] 
 
    folders = [p for p in root.iterdir() if p.is_dir()] 
    folders.sort(key=lambda x: x.name, reverse=True) 
 
    items = [] 
    for folder in folders[: max(1, limit)]: 
        request_id = folder.name.split('_')[-1] if '_' in folder.name else folder.name 
        manifest_path = folder / MANIFEST_FILE 
        manifest = _read_json_file(manifest_path) if manifest_path.exists() else None 
 
        generated_at = manifest.get('generated_at') if isinstance(manifest, dict) else None 
        product_name = manifest.get('product_name') if isinstance(manifest, dict) else None 
        if isinstance(manifest, dict): 
            request_id = str(manifest.get('request_id') or request_id) 
 
        mode, total_images, image_status_counts = _derive_summary(folder, manifest) 
        available_artifacts = _extract_available_artifacts(manifest.get('files')) if isinstance(manifest, dict) else [] 
 
        items.append({ 
            'request_id': request_id, 
            'folder': folder.name, 
            'generated_at': generated_at, 
            'manifest_available': manifest_path.exists(), 
            'mode': mode, 
            'product_name': product_name, 
            'total_images': total_images, 
            'image_status_counts': image_status_counts, 
            'available_artifacts': available_artifacts, 
        }) 
    return items 
 
 
def load_manifest(base_dir, request_id): 
    request_dir = find_request_dir(base_dir, request_id) 
    if not request_dir: 
        return None 
    return _read_json_file(request_dir / MANIFEST_FILE) 
 
 
def resolve_artifact_file(base_dir, request_id, filename): 
    if Path(filename).name != filename: 
        return None 
    request_dir = find_request_dir(base_dir, request_id) 
    if not request_dir: 
        return None 
    file_path = request_dir / filename 
    if not file_path.exists() or not file_path.is_file(): 
        return None 
    return file_path 
 
 
def resolve_manifest_artifacts(base_dir, request_id): 
    manifest = load_manifest(base_dir, request_id) 
    if not manifest: 
        return None 
 
    files = manifest.get('files', []) 
    if not isinstance(files, list): 
        return None 
 
    resolved = [] 
    missing = [] 
    for item in files: 
        if not isinstance(item, dict): 
            continue 
        name = item.get('name') 
        if not isinstance(name, str) or not name: 
            continue 
        path = resolve_artifact_file(base_dir, request_id, name) 
        if path: 
            resolved.append(path) 
        else: 
            missing.append(name) 
 
    return resolved, missing
