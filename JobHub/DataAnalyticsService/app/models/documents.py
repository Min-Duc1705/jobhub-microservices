from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)


# ── SalaryDataset ─────────────────────────────────────────────────────────────
class SalaryDataset(BaseModel):
    """
    Dữ liệu training cho mô hình dự đoán lương.
    Thu thập từ crawl, khảo sát, hoặc user tự nhập.
    """
    id:                Optional[PyObjectId] = Field(None, alias="_id")
    job_title:         str
    years_of_experience: int
    skill_set:         List[str] = []     # ["React", "Node.js", "Docker"]
    location:          str                # "Hà Nội", "TP.HCM", "Đà Nẵng"
    level:             str                # INTERN | JUNIOR | MIDDLE | SENIOR
    salary_min:        float              # Mức lương min
    salary_max:        float              # Mức lương max
    is_negotiable:     bool = False       # Lương thỏa thuận
    source:            str = "user-input" # crawl | user-input | survey
    collected_at:      datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ── SalaryPredictionCache ──────────────────────────────────────────────────────
class SalaryPredictionCache(BaseModel):
    """
    Cache kết quả dự đoán lương — tránh re-compute với input giống nhau.
    Hash bộ input (kinh nghiệm + kỹ năng + vị trí) làm khóa tra cứu.
    """
    id:            Optional[PyObjectId] = Field(None, alias="_id")
    input_hash:    str                   # SHA256 của bộ input
    min_salary:    float
    max_salary:    float
    confidence:    float                 # Độ tin cậy 0.0 → 1.0
    model_version: str = "1.0"
    predicted_at:  datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ── JobTrendSnapshot ──────────────────────────────────────────────────────────
class JobTrendSnapshot(BaseModel):
    """
    Snapshot xu hướng tuyển dụng theo tháng cho từng kỹ năng/công nghệ.
    Là input của Prophet/LSTM để dự báo xu hướng tương lai.
    """
    id:           Optional[PyObjectId] = Field(None, alias="_id")
    skill_id:     str
    skill_name:   str                    # Denormalize để query nhanh
    month:        int                    # 1–12
    year:         int
    job_count:    int                    # Số tin tuyển dụng trong tháng có skill này
    avg_salary:   float                  # Lương trung bình
    demand_index: float = 0.0           # Chỉ số nhu cầu mở rộng
    snapshot_at:  datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
