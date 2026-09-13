from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    secret_key: str
    admin_username: str
    admin_password: str

    class Config:
        env_file = ".env"


settings = Settings()