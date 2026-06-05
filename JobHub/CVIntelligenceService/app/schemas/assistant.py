from typing import Optional, List, Any
from pydantic import BaseModel


class AssistantMessage(BaseModel):
    """Một tin nhắn trong lịch sử hội thoại."""
    role: str       # "user" | "model"
    content: str


class AssistantChatRequest(BaseModel):
    """Request gửi từ Frontend để chat với AI Assistant."""
    message: str
    image_base64: Optional[str] = None     # Ảnh dạng base64 (JPG/PNG)
    file_content: Optional[str] = None    # Nội dung file đã extract (PDF/Word text)
    conversation_history: List[AssistantMessage] = []  # Lịch sử chat cho context


class ActionItem(BaseModel):
    """Một hành động cụ thể mà AI đã thực hiện hoặc đề xuất."""
    action_type: str        # "created_job" | "updated_profile" | "found_jobs" | "predicted_salary" | ...
    description: str        # Mô tả ngắn: "Đã tạo tin tuyển dụng Backend Developer"
    data: Optional[Any] = None   # Dữ liệu kết quả từ API (job object, list of jobs, ...)
    requires_confirmation: bool = False   # True = cần user xác nhận trước khi thực hiện
    tool_name: Optional[str] = None       # Tên tool đã gọi


class AssistantChatResponse(BaseModel):
    """Response trả về từ AI Assistant."""
    reply: str                    # Tin nhắn phản hồi ngôn ngữ tự nhiên của AI
    actions_taken: List[ActionItem] = []  # Danh sách các hành động AI đã thực hiện
    pending_action: Optional[ActionItem] = None  # Hành động cần xác nhận (nếu có)
    suggestions: List[str] = []   # Gợi ý câu hỏi tiếp theo
    error: Optional[str] = None   # Lỗi (nếu có)


class AssistantConfirmRequest(BaseModel):
    """User xác nhận thực hiện một pending action."""
    action_type: str
    payload: dict              # Dữ liệu action cần thực hiện
    confirmed: bool = True
