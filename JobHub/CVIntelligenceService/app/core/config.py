from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CV Intelligence Service"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "yourpassword"
    POSTGRES_DB: str = "JobHub_AIDb"
    RABBITMQ_URL: str = "amqp://guest:guest@localhost/"

    class Config:
        env_file = ".env"

settings = Settings()
