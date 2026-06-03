import asyncio
import logging

import uvicorn
from fastapi import FastAPI

from app.routers import cv_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CV Intelligence Service",
    description=(
        "AI Service phân tích và chấm điểm CV.\n\n"
        "**Chức năng:**\n"
        "- Chấm điểm CV vs Job Description bằng SBERT (multilingual, hỗ trợ tiếng Việt)\n"
        "- Sinh nhận xét chuyên sâu bằng LLM (Gemini 2.5 Flash)\n"
        "- Ghi log hành vi người dùng (JobViewHistory) cho Recommendation\n\n"
        "**Luồng tự động:**\n"
        "Khi ứng viên nộp CV bên ResumeService → Event `ApplicationSubmitted` → "
        "Service này tự động chấm điểm và lưu vào MongoDB."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Register Routers ───────────────────────────────────────────────────────────
from app.routers import hire_agent_router
app.include_router(cv_router.router, prefix="/api/v1")
app.include_router(hire_agent_router.router, prefix="/api/v1")


# ── Lifecycle Events ───────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    """Khởi động các tác vụ chạy ngầm khi service bật lên."""
    from app.consumers.application_consumer import start_consumer
    asyncio.create_task(start_consumer())

    # Khởi chạy vòng lặp huấn luyện SVD định kỳ chạy ngầm (mỗi 4 tiếng)
    from app.services.cv_service import start_periodic_svd_training
    asyncio.create_task(start_periodic_svd_training())

    logger.info("[Startup] CVIntelligenceService đã sẵn sàng!")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "CVIntelligenceService", "port": 5006}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5006, reload=False)
