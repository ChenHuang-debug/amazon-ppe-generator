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


def test_health_returns_200() -> None:
    client = TestClient(app)
    response = client.get('/health')

    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_generate_mock_mode_returns_200_and_7_images(monkeypatch) -> None:
    monkeypatch.setenv('APP_MODE', 'MOCK')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    client = TestClient(app)

    response = client.post('/generate', json=_valid_payload())
    body = response.json()

    assert response.status_code == 200
    assert len(body['images']) == 7
    assert body['images'][0]['image_url'].startswith('https://mock-cdn.local/')
    assert set(body.keys()) == {
        'status',
        'product_name',
        'product_category',
        'images',
        'usage_guide',
        'product_analysis',
        'meta',
    }


def test_generate_real_mode_without_key_uses_fallback_urls(monkeypatch) -> None:
    monkeypatch.setenv('APP_MODE', 'REAL')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    client = TestClient(app)

    response = client.post('/generate', json=_valid_payload())
    body = response.json()

    assert response.status_code == 200
    assert len(body['images']) == 7
    assert body['images'][0]['image_url'].startswith('https://real-images.example/')


def test_generate_without_image_url_returns_422(monkeypatch) -> None:
    monkeypatch.setenv('APP_MODE', 'MOCK')
    client = TestClient(app)
    payload = _valid_payload()
    payload.pop('image_url')

    response = client.post('/generate', json=payload)

    assert response.status_code == 422
