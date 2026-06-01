import logging
from datetime import datetime

from app.core.database import (
    get_salary_dataset_col,
    get_salary_cache_col,
    get_job_trend_col,
)
from app.ml.salary_predictor import predict_salary, make_input_hash
from app.models.documents import (
    SalaryDataset,
    SalaryPredictionCache,
    JobTrendSnapshot,
)
from app.schemas.analytics import (
    SalaryPredictRequest,
    SalaryPredictResponse,
    AddSalaryDataRequest,
    TrendRequest,
    TrendResponse,
    TrendDataPoint,
)

logger = logging.getLogger(__name__)


# ── Salary Prediction ─────────────────────────────────────────────────────────
async def predict(req: SalaryPredictRequest) -> SalaryPredictResponse:
    """
    Dự đoán lương với cache:
    1. Tính hash bộ input.
    2. Tra cứu MongoDB — nếu có → trả về cache ngay.
    3. Không có → Gọi XGBoost model predict → Lưu cache → Trả về.
    """
    input_hash = make_input_hash(
        req.job_title, req.years_of_experience, req.skill_set, req.location, req.level
    )

    # Kiểm tra cache
    cache_col = get_salary_cache_col()
    cached = await cache_col.find_one({"input_hash": input_hash})
    if cached:
        logger.info(f"[Salary] Cache hit: {input_hash[:8]}...")
        return SalaryPredictResponse(
            min_salary=cached["min_salary"],
            max_salary=cached["max_salary"],
            confidence=cached["confidence"],
            model_version=cached["model_version"],
            from_cache=True,
        )

    # Cache miss → gọi model
    result = predict_salary(
        req.job_title, req.years_of_experience, req.skill_set, req.location, req.level
    )

    # Lưu vào cache
    cache_doc = SalaryPredictionCache(
        input_hash=input_hash,
        **result,
    )
    await cache_col.insert_one(cache_doc.model_dump(exclude={"id"}))

    return SalaryPredictResponse(**result, from_cache=False)


async def add_salary_data(req: AddSalaryDataRequest) -> dict:
    """Thêm 1 bản ghi lương thực tế vào dataset (để dùng cho lần retrain tiếp theo)."""
    doc = SalaryDataset(
        job_title=req.job_title,
        years_of_experience=req.years_of_experience,
        skill_set=req.skill_set,
        location=req.location,
        level=req.level,
        salary_min=req.salary_min,
        salary_max=req.salary_max,
        is_negotiable=req.is_negotiable,
        source=req.source,
    )
    col = get_salary_dataset_col()
    await col.insert_one(doc.model_dump(exclude={"id"}))
    return {"message": "Đã thêm dữ liệu lương thành công. Dataset hiện có thêm 1 mẫu."}


async def get_dataset_stats() -> dict:
    """Thống kê nhanh dataset hiện tại."""
    col = get_salary_dataset_col()
    total = await col.count_documents({})
    return {"total_samples": total, "message": "Chạy scripts/train_salary_model.py để retrain sau khi có đủ dữ liệu mới."}


# ── Job Trend ─────────────────────────────────────────────────────────────────
async def get_trend(req: TrendRequest) -> TrendResponse:
    """
    Lấy dữ liệu lịch sử xu hướng của 1 kỹ năng từ MongoDB.
    Kết hợp với dự báo đơn giản dựa trên moving average (Prophet training offline).
    """
    col = get_job_trend_col()
    docs = await col.find({"skill_name": req.skill_name}).sort([("year", 1), ("month", 1)]).to_list(length=None)

    history = [
        TrendDataPoint(
            month=d["month"],
            year=d["year"],
            job_count=d["job_count"],
            avg_salary=d["avg_salary"],
        )
        for d in docs
    ]

    # Dự báo đơn giản: Moving Average 3 tháng cuối (sẽ thay bằng Prophet sau khi có đủ data)
    forecast = _simple_moving_avg_forecast(history, months=req.months)

    return TrendResponse(skill_name=req.skill_name, history=history, forecast=forecast)


async def record_trend_snapshot(
    skill_id: str, skill_name: str, month: int, year: int,
    job_count: int, avg_salary: float,
) -> dict:
    """Ghi snapshot tháng này cho 1 kỹ năng (thường gọi bằng Scheduled Task / Event)."""
    col = get_job_trend_col()
    doc = JobTrendSnapshot(
        skill_id=skill_id,
        skill_name=skill_name,
        month=month, year=year,
        job_count=job_count,
        avg_salary=avg_salary,
    )
    await col.replace_one(
        {"skill_id": skill_id, "month": month, "year": year},
        doc.model_dump(exclude={"id"}),
        upsert=True,
    )
    return {"message": "Đã ghi snapshot xu hướng."}


def _simple_moving_avg_forecast(history: list[TrendDataPoint], months: int) -> list[TrendDataPoint]:
    """Dự báo đơn giản Moving Average 3 tháng — placeholder cho Prophet."""
    if len(history) < 3:
        return []
    window = 3
    recent = history[-window:]
    avg_count  = sum(p.job_count for p in recent) / window
    avg_salary = sum(p.avg_salary for p in recent) / window

    result = []
    if history:
        last = history[-1]
        m, y = last.month, last.year
        for _ in range(months):
            m += 1
            if m > 12:
                m = 1
                y += 1
            result.append(TrendDataPoint(
                month=m, year=y,
                job_count=round(avg_count),
                avg_salary=round(avg_salary, 1),
            ))
    return result
