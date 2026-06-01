from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MongoDB (lưu SalaryDataset, SalaryPredictionCache, JobTrendSnapshot)
    MONGO_URL: str = "mongodb://root:root@localhost:27017/?authSource=admin"
    MONGO_DB:  str = "DataAnalyticsDB"

    # RabbitMQ (nhận event JobPublished từ JobService để cập nhật TrendSnapshot)
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"

    # Đường dẫn lưu file model đã train
    MODEL_PATH: str = "app/ml/artifacts/salary_model.pkl"

    class Config:
        env_file = ".env"

settings = Settings()
