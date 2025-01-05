from pydantic_settings import BaseSettings
import os


class Config(BaseSettings):
    db_user: str = os.getenv("DB_USER")
    db_password: str = os.getenv("DB_PASSWORD")
    db_host: str = os.getenv("DB_HOST")
    db_port: int = int(os.getenv("DB_PORT", 5432))
    db_name: str = os.getenv("DB_NAME")
    model_directory: str = os.getenv("MODEL_DIRECTORY", "models")
    model_version: str = os.getenv("MODEL_VERSION", "v1")
    DATABASE_URL: str = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    MODEL_PATH: str = f"{model_directory}/{model_version}"

    class Config:
        extra = "allow"
        env_file = ".env"


config = Config()
