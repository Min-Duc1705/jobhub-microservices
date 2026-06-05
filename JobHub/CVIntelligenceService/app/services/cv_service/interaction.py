# app/services/cv_service/interaction.py
"""
Ghi log và truy vấn hành vi tương tác của người dùng với các Job.
"""
import logging
from datetime import datetime

from app.core.database import get_resume_analysis_col, get_job_view_history_col
from app.models.documents import JobViewHistory
from app.schemas.cv_scoring import TrackInteractionRequest

logger = logging.getLogger(__name__)

# Điểm số cho từng loại tương tác
_INTERACTION_SCORES = {
    "VIEW":  1.0,
    "CLICK": 2.0,
    "SAVE":  3.0,
    "APPLY": 5.0,
}


async def track_interaction(req: TrackInteractionRequest) -> dict:
    """Ghi log hành vi người dùng với Job (VIEW/CLICK/SAVE/APPLY)."""
    score = _INTERACTION_SCORES.get(req.interaction_type.upper(), 1.0)
    doc = JobViewHistory(
        customer_id=req.customer_id,
        job_id=req.job_id,
        interaction_type=req.interaction_type.upper(),
        interaction_score=score,
        timestamp=datetime.utcnow(),
    )
    col = get_job_view_history_col()
    await col.insert_one(doc.model_dump(exclude={"id"}))
    return {"message": "Ghi log thành công"}


async def get_analyses_by_job(job_id: str) -> list:
    """Lấy tất cả kết quả phân tích CV của 1 Job — HR dùng để xem bảng xếp hạng."""
    col = get_resume_analysis_col()
    docs = await col.find({"job_id": job_id}).sort("matching_score", -1).to_list(length=None)
    for doc in docs:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
    return docs
