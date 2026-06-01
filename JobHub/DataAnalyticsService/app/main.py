import logging
import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.routers import analytics_router
from app.services.rabbitmq_consumer import start_rabbitmq_consumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi chạy rabbitmq consumer dưới dạng background task
    loop = asyncio.get_event_loop()
    task = loop.create_task(start_rabbitmq_consumer())
    yield
    # Hủy task khi app tắt
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="Data Analytics Service",
    description=(
        "AI Service phân tích dữ liệu thị trường tuyển dụng.\n\n"
        "**Chức năng:**\n"
        "- Dự đoán mức lương (XGBoost Regression) với cache MongoDB\n"
        "- Phân tích xu hướng tuyển dụng theo kỹ năng/công nghệ\n"
        "- Quản lý tập dữ liệu lương thực tế (SalaryDataset)\n\n"
        "**Cách train model lương:**\n"
        "1. Thêm data qua `POST /api/v1/analytics/salary/dataset`\n"
        "2. Chạy: `python scripts/train_salary_model.py`\n"
        "3. Restart service để load model mới"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.include_router(analytics_router.router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "DataAnalyticsService", "port": 5007}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5007, reload=False)
