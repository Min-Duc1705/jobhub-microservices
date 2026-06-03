from fastapi import APIRouter
from app.schemas.hire_agent import HireAgentChatRequest, HireAgentChatResponse
from app.services import hire_agent_service

router = APIRouter(prefix="/cv/hire-agent", tags=["Hire Agent"])

@router.post("/chat", response_model=HireAgentChatResponse, summary="Xử lý hội thoại phỏng vấn sàng lọc ảo")
async def chat_screening(req: HireAgentChatRequest):
    history = [msg.model_dump() for msg in req.chat_history]
    res = await hire_agent_service.process_screening_chat(
        job_description=req.job_description,
        cv_text=req.cv_text,
        chat_history=history,
        recruiter_name=req.recruiter_name,
        company_name=req.company_name,
        job_name=req.job_name,
        job_url=req.job_url
    )
    return HireAgentChatResponse(
        reply=res.get("reply", "Đã xảy ra sự cố khi kết nối với AI Agent. Vui lòng thử lại sau."),
        is_completed=res.get("is_completed", False),
        is_passed=res.get("is_passed", False)
    )
