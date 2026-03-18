import json
from urllib import error, request


def post_json(
    endpoint: str,
    body: dict[str, object],
    api_key: str,
    timeout: int,
) -> dict[str, object] | None:
    try:
        req = request.Request(
            endpoint,
            data=json.dumps(body).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        with request.urlopen(req, timeout=timeout) as resp:
            raw = json.loads(resp.read().decode('utf-8'))
        return raw if isinstance(raw, dict) else None
    except (error.URLError, error.HTTPError, TimeoutError, json.JSONDecodeError, ValueError):
        return None


def parse_chat_content(raw: dict[str, object]) -> str | None:
    output_text = raw.get('output_text')
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    choices = raw.get('choices')
    if not isinstance(choices, list) or not choices:
        return None
    first = choices[0] if isinstance(choices[0], dict) else {}
    message = first.get('message', {}) if isinstance(first, dict) else {}
    content = message.get('content') if isinstance(message, dict) else None

    if isinstance(content, str) and content.strip():
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            text_val = item.get('text')
            if isinstance(text_val, str) and text_val.strip():
                parts.append(text_val)
        if parts:
            return '\n'.join(parts)
    return None


def normalize_prompt_items(
    raw_items: list[object],
    default_names: list[str],
    default_purposes: list[str],
) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for i in range(1, 8):
        raw = raw_items[i - 1] if i - 1 < len(raw_items) else {}
        item = raw if isinstance(raw, dict) else {}
        normalized.append({
            'index': str(safe_int(item.get('index'), i)),
            'name': str(item.get('name') or default_names[i - 1]),
            'purpose': str(item.get('purpose') or default_purposes[i - 1]),
            'positive_prompt': str(item.get('positive_prompt') or ''),
            'negative_prompt': str(item.get('negative_prompt') or 'text, watermark, logo, blur, low quality'),
        })
    return normalized


def safe_int(value: object, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def extract_image_url(raw: dict[str, object]) -> str | None:
    data = raw.get('data')
    if not isinstance(data, list) or not data:
        return None
    first = data[0] if isinstance(data[0], dict) else {}
    url = first.get('url') if isinstance(first, dict) else None
    if isinstance(url, str) and url.startswith('http'):
        return url
    return None


def build_fallback_image_url(request_id: str, idx: int) -> str:
    return f'https://real-images.example/{request_id}/image_{idx}.png'
