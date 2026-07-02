from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # Auth
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Uploads (comprovantes). Absolute in Docker (WORKDIR /app); override via
    # env em ambientes onde /app nao e gravavel (ex.: CI).
    UPLOAD_DIR: str = "/app/uploads"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # SMTP
    SMTP_HOST: str = "mailpit"
    SMTP_PORT: int = 1025
    SMTP_FROM_EMAIL: str = "noreply@gestorcustos.local"

    # Notification settings
    DAYS_BEFORE_DUE_NOTIFICATION: int = 3

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    FRONTEND_URL: str = "http://localhost:5173"

    # Admin
    ADMIN_SECRET_KEY: str | None = None

    # Evolution API (WhatsApp)
    EVOLUTION_API_URL: str = "http://localhost:8080"
    EVOLUTION_API_KEY: str = ""
