from typing import List, Optional
from pydantic import BaseModel

class ChatMessage(BaseModel):
    sender: str
    content: str

class HireAgentChatRequest(BaseModel):
    job_description: str
    cv_text: str
    chat_history: List[ChatMessage]
    recruiter_name: Optional[str] = None
    company_name: Optional[str] = None
    job_name: Optional[str] = None
    job_url: Optional[str] = None

class HireAgentChatResponse(BaseModel):
    reply: str
    is_completed: bool
    is_passed: bool
