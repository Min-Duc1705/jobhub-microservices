import json
import logging
import os
import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)

# Khởi tạo chỉ số xoay vòng key và model
_current_key_idx = 0
_current_model_idx = 0

GEMINI_MODELS = [
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash-latest",
]


def _load_api_keys() -> list:
    paths_to_try = [
        "gemini-keys.json",
        "/app/gemini-keys.json",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "gemini-keys.json")
    ]
    for p in paths_to_try:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    keys = []
                    if isinstance(data, list):
                        keys = data
                    elif isinstance(data, dict) and "geminiApiKeys" in data:
                        keys = data["geminiApiKeys"]
                    
                    if isinstance(keys, list):
                        keys = [k.strip() for k in keys if k and isinstance(k, str) and k.strip()]
                        if keys:
                            return keys
            except Exception as e:
                logger.warning(f"[LLM] Lỗi khi đọc file keys {p}: {e}")
    
    # Fallback về key từ config/env
    if settings.GEMINI_API_KEY:
        return [settings.GEMINI_API_KEY]
    return []

# Cấu hình ban đầu làm dự phòng
initial_keys = _load_api_keys()
if initial_keys:
    genai.configure(api_key=initial_keys[0])


_PROMPT_TEMPLATE = """
Bạn là chuyên gia tuyển dụng. Dưới đây là Mô tả công việc (JD) và thông tin CV của ứng viên.
Hãy đánh giá chi tiết mức độ phù hợp và trả về ĐÚNG ĐỊNH DẠNG JSON. Viết bằng tiếng Việt.
Tuyệt đối không sử dụng mardown bọc chuỗi (ví dụ ```json ... ```), chỉ trả về pure JSON object.

=== MÔ TẢ CÔNG VIỆC ===
{job_description}

=== THÔNG TIN CV ỨNG VIÊN ===
{cv_text}

=== YÊU CẦU ĐẦU RA (PURE JSON) ===
{{
  "extracted_skills": ["skill1", "skill2"],
  "strengths": ["điểm mạnh 1", "điểm mạnh 2"],
  "weaknesses": ["điểm yếu 1", "điểm yếu 2"],
  "ai_feedback": "Nhận xét tổng thể 2-3 câu về mức độ phù hợp của ứng viên"
}}
"""


async def generate_feedback(
    job_description: str,
    cv_text: str,
    model_name: str = None,
) -> dict:
    """
    Sinh nhận xét chuyên sâu bằng Google Gemini LLM.
    Tự động xoay vòng API key và thử các model khác nhau nếu gặp lỗi hết quota (429) hoặc model không khả dụng.
    """
    default_empty = {
        "extracted_skills": [],
        "strengths": [],
        "weaknesses": [],
        "ai_feedback": None,
    }

    keys = _load_api_keys()
    if not keys:
        logger.warning("[LLM] Không có API Key nào được cấu hình — bỏ qua bước sinh nhận xét.")
        return default_empty

    prompt = _PROMPT_TEMPLATE.format(
        job_description=job_description,
        cv_text=cv_text,
    )

    models_to_try = [model_name] if model_name else GEMINI_MODELS
    
    num_keys = len(keys)
    num_models = len(models_to_try)
    total_attempts = num_keys * num_models

    global _current_key_idx, _current_model_idx
    # Lấy vị trí bắt đầu
    start_key_idx = _current_key_idx % num_keys
    # Nếu chỉ chạy duy nhất 1 model truyền vào, model index bắt đầu luôn là 0
    start_model_idx = 0 if model_name else (_current_model_idx % num_models)

    attempt = 0
    curr_key_idx = start_key_idx
    curr_model_idx = start_model_idx

    while attempt < total_attempts:
        key = keys[curr_key_idx]
        target_model = models_to_try[curr_model_idx]
        
        try:
            logger.info(f"[LLM] Đang gọi Gemini API (Key Index: {curr_key_idx}/{num_keys-1}, Model: {target_model})...")
            genai.configure(api_key=key)
            model = genai.GenerativeModel(target_model)
            response = await model.generate_content_async(
                contents=prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    response_mime_type="application/json",
                ),
            )
            # Parse JSON an toàn
            text_content = response.text
            result = json.loads(text_content)
            
            # Lưu lại vị trí thành công gần nhất
            _current_key_idx = curr_key_idx
            if not model_name:
                _current_model_idx = curr_model_idx
                
            return result
        except Exception as e:
            err_str = str(e)
            logger.warning(
                f"[LLM] Thất bại với Key Index {curr_key_idx}, Model {target_model}: {err_str}"
            )
            
            # Chuyển sang model tiếp theo; nếu hết model của key này thì chuyển sang key tiếp theo
            curr_model_idx = (curr_model_idx + 1) % num_models
            if curr_model_idx == 0:
                curr_key_idx = (curr_key_idx + 1) % num_keys
            attempt += 1

    logger.error("[LLM] Đã thử tất cả API Key và Model nhưng đều thất bại.")
    return default_empty
