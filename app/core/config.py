from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_env: str = "dev"

    # Groq
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"

    # Twilio
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_whatsapp_number: str

    # Supabase (ONLY DB YOU NEED)
    supabase_url: str
    supabase_service_role_key: str

    # Embeddings
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    # WhatsApp Meta (optional future)
    whatsapp_verify_token: str = ""
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""


settings = Settings()