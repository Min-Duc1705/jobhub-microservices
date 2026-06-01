from typing import List
from pydantic import BaseModel


# ── Salary Prediction Schemas ──────────────────────────────────────────────────
class SalaryPredictRequest(BaseModel):
    """Ứng viên nhập thông tin để xem mức lương dự đoán."""
    job_title:           str
    years_of_experience: int
    skill_set:           List[str]
    location:            str
    level:               str          # INTERN | JUNIOR | MIDDLE | SENIOR


class SalaryPredictResponse(BaseModel):
    min_salary:    float              # Triệu VND
    max_salary:    float
    confidence:    float
    model_version: str
    from_cache:    bool = False       # True nếu lấy từ cache MongoDB


# ── Salary Dataset Schemas ─────────────────────────────────────────────────────
class AddSalaryDataRequest(BaseModel):
    """Admin hoặc HR nhập dữ liệu lương thực tế (contribute to dataset)."""
    job_title:           str
    years_of_experience: int
    skill_set:           List[str]
    location:            str
    level:               str
    salary_min:          float
    salary_max:          float
    is_negotiable:       bool = False
    source:              str = "user-input"


# ── Trend Schemas ──────────────────────────────────────────────────────────────
class TrendRequest(BaseModel):
    skill_name: str
    months:     int = 6               # Dự báo bao nhiêu tháng tiếp theo


class TrendDataPoint(BaseModel):
    month:        int
    year:         int
    job_count:    int
    avg_salary:   float


class TrendResponse(BaseModel):
    skill_name:  str
    history:     List[TrendDataPoint]   # Dữ liệu lịch sử đã có
    forecast:    List[TrendDataPoint]   # Dự báo tương lai của Prophet
