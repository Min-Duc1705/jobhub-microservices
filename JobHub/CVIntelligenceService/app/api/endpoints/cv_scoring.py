from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel

class ScoreResponse(BaseModel):
    score: float
    feedback: str

router = APIRouter()

@router.post("/score-cv", response_model=ScoreResponse)
async def score_cv(job_description: str, cv_file: UploadFile = File(...)):
    content = await cv_file.read()
    score = 85.5
    feedback = "Ứng viên phù hợp với yêu cầu mô tả."
    return ScoreResponse(score=score, feedback=feedback)
