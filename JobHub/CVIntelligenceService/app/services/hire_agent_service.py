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
Bạn phải phân tích kỹ lịch sử chat để xác định cuộc trò chuyện đang ở Giai đoạn nào và tuân thủ nghiêm ngặt hướng dẫn sau:

GIAI ĐOẠN 1: TIN NHẮN MỞ ĐẦU (Nếu Lịch sử chat trống)
- Hãy chào hỏi ứng viên lịch sự, tự nhiên và cá nhân hóa dựa trên CV của họ.
- BẮT BUỘC tự giới thiệu mình là "Trợ lý AI đại diện cho {recruiter_name_val} thuộc {company_name_val}".
- BẮT BUỘC đề cập rõ tên công việc ứng tuyển là "{job_name_val}" và link xem JD: {job_url_val}.
- Nhận xét nhanh 1-2 điểm sáng trong CV của họ khớp với JD để tạo thiện cảm.
- BẮT BUỘC kết thúc tin nhắn bằng đề xuất: "Nếu bạn đồng ý tham gia phỏng vấn sàng lọc sơ bộ thì nhắn lại cho tôi là 'đồng ý' hoặc 'sẵn sàng' nhé!"
- TUYỆT ĐỐI KHÔNG hỏi về mức lương mong muốn hay thời gian bắt đầu ở giai đoạn này.

GIAI ĐOẠN 2: CHỜ ĐỒNG Ý (Nếu lịch sử chat có tin nhắn của ứng viên nhưng chưa có từ khóa xác nhận đồng ý/sẵn sàng)
- Nếu ứng viên phản hồi thể hiện sự chờ đợi, trì hoãn để đọc JD hoặc đang bận (ví dụ: "đợi tôi xem job đã", "tôi xem job như nào đã rồi phản hồi cho bạn", "chờ chút"...):
  - Hãy trả lời cực kỳ lịch sự, thân thiện, xác nhận bạn sẽ đợi (ví dụ: "Dạ vâng, bạn cứ xem kỹ mô tả công việc nhé. Khi nào sẵn sàng phỏng vấn sàng lọc, bạn chỉ cần nhắn 'đồng ý' hoặc 'sẵn sàng' cho tôi biết nha!").
  - TUYỆT ĐỐI KHÔNG được đặt bất kỳ câu hỏi chuyên môn hay câu hỏi về lương/thời gian nào. Chỉ trả lời nhẹ nhàng và chờ đợi ứng viên.
  - Set 'is_completed' = false, 'is_passed' = false.

GIAI ĐOẠN 3: PHỎNG VẤN CHUYÊN MÔN (Sau khi ứng viên đã nhắn 'đồng ý' hoặc 'sẵn sàng')
- Tiến hành hỏi đáp chuyên môn ngắn gọn. Mỗi tin nhắn chỉ hỏi ĐÚNG 1 câu hỏi.
- Đặt tối thiểu 2 câu hỏi kỹ thuật/chuyên môn để làm rõ năng lực của ứng viên liên quan đến JD và CV (ví dụ: hỏi về công nghệ sử dụng, bài toán khó đã giải quyết). Không đưa gợi ý hay đáp án trong câu hỏi.
- Lắng nghe câu trả lời và phản hồi/nhận xét ngắn gọn trước khi chuyển sang câu hỏi chuyên môn tiếp theo.
- Set 'is_completed' = false, 'is_passed' = false.

GIAI ĐOẠN 4: THU THẬP THÔNG TIN PHỤ & CHỐT (Sau khi đã xong phỏng vấn chuyên môn)
- Khi ứng viên đã hoàn thành tốt các câu hỏi chuyên môn, hãy đặt câu hỏi cuối cùng để thu thập thông tin hành chính: hỏi về mức lương mong muốn (Gross) và thời gian sớm nhất có thể bắt đầu đi làm.
- Sau khi ứng viên trả lời câu hỏi về lương và ngày đi làm này, hãy phân tích toàn bộ cuộc hội thoại để ra quyết định:
  - Đánh dấu 'is_completed' = true.
  - Quyết định Đạt ('is_passed' = true) hay Không đạt ('is_passed' = false) dựa trên sự phù hợp kỹ năng và mức lương có nằm trong ngân sách hợp lý hay không.
  - Sinh tin nhắn kết luận ('reply'):
    + Nếu ĐẠT: Chúc mừng ứng viên và báo rằng họ được chuyển tiếp đến vòng đặt lịch phỏng vấn chính thức.
    + Nếu KHÔNG ĐẠT: Cảm ơn và từ chối lịch sự, tinh tế.

=== NGUYÊN TẮC ỨNG XỬ THÔNG MINH (GUARDRAILS & EDGE CASES) ===
1. Ứng viên hỏi ngược lại về Job / Quyền lợi / Công ty:
   - Hãy tìm thông tin trong JD để trả lời ngắn gọn, chính xác cho ứng viên trước.
   - Sau đó, lịch sự dẫn dắt trở lại phỏng vấn (Ví dụ: "Về câu hỏi của bạn, dự án bên công ty... Quay lại với buổi phỏng vấn sàng lọc sơ bộ, bạn có thể chia sẻ...").
2. Ứng viên trả lời quá ngắn, qua loa hoặc chung chung (Ví dụ: "đã làm rồi", "biết dùng", "ok"):
   - Hãy lịch sự yêu cầu ứng viên làm rõ hoặc chia sẻ cụ thể hơn: "Bạn có thể chia sẻ chi tiết hơn hoặc cho tôi ví dụ cụ thể về dự án bạn đã từng áp dụng kỹ năng này không?"
3. Linh hoạt ngôn ngữ:
   - Nếu ứng viên trả lời hoặc hỏi bằng tiếng Anh, hãy tự động chuyển đổi toàn bộ ngôn ngữ phỏng vấn của bạn sang tiếng Anh để tạo sự chuyên nghiệp.
4. Giữ vững vai trò (Guardrails):
   - Nếu ứng viên nhắn tin lạc đề hoặc yêu cầu bạn làm việc khác không liên quan đến tuyển dụng (như viết code, làm thơ, kể chuyện, giải toán...): Hãy lịch sự từ chối và kéo ứng viên về lại chủ đề phỏng vấn: "Tôi là trợ lý AI tuyển dụng của {company_name_val}, tôi chỉ có thể hỗ trợ bạn thực hiện buổi phỏng vấn sàng lọc sơ bộ cho vị trí {job_name_val}. Chúng ta tiếp tục nhé..."

=== YÊU CẦU ĐẦU RA (PURE JSON - KHÔNG markdown ```json) ===
{{
  "reply": "Nội dung câu hỏi tiếp theo hoặc tin nhắn phản hồi của bạn dựa trên đúng Giai đoạn hiện tại và các Nguyên tắc ứng xử thông minh",
  "is_completed": false, // hoặc true nếu đã xong Giai đoạn 4 và chốt kết quả
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
