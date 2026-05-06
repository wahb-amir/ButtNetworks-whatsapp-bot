from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # app
    app_env: str = "dev"

    # groq
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"

    # whatsapp
    whatsapp_verify_token: str
    whatsapp_access_token: str
    whatsapp_phone_number_id: str

    supabase_url: str
    supabase_service_role_key: str

    # embeddings
    embedding_model: str = "BAAI/bge-small-en-v1.5"


settings = Settings()