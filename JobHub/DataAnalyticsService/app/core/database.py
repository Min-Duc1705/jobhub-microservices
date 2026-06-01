import motor.motor_asyncio
from app.config import settings

_client: motor.motor_asyncio.AsyncIOMotorClient | None = None


def get_client():
    global _client
    if _client is None:
        _client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URL)
    return _client


def get_db():
    return get_client()[settings.MONGO_DB]


def get_salary_dataset_col():
    return get_db()["salary_datasets"]


def get_salary_cache_col():
    return get_db()["salary_prediction_caches"]


def get_job_trend_col():
    return get_db()["job_trend_snapshots"]
