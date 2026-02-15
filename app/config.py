from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_path: str = "/data/life.db"
    api_key: str = "dev-secret-key"

settings = Settings()
