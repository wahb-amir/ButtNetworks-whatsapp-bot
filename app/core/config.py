from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # app
    app_env: str = "dev"
    app_port: int = 8000
    public_base_url: str = "http://localhost:8000"

    # groq
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"

    # meta / whatsapp
    whatsapp_verify_token: str
    whatsapp_access_token: str
    whatsapp_phone_number_id: str
    whatsapp_waba_id: str | None = None
    meta_app_secret: str | None = None

    # db
    database_url: str

    # embeddings / rag
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384
    rag_top_k: int = 4


settings = Settings()