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
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite-preview",
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
    Sinh nhận xét chuyên sâu bằng Google Gemini LLM hoặc Local AI (Ollama).
    """
    default_empty = {
        "extracted_skills": [],
        "strengths": [],
        "weaknesses": [],
        "ai_feedback": None,
    }

    prompt = _PROMPT_TEMPLATE.format(
        job_description=job_description,
        cv_text=cv_text,
    )

    if settings.USE_LOCAL_AI:
        import httpx
        try:
            logger.info(f"[LLM-Local] Đang gọi local Ollama model {settings.LOCAL_AI_MODEL}...")
            async with httpx.AsyncClient(timeout=120.0) as client:
                res = await client.post(
                    f"{settings.LOCAL_AI_URL.rstrip('/')}/api/chat",
                    json={
                        "model": settings.LOCAL_AI_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                        "options": {"temperature": 0.3}
                    }
                )
                if res.status_code == 200:
                    reply_text = res.json()["message"]["content"]
                    import re
                    clean_match = re.search(r"\{.*\}", reply_text, re.DOTALL)
                    if clean_match:
                        reply_text = clean_match.group(0)
                    result = json.loads(reply_text)
                    return result
                else:
                    logger.warning(f"[LLM-Local] Gọi Ollama thất bại: HTTP {res.status_code}")
        except Exception as local_ex:
            logger.error(f"[LLM-Local] Lỗi gọi Ollama: {local_ex}")
        return default_empty

    if settings.USE_VERTEX_AI:
        try:
            from app.services.ai_assistant_service.vertex_initializer import _init_vertex_ai
            from vertexai.generative_models import GenerativeModel, GenerationConfig
            _init_vertex_ai()
            target_model = model_name if model_name else settings.GEMINI_MODEL
            logger.info(f"[LLM] Đang gọi Vertex AI (Model: {target_model})...")
            clean_model = target_model.replace("models/", "")
            model = GenerativeModel(clean_model)
            response = await model.generate_content_async(
                contents=prompt,
                generation_config=GenerationConfig(
                    temperature=0.3,
                    response_mime_type="application/json",
                ),
            )
            result = json.loads(response.text)
            return result
        except Exception as vertex_ex:
            logger.error(f"[LLM] Lỗi gọi Vertex AI: {vertex_ex}")
            return default_empty

    keys = _load_api_keys()

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
                request_options={"timeout": 30.0}
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


_PARSE_EXP_PROMPT = """
You are an expert HR assistant. Given the job experience requirement text below, extract the minimum years of experience required as a single integer.
Follow these rules:
1. If no experience is required, or it says "dưới 1 năm" (under 1 year), "fresher", "intern", "không yêu cầu", return 0.
2. If it specifies a range like "1-3 năm" or "1 to 3 years", return the lower bound (e.g., 1).
3. If it specifies "Trên 5 năm" (over 5 years) or "5+ years", return 5.
4. If it's a student (e.g. "sinh viên năm 4") but says "dưới 1 năm kinh nghiệm" or "không yêu cầu kinh nghiệm", return 0.
5. Return ONLY a JSON object containing the field "years".

=== EXPERIENCE TEXT ===
{experience_text}

=== OUTPUT FORMAT ===
{{
  "years": 0
}}
"""

async def parse_experience_with_llm(experience_text: str) -> int:
    """
    Sử dụng Gemini LLM hoặc Local AI để bóc tách số năm kinh nghiệm từ chuỗi văn bản.
    """
    prompt = _PARSE_EXP_PROMPT.format(experience_text=experience_text)
    
    # Try Local AI if configured
    if settings.USE_LOCAL_AI:
        import httpx
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    f"{settings.LOCAL_AI_URL.rstrip('/')}/api/chat",
                    json={
                        "model": settings.LOCAL_AI_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                        "options": {"temperature": 0.1}
                    }
                )
                if res.status_code == 200:
                    reply_text = res.json()["message"]["content"]
                    import re
                    clean_match = re.search(r"\{.*\}", reply_text, re.DOTALL)
                    if clean_match:
                        reply_text = clean_match.group(0)
                    result = json.loads(reply_text)
                    return int(result.get("years", 0))
        except Exception as e:
            logger.warning(f"[LLM-Local] Lỗi bóc tách kinh nghiệm: {e}")
            
    # Try Vertex AI if configured
    if settings.USE_VERTEX_AI:
        try:
            from app.services.ai_assistant_service.vertex_initializer import _init_vertex_ai
            from vertexai.generative_models import GenerativeModel, GenerationConfig
            _init_vertex_ai()
            model = GenerativeModel(settings.GEMINI_MODEL.replace("models/", ""))
            response = await model.generate_content_async(
                contents=prompt,
                generation_config=GenerationConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
            result = json.loads(response.text)
            return int(result.get("years", 0))
        except Exception as e:
            logger.warning(f"[LLM-Vertex] Lỗi bóc tách kinh nghiệm: {e}")

    # Gemini API with key rotation
    keys = _load_api_keys()
    if not keys:
        return 0
        
    models_to_try = GEMINI_MODELS
    num_keys = len(keys)
    num_models = len(models_to_try)
    total_attempts = num_keys * num_models

    global _current_key_idx, _current_model_idx
    curr_key_idx = _current_key_idx % num_keys
    curr_model_idx = _current_model_idx % num_models
    attempt = 0

    while attempt < total_attempts:
        key = keys[curr_key_idx]
        target_model = models_to_try[curr_model_idx]
        
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel(target_model)
            response = await model.generate_content_async(
                contents=prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
                request_options={"timeout": 15.0}
            )
            result = json.loads(response.text)
            _current_key_idx = curr_key_idx
            _current_model_idx = curr_model_idx
            return int(result.get("years", 0))
        except Exception as e:
            logger.warning(f"[LLM] Bóc tách exp thất bại với Key {curr_key_idx}, Model {target_model}: {e}")
            curr_model_idx = (curr_model_idx + 1) % num_models
            if curr_model_idx == 0:
                curr_key_idx = (curr_key_idx + 1) % num_keys
            attempt += 1

    return 0
