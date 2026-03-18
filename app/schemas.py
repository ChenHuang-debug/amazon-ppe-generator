from enum import Enum
from typing import Any, List, Optional

from pydantic import AnyHttpUrl, BaseModel, Field


class ProductCategory(str, Enum):
    vest = 'vest'
    raincoat = 'raincoat'
    rain_pants = 'rain_pants'
    cap_cover = 'cap_cover'


class PricePoint(str, Enum):
    budget = 'budget'
    mid_range = 'mid-range'
    premium = 'premium'


class PPEGenerateRequest(BaseModel):
    product_name: str = Field(..., min_length=2, max_length=120)
    category: ProductCategory
    colors: List[str] = Field(..., min_length=1, max_length=6)
    reflective_type: str = Field(..., min_length=2, max_length=120)
    certification: str = Field(..., min_length=2, max_length=120)
    features: List[str] = Field(..., min_length=1, max_length=12)
    scenarios: List[str] = Field(..., min_length=1, max_length=8)
    price_level: Optional[PricePoint] = None
    image_url: AnyHttpUrl

    model_config = {
        'json_schema_extra': {
            'example': {
                'product_name': 'High Visibility Reflective Safety Vest',
                'category': 'vest',
                'colors': ['Yellow', 'Silver'],
                'reflective_type': '2-inch silver reflective strips',
                'certification': 'ANSI/ISEA 107 Class 2',
                'features': ['6 pockets', 'zipper front', 'adjustable waist straps'],
                'scenarios': ['construction', 'road work', 'traffic control'],
                'price_level': 'mid-range',
                'image_url': 'https://example.com/reference/vest.jpg'
            }
        }
    }


class GeneratedImage(BaseModel):
    index: int = Field(..., ge=1, le=7)
    name: str
    purpose: str
    image_url: AnyHttpUrl
    positive_prompt: str
    negative_prompt: str


class GenerateMeta(BaseModel):
    request_id: str
    generated_at: str
    mode: str = 'mock'


class PPEGenerateResponse(BaseModel):
    status: str = 'success'
    product_name: str
    product_category: ProductCategory
    images: List[GeneratedImage] = Field(..., min_length=7, max_length=7)
    usage_guide: str
    product_analysis: dict[str, Any]
    meta: GenerateMeta
