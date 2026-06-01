import motor.motor_asyncio
from app.config import settings

# Motor — async MongoDB driver
_client: motor.motor_asyncio.AsyncIOMotorClient | None = None


def get_client() -> motor.motor_asyncio.AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URL)
    return _client


def get_db():
    return get_client()[settings.MONGO_DB]


# ── Collection shortcuts ──────────────────────────────────────────────────────
def get_resume_analysis_col():
    return get_db()["resume_analyses"]


def get_job_view_history_col():
    return get_db()["job_view_histories"]
