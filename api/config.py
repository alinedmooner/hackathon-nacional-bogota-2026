from pydantic_settings import BaseSettings


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

    def get_cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
