import json
import logging
import google.generativeai as genai
from app.ml.llm_generator import _load_api_keys, GEMINI_MODELS

logger = logging.getLogger(__name__)

_PROMPT_TEMPLATE = """
Bạn là một Trợ lý AI đại diện cho chuyên viên tuyển dụng "{recruiter_name_val}" thuộc công ty "{company_name_val}" trên hệ thống JobHub.
Nhiệm vụ của bạn là thực hiện cuộc phỏng vấn sàng lọc sơ bộ (screening interview) với ứng viên dựa trên Mô tả công việc (JD) và CV của họ.

=== MÔ TẢ CÔNG VIỆC (JD) ===
{job_description}

=== CV ỨNG VIÊN ===
{cv_text}

=== LỊCH SỬ CHAT (Theo thứ tự thời gian) ===
{chat_history_str}

=== THÔNG TIN NHÀ TUYỂN DỤNG & CÔNG VIỆC ===
{meta_info_str}

=== HƯỚNG DẪN KỊCH BẢN PHỎNG VẤN SÀNG LỌC ===
1. Nếu Lịch sử chat trống (chưa có tin nhắn nào từ ứng viên): Hãy sinh tin nhắn mở đầu (Welcome) tự nhiên, lịch sự, cá nhân hóa dựa trên CV của ứng viên.
   - BẮT BUỘC: Bạn phải tự giới thiệu mình là "Trợ lý AI đại diện cho {recruiter_name_val} thuộc {company_name_val}".
   - BẮT BUỘC: Bạn phải đề cập rõ tên công việc ứng tuyển là "{job_name_val}".
   - BẮT BUỘC: Bạn phải cung cấp liên kết xem chi tiết công việc cho ứng viên tại: {job_url_val}.
   - Hãy gửi lời chào ấn tượng, đánh giá sơ bộ vài điểm sáng trong CV của họ khớp với JD, và mời họ chia sẻ mức lương mong muốn (Gross) và thời gian sớm nhất có thể bắt đầu để khởi đầu quy trình sàng lọc sơ bộ.
2. Nếu cuộc phỏng vấn đang diễn ra:
   - Hãy đọc câu trả lời mới nhất của ứng viên. Đặt câu hỏi tiếp theo (mỗi lần chỉ hỏi đúng 1 câu) để làm rõ các thông tin cốt lõi (ví dụ: Mức lương mong muốn, thời gian có thể đi làm, kỹ năng kỹ thuật chính).
   - Hãy phỏng vấn tự nhiên, ngắn gọn, tối đa 3-4 câu hỏi là phải kết luận.
3. Khi đã thu thập đủ thông tin (hoặc lịch sử chat đã có từ 6 tin nhắn trở lên bao gồm cả của Agent và Ứng viên):
   - Đánh dấu "is_completed" = true.
   - Quyết định ứng viên Đạt ("is_passed" = true) hay Không đạt ("is_passed" = false). Để đạt, mức lương mong muốn phải hợp lý và kỹ năng cốt lõi phải khớp tốt với JD.
   - Sinh tin nhắn kết luận ("reply"): 
     + Nếu ĐẠT: Chúc mừng ứng viên và báo rằng họ được chuyển tiếp đến vòng đặt lịch phỏng vấn chính thức.
     + Nếu KHÔNG ĐẠT: Cảm ơn và từ chối một cách lịch sự, tinh tế nhất.

=== YÊU CẦU ĐẦU RA (PURE JSON - KHÔNG markdown ```json) ===
{{
  "reply": "Nội dung câu hỏi tiếp theo hoặc tin nhắn kết luận của bạn",
  "is_completed": false, // hoặc true nếu đã kết thúc phỏng vấn sàng lọc
  "is_passed": false // hoặc true nếu is_completed = true và ứng viên đạt yêu cầu
}}
"""

async def process_screening_chat(
    job_description: str,
    cv_text: str,
    chat_history: list,
    recruiter_name: str = None,
    company_name: str = None,
    job_name: str = None,
    job_url: str = None
) -> dict:
    default_empty = {
        "reply": "Xin lỗi, đã xảy ra sự cố khi kết nối với AI Agent. Vui lòng thử lại sau.",
        "is_completed": False,
        "is_passed": False
    }

    keys = _load_api_keys()
    if not keys:
        logger.warning("[HireAgent] Không có API Key nào được cấu hình.")
        return default_empty

    # Định dạng lịch sử chat thành dạng chuỗi dễ đọc cho AI
    history_lines = []
    for msg in chat_history:
        sender = "Agent (Bạn)" if msg.get("sender", "").lower() == "agent" else "Ứng viên"
        content = msg.get("content", "")
        history_lines.append(f"{sender}: {content}")
    chat_history_str = "\n".join(history_lines) if history_lines else "(Trống - Chưa bắt đầu trò chuyện)"

    # Format meta info
    meta_info_str = f"HR phụ trách: {recruiter_name or 'Chưa rõ'}\nCông ty: {company_name or 'Chưa rõ'}\nTên Job: {job_name or 'Chưa rõ'}\nLink Job: {job_url or 'Chưa rõ'}"

    recruiter_name_val = recruiter_name if recruiter_name else "chuyên viên nhân sự"
    company_name_val = company_name if company_name else "công ty đối tác"
    job_name_val = job_name if job_name else "vị trí tuyển dụng"
    job_url_val = job_url if job_url else "hệ thống JobHub"

    prompt = _PROMPT_TEMPLATE.format(
        job_description=job_description,
        cv_text=cv_text,
        chat_history_str=chat_history_str,
        meta_info_str=meta_info_str,
        recruiter_name_val=recruiter_name_val,
        company_name_val=company_name_val,
        job_name_val=job_name_val,
        job_url_val=job_url_val
    )

    models_to_try = GEMINI_MODELS
    num_keys = len(keys)
    num_models = len(models_to_try)
    total_attempts = num_keys * num_models

    attempt = 0
    curr_key_idx = 0
    curr_model_idx = 0

    while attempt < total_attempts:
        key = keys[curr_key_idx]
        target_model = models_to_try[curr_model_idx]

        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel(target_model)
            response = await model.generate_content_async(
                contents=prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.4,
                    response_mime_type="application/json",
                ),
            )
            text_content = response.text
            result = json.loads(text_content)
            return result
        except Exception as e:
            logger.warning(f"[HireAgent] Thất bại với Key Index {curr_key_idx}, Model {target_model}: {e}")
            curr_model_idx = (curr_model_idx + 1) % num_models
            if curr_model_idx == 0:
                curr_key_idx = (curr_key_idx + 1) % num_keys
            attempt += 1

    return default_empty
