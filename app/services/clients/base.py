from abc import ABC, abstractmethod

from app.schemas import GeneratedImage, PPEGenerateRequest


class BaseLLMClient(ABC):
    @abstractmethod
    def generate_product_analysis(self, payload: PPEGenerateRequest) -> dict[str, object]:
        raise NotImplementedError

    @abstractmethod
    def generate_image_prompts(
        self,
        payload: PPEGenerateRequest,
        analysis: dict[str, object],
    ) -> list[dict[str, str]]:
        raise NotImplementedError

    @abstractmethod
    def generate_usage_guide(
        self,
        payload: PPEGenerateRequest,
        images: list[GeneratedImage],
    ) -> str:
        raise NotImplementedError


class BaseImageClient(ABC):
    @abstractmethod
    def generate_images(
        self,
        request_id: str,
        prompts: list[dict[str, str]],
        payload: PPEGenerateRequest,
    ) -> list[GeneratedImage]:
        raise NotImplementedError
