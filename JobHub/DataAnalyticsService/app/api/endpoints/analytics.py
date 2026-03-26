from fastapi import APIRouter
from pydantic import BaseModel

class SalaryPredictionRequest(BaseModel):
    experience_years: int
    skills: list[str]
    position: str

class SalaryPredictionResponse(BaseModel):
    min_salary: float
    max_salary: float

router = APIRouter()

@router.post("/predict-salary", response_model=SalaryPredictionResponse)
async def predict_salary(request: SalaryPredictionRequest):
    return SalaryPredictionResponse(min_salary=15000000, max_salary=22000000)
