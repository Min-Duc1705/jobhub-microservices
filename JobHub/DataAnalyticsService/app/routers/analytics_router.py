from fastapi import APIRouter
from app.schemas.analytics import (
    SalaryPredictRequest,
    SalaryPredictResponse,
    AddSalaryDataRequest,
    TrendRequest,
    TrendResponse,
)
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["Data Analytics"])


# ── Salary Prediction ─────────────────────────────────────────────────────────
@router.post("/salary/predict", response_model=SalaryPredictResponse,
             summary="Dự đoán khoảng lương phù hợp")
async def predict_salary(req: SalaryPredictRequest):
    """
    Ứng viên nhập [Kinh nghiệm + Kỹ năng + Vị trí + Cấp bậc] 
    → AI trả về khoảng lương thị trường (VD: 18 - 25 triệu VND).

    Có **cache layer**: input giống nhau sẽ không tính lại, trả ngay từ cache.
    """
    return await analytics_service.predict(req)


@router.post("/salary/dataset", summary="Đóng góp dữ liệu lương thực tế")
async def add_salary_data(req: AddSalaryDataRequest):
    """
    Admin / HR nhập lương thực tế để mở rộng tập dữ liệu training.
    Sau khi có đủ lượng mẫu mới, chạy script train để cải thiện độ chính xác.
    """
    return await analytics_service.add_salary_data(req)


@router.get("/salary/dataset/stats", summary="Thống kê dataset hiện tại")
async def dataset_stats():
    """Xem số lượng mẫu hiện có trong MongoDB để biết khi nào nên retrain."""
    return await analytics_service.get_dataset_stats()


# ── Job Trend ─────────────────────────────────────────────────────────────────
@router.post("/trend", response_model=TrendResponse,
             summary="Xem xu hướng và dự báo nhu cầu tuyển dụng")
async def get_trend(req: TrendRequest):
    """
    Trả về lịch sử số lượng job và lương trung bình của 1 kỹ năng theo từng tháng,
    kèm dự báo N tháng tiếp theo bằng Moving Average (placeholder cho Prophet/LSTM).
    """
    return await analytics_service.get_trend(req)


@router.post("/trend/snapshot", summary="Ghi snapshot xu hướng tháng này (Internal)")
async def record_snapshot(
    skill_id: str, skill_name: str,
    month: int, year: int,
    job_count: int, avg_salary: float,
):
    """
    Endpoint nội bộ — được gọi bởi Scheduler hoặc khi nhận event `JobPublished` 
    từ JobService để cập nhật dữ liệu xu hướng hàng tháng.
    """
    return await analytics_service.record_trend_snapshot(
        skill_id, skill_name, month, year, job_count, avg_salary
    )
