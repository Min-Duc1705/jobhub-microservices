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


# ── ResumeAnalysis ─────────────────────────────────────────────────────────────
class ResumeAnalysis(BaseModel):
    """
    Cache kết quả chấm điểm CV bằng AI.
    Được tạo ra khi nhận event ApplicationSubmitted từ ResumeService.
    """
    id:             Optional[PyObjectId] = Field(None, alias="_id")
    application_id: str                  # 1-1 với Application bên ResumeService
    job_id:         str
    customer_id:    str
    matching_score: float               # Cosine Similarity score 0-100%
    extracted_skills: List[str] = []    # Kỹ năng trích xuất được từ CV
    strengths:      List[str] = []      # Điểm mạnh (do LLM sinh)
    weaknesses:     List[str] = []      # Điểm yếu (do LLM sinh)
    ai_feedback:    Optional[str] = None  # Nhận xét tổng thể của LLM
    analyzed_at:    datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ── JobViewHistory ─────────────────────────────────────────────────────────────
class InteractionType(str):
    VIEW  = "VIEW"
    CLICK = "CLICK"
    APPLY = "APPLY"
    SAVE  = "SAVE"


class JobViewHistory(BaseModel):
    """
    Lưu vết hành vi của người dùng với Job.
    Write-heavy: ghi mỗi lần user click/xem/ứng tuyển.
    Phục vụ Recommendation Engine (Matrix Factorization).
    """
    id:               Optional[PyObjectId] = Field(None, alias="_id")
    customer_id:      str
    job_id:           str
    interaction_type: str                # VIEW | CLICK | APPLY | SAVE
    interaction_score: float             # Trọng số: VIEW=1, CLICK=2, APPLY=5, SAVE=3
    timestamp:        datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
