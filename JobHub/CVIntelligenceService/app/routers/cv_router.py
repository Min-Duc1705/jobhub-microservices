from fastapi import APIRouter
from app.schemas.cv_scoring import (
    CvScoringRequest,
    SkillScoringRequest,
    BatchScoringResponse,
    ScoringResult,
    TrackInteractionRequest,
)
from app.services import cv_service

router = APIRouter(prefix="/cv", tags=["CV Intelligence"])


@router.post("/score", summary="Chấm điểm 1 CV với JD")
async def score_one(req: CvScoringRequest):
    """
    **Stage 1 + Stage 2:**
    - SBERT tính % phù hợp giữa CV và JD.
    - Nếu score >= 50% → LLM sinh nhận xét chi tiết (điểm mạnh/yếu).
    - Kết quả được lưu vào MongoDB (ResumeAnalysis) nếu truyền đủ application_id, job_id, customer_id.
    """
    res = await cv_service.score_single_cv(req)
    return {
        "statusCode": 200,
        "message": "Chấm điểm CV thành công",
        "data": res
    }


@router.post("/score/batch", summary="Chấm điểm hàng loạt CVs")
async def score_batch(req: SkillScoringRequest, top_n: int = 10):
    """
    **Pipeline 2 bước chuẩn công nghiệp:**
    1. SBERT chấm tất cả CVs trên GPU cực nhanh.
    2. Chỉ top_n CV điểm cao nhất mới được LLM sinh nhận xét chi tiết.

    Phù hợp khi NTD cần lọc hàng trăm/nghìn CV cùng lúc.
    """
    res = await cv_service.batch_score(req, top_n=top_n)
    return {
        "statusCode": 200,
        "message": "Chấm điểm hàng loạt CV thành công",
        "data": res
    }


@router.get("/analyses/{job_id}", summary="Xem kết quả xếp hạng CV của 1 Job")
async def get_job_analyses(job_id: str):
    """
    Trả về danh sách kết quả phân tích CV của tất cả ứng viên ứng tuyển vào Job này,
    sắp xếp theo matching_score giảm dần. NTD dùng màn hình này để ra quyết định phỏng vấn.
    """
    res = await cv_service.get_analyses_by_job(job_id)
    return {
        "statusCode": 200,
        "message": "Lấy danh sách phân tích kết quả xếp hạng CV thành công",
        "data": res
    }


@router.post("/track", summary="Ghi log hành vi người dùng với Job")
async def track(req: TrackInteractionRequest):
    """
    Ghi nhận hành vi VIEW / CLICK / SAVE / APPLY của ứng viên.
    Dữ liệu này được tích lũy trong MongoDB để sau dùng cho Recommendation Engine.
    """
    return await cv_service.track_interaction(req)


@router.post("/recommendations", summary="Gợi ý việc làm thông minh dựa trên CV")
async def recommend_jobs(req: dict):
    """
    Nhận cv_text và customer_id từ frontend và trả về danh sách job phù hợp nhất từ JobService.
    """
    cv_text = req.get("cv_text", "")
    customer_id = req.get("customer_id")
    res = await cv_service.recommend_jobs_for_candidate(cv_text, customer_id)
    return {
        "statusCode": 200,
        "message": "Gợi ý việc làm thành công",
        "data": res
    }
