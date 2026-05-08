from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

API_DIR = Path(__file__).parent
ROOT_DIR = API_DIR.parent

_env_in_api = API_DIR / ".env"
_env_in_root = ROOT_DIR / ".env"
_env_file = str(_env_in_api if _env_in_api.exists() else _env_in_root)


class Settings(BaseSettings):
    # MongoDB
    mongo_uri: str = "mongodb://mongo:27017"

    # Datasets
    dataset_contratos_id: str = "jbjy-vk9h"
    dataset_archivos_id: str = "dmgg-8hin"

    # JWT
    jwt_secret_key: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # CORS — valor en .env como string separado por comas
    cors_origins: str = "*"

    # Socrata
    socrata_app_token: str = ""

    # IA · DeepInfra (OpenAI-compatible API)
    deepinfra_api_token: str = ""
    deepinfra_base_url: str = "https://api.deepinfra.com/v1/openai"
    llm_model: str = "meta-llama/Llama-3.3-70B-Instruct"

    def get_cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    model_config = SettingsConfigDict(
        env_file=_env_file,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
