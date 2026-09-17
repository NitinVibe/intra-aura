from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    secret_key: str
    admin_username: str
    admin_password: str

    # Optional SMTP settings used only for customer authentication OTP email.
    # Existing .env values remain unchanged; these are added only when email OTP
    # is enabled for the deployment.
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = None
    SMTP_USE_TLS: bool = True

    # Optional Cloudinary image storage. When configured, uploaded media/product
    # images are stored permanently outside the Vercel filesystem.
    CLOUDINARY_CLOUD_NAME: str | None = None
    CLOUDINARY_API_KEY: str | None = None
    CLOUDINARY_API_SECRET: str | None = None
    OTP_EXPIRY_MINUTES: int = 10
    OTP_RESEND_COOLDOWN_SECONDS: int = 60
    OTP_MAX_ATTEMPTS: int = 5
    OTP_MAX_RESENDS: int = 5
    LOGIN_MAX_FAILED_ATTEMPTS: int = 5
    LOGIN_LOCK_MINUTES: int = 15

    class Config:
        env_file = ".env"


settings = Settings()