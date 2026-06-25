from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MongoDB (lưu trữ logs hành vi và kết quả phân tích CV)
    MONGO_URL: str = "mongodb://root:root@localhost:27017/?authSource=admin"
    MONGO_DB:  str = "CVIntelligenceDB"

    # RabbitMQ (nhận event ApplicationSubmitted từ ResumeService)
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"

    # Gemini API (giai đoạn 2 sinh nhận xét bằng LLM)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"

    # Local AI Settings
    USE_LOCAL_AI: bool = False
    LOCAL_AI_URL: str = "http://host.docker.internal:11434"
    LOCAL_AI_MODEL: str = "gemma4:e4b"

    # SBERT Model - dùng đa ngữ vì dữ liệu có thể là tiếng Việt
    # paraphrase-multilingual-mpnet-base-v2: support tiếng Việt, chính xác cao
    SBERT_MODEL: str = "paraphrase-multilingual-mpnet-base-v2"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
