"""Cliente OpenAI-compatible apuntando a DeepInfra."""

from openai import OpenAI

from src.core.config import settings

_client: OpenAI | None = None


def get_client() -> OpenAI:
    """Singleton del cliente OpenAI configurado para DeepInfra."""
    global _client
    if _client is None:
        if not settings.deepinfra_api_token:
            raise RuntimeError(
                "DEEPINFRA_API_TOKEN no está configurado. "
                "Agregalo a api/.env o a la raíz del repo."
            )
        _client = OpenAI(
            api_key=settings.deepinfra_api_token,
            base_url=settings.deepinfra_base_url,
        )
    return _client


def get_model() -> str:
    return settings.llm_model
