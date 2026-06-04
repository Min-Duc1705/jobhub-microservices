from typing import Optional, List
from pydantic import BaseModel


# ── CV Scoring Schemas ─────────────────────────────────────────────────────────
class CvScoringRequest(BaseModel):
    """HTTP request thủ công: NTD gửi JD + CV text để chấm điểm ngay."""
    job_description:   str
    cv_text:           str
    application_id:    Optional[str] = None
    job_id:            Optional[str] = None
    customer_id:       Optional[str] = None
    generate_feedback: Optional[bool] = True


class SkillScoringRequest(BaseModel):
    """Chấm điểm hàng loạt: 1 JD + nhiều CVs."""
    job_description: str
    cv_list: List[dict]  # [{"application_id": ..., "cv_text": ...}]


class ScoringResult(BaseModel):
    application_id:  Optional[str] = None
    matching_score:  float
    ai_feedback:     Optional[str] = None
    extracted_skills: List[str] = []
    strengths:       List[str] = []
    weaknesses:      List[str] = []


class BatchScoringResponse(BaseModel):
    results:    List[ScoringResult]
    top_count:  int


# ── Job View History Schemas ───────────────────────────────────────────────────
class TrackInteractionRequest(BaseModel):
    customer_id:      str
    job_id:           str
    interaction_type: str  # VIEW | CLICK | APPLY | SAVE
