from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Équivalent de application.yml + ExternalApiConfiguration (variables `OMNI_*`)."""

    model_config = SettingsConfigDict(env_prefix="OMNI_")

    database_url: str = "sqlite+pysqlite:///:memory:"
    show_sql: bool = True

    impactco2_base_url: str = "https://impactco2.fr/api/v1"
    external_api_connect_timeout: float = 5.0
    external_api_read_timeout: float = 10.0
