import os
from dataclasses import dataclass
from enum import Enum


class AppMode(str, Enum):
    MOCK = 'MOCK'
    REAL = 'REAL'


@dataclass(frozen=True)
class Settings:
    mode: AppMode = AppMode.MOCK
    openai_api_key: str = ''
    openai_base_url: str = 'https://api.openai.com/v1'
    llm_model: str = 'gpt-4o-mini'
    image_model: str = 'gpt-image-1'
    outputs_dir: str = 'outputs'


def get_settings() -> Settings:
    raw_mode = os.getenv('APP_MODE', AppMode.MOCK.value).upper()
    try:
        mode = AppMode(raw_mode)
    except ValueError:
        mode = AppMode.MOCK
    return Settings(
        mode=mode,
        openai_api_key=os.getenv('OPENAI_API_KEY', ''),
        openai_base_url=os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1').rstrip('/'),
        llm_model=os.getenv('OPENAI_LLM_MODEL', 'gpt-4o-mini'),
        image_model=os.getenv('OPENAI_IMAGE_MODEL', 'gpt-image-1'),
        outputs_dir=os.getenv('OUTPUTS_DIR', 'outputs'),
    )
