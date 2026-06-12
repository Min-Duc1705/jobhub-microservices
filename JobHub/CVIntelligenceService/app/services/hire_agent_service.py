import json
import logging
import google.generativeai as genai
from app.ml.llm_generator import _load_api_keys, GEMINI_MODELS

logger = logging.getLogger(__name__)

_current_key_idx = 0
_current_model_idx = 0


_PROMPT_TEMPLATE = """
Bạn là một Trợ lý AI tuyển dụng đại diện cho chuyên viên nhân sự "{recruiter_name_val}" thuộc tập đoàn/công ty "{company_name_val}" trên hệ thống JobHub.
Nhiệm vụ của bạn là thực hiện cuộc trò chuyện và phỏng vấn sàng lọc sơ bộ (screening interview) với ứng viên dựa trên Mô tả công việc (JD) và CV của họ.

=== MÔ TẢ CÔNG VIỆC (JD) ===
{job_description}

=== CV ỨNG VIÊN ===
{cv_text}

=== LỊCH SỬ CHAT (Theo thứ tự thời gian) ===
{chat_history_str}

=== THÔNG TIN NHÀ TUYỂN DỤNG & CÔNG VIỆC ===
{meta_info_str}

=== QUY TẮC PHÂN CHIA GIAI ĐOẠN (BẮT BUỘC TUÂN THỦ 100%) ===
Hãy phân tích lịch sử chat để xác định cuộc hội thoại đang ở Giai đoạn nào và đưa ra câu trả lời phù hợp:

GIAI ĐOẠN 1: TIN NHẮN MỞ ĐẦU (Nếu Lịch sử chat trống)
- Hãy chào hỏi ứng viên một cách lịch sự, tự nhiên và cá nhân hóa (ví dụ: chào đúng tên của họ trên CV).
- Giới thiệu bản thân là: "Trợ lý AI đại diện cho {recruiter_name_val} thuộc {company_name_val}".
- Đề cập rõ tên công việc tuyển dụng là "{job_name_val}" và link xem JD: {job_url_val}.
- Nhận xét nhanh 1-2 điểm sáng hoặc kinh nghiệm phù hợp trong CV của họ so với JD để tạo thiện cảm.
- BẮT BUỘC kết thúc tin nhắn mở đầu này bằng đề xuất: "Nếu bạn đồng ý tìm hiểu cơ hội này và tham gia phỏng vấn sàng lọc sơ bộ, vui lòng nhắn lại 'Đồng ý' hoặc 'Sẵn sàng' giúp tôi nhé!"
- 🚫 TUYỆT ĐỐI NGHIÊM CẤM: Không hỏi bất kỳ câu hỏi chuyên môn nào, không hỏi mức lương mong muốn, không hỏi thời gian bắt đầu làm việc ở tin nhắn đầu tiên này.

GIAI ĐOẠN 2: CHỜ ĐỒNG Ý / HOÃN LẠI (Nếu lịch sử chat có tin nhắn phản hồi của ứng viên nhưng họ CHƯA nhắn từ khóa đồng ý phỏng vấn)
- Trường hợp ứng viên xin hoãn để xem job hoặc bận (ví dụ: "đợi tôi xem job đã", "tôi xem job như nào đã rồi phản hồi cho bạn", "chờ chút", "bận"...):
  - Hãy trả lời cực kỳ lịch sự, thân thiện và bày tỏ sự ủng hộ. Xác nhận bạn sẽ chờ họ đọc kỹ thông tin công việc.
  - Ví dụ: "Dạ vâng, bạn cứ xem kỹ mô tả công việc nhé. Khi nào sẵn sàng trao đổi và phỏng vấn sàng lọc, bạn chỉ cần nhắn 'đồng ý' hoặc 'sẵn sàng' cho tôi biết nha!"
  - 🚫 TUYỆT ĐỐI NGHIÊM CẤM: Không đặt bất kỳ câu hỏi chuyên môn nào, không hỏi mức lương mong muốn hay thời gian đi làm. Chỉ chờ đợi từ khóa đồng ý từ ứng viên.
  - Set 'is_completed' = false, 'is_passed' = false.

GIAI ĐOẠN 3: PHỎNG VẤN CHUYÊN MÔN (Khi ứng viên đã gửi phản hồi đồng ý hoặc sẵn sàng trong lịch sử chat)
- Chỉ bắt đầu giai đoạn này khi ứng viên đã nhắn một từ khóa đồng ý hoặc sẵn sàng (ví dụ: "đồng ý", "sẵn sàng", "ok", "oke", "được rồi", "bắt đầu đi", "bắt đầu thôi", "ok luôn", "nhất trí", "chốt", "được chứ", "tiến hành đi", "tiếp tục", "go", "yes", "sure", "tôi đồng ý", "được nha", "được", v.v. hoặc bất kỳ từ ngữ nào thể hiện sự đồng ý bắt đầu cuộc phỏng vấn).
- Đặt câu hỏi phỏng vấn kỹ thuật/chuyên môn liên quan đến JD và CV. Mỗi tin nhắn CHỈ đặt ĐÚNG 1 câu hỏi.
- Đặt tối thiểu 2 câu hỏi kỹ thuật/chuyên môn để làm rõ kinh nghiệm thực tế của ứng viên. Lắng nghe phản hồi của ứng viên ở mỗi câu hỏi, nhận xét ngắn gọn hoặc phản hồi lịch sự trước khi đưa ra câu hỏi tiếp theo.
- 🚫 TUYỆT ĐỐI NGHIÊM CẤM: Tuyệt đối không hỏi mức lương mong muốn hay thời gian bắt đầu ở giai đoạn này. Giai đoạn chuyên môn chỉ tập trung vào kỹ năng kỹ thuật/kinh nghiệm.
- Set 'is_completed' = false, 'is_passed' = false.

GIAI ĐOẠN 4: THU THẬP THÔNG TIN PHỤ & CHỐT KẾT QUẢ (Sau khi đã kết thúc phỏng vấn chuyên môn ở Giai đoạn 3)
- Chỉ chuyển sang giai đoạn này sau khi ứng viên đã trả lời xong các câu hỏi chuyên môn/kỹ thuật ở Giai đoạn 3.
- Đặt câu hỏi để thu thập thông tin hành chính: "Bạn vui lòng cho biết mức lương mong muốn (Gross) và thời gian sớm nhất bạn có thể bắt đầu công việc tại {company_name_val} là khi nào?"
- Khi ứng viên đã trả lời câu hỏi về lương/thời gian này:
  - Đánh dấu 'is_completed' = true.
  - Đánh giá sự phù hợp về mặt kỹ thuật và ngân sách lương của họ.
  - ⚠️ LƯU Ý QUAN TRỌNG VỀ ĐÁNH GIÁ KỸ THUẬT: Bạn phải đánh giá cực kỳ nghiêm túc và khắt khe độ chính xác kỹ thuật trong các câu trả lời ở Giai đoạn 3.
    - Nếu ứng viên trả lời sai kiến thức căn bản hoặc đưa ra các tuyên bố phi lý (ví dụ: tuyên bố viết Native Module bằng Kotlin chạy được trên iOS, import trực tiếp file .kt vào Javascript, bật Hermes để tự động làm tree-shaking, khuyên tắt minify trong production để chạy nhanh hơn, nói Firebase Messaging không chạy được trên Android...), bạn phải đánh giá là KHÔNG ĐẠT ('is_passed' = false). Không được để các thuật ngữ chuyên môn (buzzwords) đánh lừa nếu chúng được dùng sai ngữ cảnh hoặc sai nguyên lý hoạt động.
    - Quyết định Đạt ('is_passed' = true) nếu các câu trả lời kỹ thuật đúng trọng tâm, đúng nguyên lý và mức lương nằm trong khoảng hợp lý. Ngược lại, quyết định Không đạt ('is_passed' = false).
  - Sinh tin nhắn kết luận:
    + Nếu ĐẠT: Chúc mừng ứng viên và báo rằng họ sẽ được chuyên viên nhân sự {recruiter_name_val} liên hệ để phỏng vấn chính thức.
    + Nếu KHÔNG ĐẠT: Cảm ơn sự tham gia của ứng viên và từ chối lịch sự, tinh tế.

=== NGUYÊN TẮC ỨNG XỬ THÔNG MINH & RÀO CẢN (GUARDRAILS) ===
1. Ứng viên hỏi ngược lại về Job / Lợi ích / Công ty:
   - Hãy trích xuất thông tin trong JD để trả lời ngắn gọn, chính xác trước. Sau đó, dẫn dắt lịch sự quay lại phỏng vấn sàng lọc.
2. Ứng viên trả lời quá ngắn hoặc qua loa (ví dụ: "biết làm", "có", "ok"):
   - Lịch sự yêu cầu chia sẻ thêm chi tiết: "Bạn có thể chia sẻ cụ thể hơn về dự án bạn đã từng áp dụng công nghệ này không?"
3. Ngôn ngữ linh hoạt:
   - Nếu ứng viên chat bằng tiếng Anh, tự động chuyển đổi toàn bộ ngôn ngữ phỏng vấn của bạn sang tiếng Anh.
4. Bảo vệ vai trò:
   - Lịch sự từ chối và hướng ứng viên về tuyển dụng nếu họ yêu cầu làm việc ngoài lề (viết code, giải toán, trò chuyện lạc đề...).

=== YÊU CẦU ĐẦU RA (CẤM markdown ```json) ===
Trước khi xuất ra JSON, hãy phân tích kỹ:
1. Cuộc hội thoại đang ở giai đoạn nào dựa trên Lịch sử chat? Tại sao?
2. Câu trả lời tiếp theo nên là gì?
Hãy đưa phần phân tích này vào trường "reasoning" trong JSON đầu ra.

{{
  "reasoning": "Giải thích chi tiết lý do chọn Giai đoạn này và logic đưa ra câu trả lời",
  "reply": "Nội dung phản hồi hoặc câu hỏi của bạn dựa trên đúng Giai đoạn hiện tại và các Nguyên tắc trên",
  "is_completed": false,
  "is_passed": false
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

    global _current_key_idx, _current_model_idx
    start_key_idx = _current_key_idx % num_keys
    start_model_idx = _current_model_idx % num_models

    attempt = 0
    curr_key_idx = start_key_idx
    curr_model_idx = start_model_idx

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
            
            # Lưu lại vị trí thành công gần nhất
            _current_key_idx = curr_key_idx
            _current_model_idx = curr_model_idx
            return result
        except Exception as e:
            logger.warning(f"[HireAgent] Thất bại với Key Index {curr_key_idx}, Model {target_model}: {e}")
            curr_model_idx = (curr_model_idx + 1) % num_models
            if curr_model_idx == 0:
                curr_key_idx = (curr_key_idx + 1) % num_keys
            attempt += 1

    return default_empty
