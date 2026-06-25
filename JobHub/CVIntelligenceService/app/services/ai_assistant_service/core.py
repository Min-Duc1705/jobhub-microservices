# app/services/ai_assistant_service/core.py
"""
Orchestrator chính của AI Assistant.
Điều phối session, tool-calling loop với Gemini và sinh kết quả phản hồi.
"""
import json
import logging
import base64
import time

import google.generativeai as genai
from app.config import settings
from app.ml.llm_generator import _load_api_keys
from app.schemas.assistant import (
    AssistantChatRequest, AssistantChatResponse, ActionItem
)

from .prompts import _SYSTEM_PROMPT_TEMPLATE
from .tools import _filter_tools_by_permission, _build_gemini_tools
from .executor import _execute_tool, _generate_suggestions
from .session_manager import (
    clean_expired_sessions, get_or_create_session, save_to_session, clear_session
)
from .fallback_builder import build_fallback_message

logger = logging.getLogger(__name__)

# Rotating Gemini API key index (global per process)
_current_key_idx = 0

# Human-readable capability descriptions per tool
_CAPABILITY_MAP = {
    "preview_create_job": "- Đăng tin tuyển dụng mới (tạo bản xem trước từ mô tả hoặc ảnh JD)",
    "delete_job": "- Xóa tin tuyển dụng đã đăng",
    "search_jobs": "- Tìm kiếm tin tuyển dụng trên toàn hệ thống",
    "get_my_jobs": "- Xem danh sách tin tuyển dụng do bạn quản lý",
    "get_job_detail": "- Xem chi tiết thông tin tin tuyển dụng theo ID",
    "search_candidates": "- Tìm kiếm ứng viên phù hợp với tiêu chí",
    "get_applications_for_job": "- Xem danh sách hồ sơ ứng tuyển của tin tuyển dụng",
    "predict_salary": "- Dự đoán mức lương thị trường để tham khảo",
    "get_my_company_info": "- Xem thông tin chi tiết về công ty của bạn",
    "navigate_to_page": "- Chuyển hướng người dùng nhanh đến các trang chức năng trên hệ thống",
    "search_companies": "- Tìm kiếm thông tin và xem danh sách các công ty trên hệ thống",
    "update_my_profile": "- Cập nhật thông tin hồ sơ cá nhân (tên, điện thoại, địa chỉ, giới thiệu...)",
    "get_my_saved_jobs": "- Xem danh sách các tin tuyển dụng đã lưu của bạn",
    "save_job": "- Lưu tin tuyển dụng vào danh sách việc làm đã lưu",
    "unsave_job": "- Bỏ lưu tin tuyển dụng khỏi danh sách việc làm đã lưu",
    "get_my_resumes": "- Xem danh sách các CV (Resumes) của bạn",
    "set_default_resume": "- Đặt một CV làm mặc định để nộp tuyển",
    "delete_resume": "- Xóa một CV trong danh sách của bạn",
    "get_my_applications": "- Xem danh sách các đơn đã ứng tuyển (Applications) của bạn",
    "apply_job": "- Nộp đơn ứng tuyển vào một tin tuyển dụng",
    "cancel_application": "- Hủy đơn ứng tuyển vào một tin tuyển dụng",
    "review_application": "- Phê duyệt/từ chối/cập nhật trạng thái đơn ứng tuyển của ứng viên (HR)",
    "update_company_info": "- Cập nhật thông tin chi tiết của công ty đang quản lý (HR)",
    "get_my_hire_agent_campaigns": "- Xem danh sách các chiến dịch tuyển dụng bằng AI (Hire Agent Campaigns)",
    "create_hire_agent_campaign": "- Tạo một chiến dịch tuyển dụng bằng AI mới (HR)",
    "schedule_campaign_interview": "- Đặt lịch hẹn phỏng vấn cho ứng viên trong chiến dịch tuyển dụng AI",
    "broadcast_notification": "- Gửi thông báo hệ thống (broadcast) tới người dùng hoặc nhóm đối tượng",
    "import_skills_to_my_profile": "- Thêm/import hàng loạt kỹ năng từ danh sách tên kỹ năng vào hồ sơ cá nhân của bạn",
    "get_my_conversations": "- Xem danh sách các cuộc trò chuyện (chat) của bạn",
    "get_chat_history": "- Xem chi tiết tin nhắn trong một cuộc hội thoại cụ thể",
    "get_my_notifications": "- Xem các thông báo chưa đọc của bạn",
    "telegram_subscribe": "- Đặt lịch tự động nhận thông báo gửi qua Telegram",
    "telegram_list_subscriptions": "- Xem danh sách lịch nhận thông báo Telegram của bạn",
    "telegram_delete_subscription": "- Xóa lịch nhận thông báo Telegram",
    "telegram_pause_subscription": "- Tạm dừng lịch nhận thông báo Telegram",
    "telegram_resume_subscription": "- Tiếp tục lịch nhận thông báo Telegram"
}


async def process_assistant_message(
    request: AssistantChatRequest,
    user_token: str,
    user_permissions: list[dict],
    user_role: str,
    username: str,
    session_id: str,
    company_name: str = "",
) -> AssistantChatResponse:
    """Main entry: xử lý tin nhắn từ user, gọi tools nếu cần, trả về response."""

    # Dọn session hết hạn
    clean_expired_sessions()

    # Lấy / khởi tạo session
    session_history = get_or_create_session(session_id, request.conversation_history)

    # Lọc tools theo quyền user
    available_tool_defs = _filter_tools_by_permission(user_permissions, user_role)
    tool_names = [td["name"] for td in available_tool_defs]
    gemini_tools = _build_gemini_tools(available_tool_defs)

    # Build capabilities string
    capabilities_list = []
    seen_caps = set()
    for name in tool_names:
        cap = _CAPABILITY_MAP.get(name)
        if cap and cap not in seen_caps:
            capabilities_list.append(cap)
            seen_caps.add(cap)

    capabilities_str = (
        "\n".join(capabilities_list)
        if capabilities_list
        else "- Giải đáp thắc mắc và hỗ trợ thông tin chung"
    )

    # Build system prompt
    company_info_str = (
        f"Công ty của người dùng (nhà tuyển dụng): **{company_name}**"
        if company_name else ""
    )
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
        role=user_role,
        username=username,
        company_info=company_info_str,
        available_tools=", ".join(tool_names) if tool_names else "Không có công cụ nào",
        capabilities=capabilities_str
    )

    from datetime import datetime, timezone, timedelta
    ict_tz = timezone(timedelta(hours=7))
    now_ict = datetime.now(ict_tz)
    now_str = now_ict.strftime("%Y-%m-%dT%H:%M:%S%z")
    days = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
    day_of_week = days[now_ict.weekday()]
    time_instruction = f"\n\n## 🕐 Thời gian hiện tại\nThời gian hiện tại của hệ thống: **{now_str}** ({day_of_week}, ngày {now_ict.strftime('%d/%m/%Y %H:%M:%S')}). Hãy sử dụng mốc thời gian này để tính toán target_time chính xác cho nhắc nhở/báo thức một lần."
    system_prompt += time_instruction

    # --- VERTEX AI PAID BRANCH ---
    if settings.USE_VERTEX_AI:
        from app.services.ai_assistant_service.vertex_initializer import _init_vertex_ai
        from app.services.ai_assistant_service.tools.vertex_builder import _build_vertex_tools
        from vertexai.generative_models import GenerativeModel, Tool, FunctionDeclaration, Content, Part, GenerationConfig
        
        try:
            # Initialize Vertex AI
            _init_vertex_ai()
            
            # Map tools
            vertex_tools = _build_vertex_tools(available_tool_defs)
            
            # Use default settings model (e.g. gemini-2.5-flash-lite)
            target_model = settings.GEMINI_MODEL.replace("models/", "")
            
            # Initialize model
            model = GenerativeModel(
                model_name=target_model,
                tools=vertex_tools if vertex_tools else None,
                system_instruction=system_prompt,
            )
            
            # Map chat history
            history_for_vertex = [
                Content(role="user" if msg["role"] == "user" else "model", parts=[Part.from_text(msg["content"])])
                for msg in session_history[-8:]
            ]
            
            chat = model.start_chat(history=history_for_vertex)
            
            # Map user parts
            vertex_user_parts = []
            if request.image_base64:
                image_data = base64.b64decode(request.image_base64)
                vertex_user_parts.append(
                    Part.from_bytes(data=image_data, mime_type="image/jpeg")
                )
            if request.file_content:
                vertex_user_parts.append(
                    Part.from_text(
                        f"[Nội dung file đính kèm]:\n{request.file_content[:3000]}\n\n"
                        f"[Yêu cầu của người dùng]: {request.message}"
                    )
                )
            else:
                vertex_user_parts.append(request.message)
                
            response = await chat.send_message_async(
                vertex_user_parts,
                generation_config=GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=2048,
                )
            )
            
            # Loop for tool calling (max 5 iterations)
            max_iterations = 5
            iteration = 0
            actions_taken = []
            pending_action = None
            
            while iteration < max_iterations:
                iteration += 1
                
                # Collect function calls
                fn_calls = []
                if response.candidates and response.candidates[0].function_calls:
                    for fc in response.candidates[0].function_calls:
                        if fc.name:
                            fn_calls.append(fc)
                            
                if not fn_calls:
                    break
                    
                # Helper to run tool
                async def run_single_tool(fc):
                    t_name = fc.name
                    r_args = dict(fc.args) if fc.args else {}
                    # Normalize list types
                    norm_args = {}
                    for k, v in r_args.items():
                        if hasattr(v, '__iter__') and not isinstance(v, (str, dict)):
                            norm_args[k] = list(v)
                        else:
                            norm_args[k] = v
                    logger.info(f"[VertexAI] Calling tool in parallel: {t_name}({norm_args})")
                    res = await _execute_tool(t_name, norm_args, user_token)
                    return t_name, norm_args, res
                    
                import asyncio
                tasks = [run_single_tool(fc) for fc in fn_calls]
                tool_results = await asyncio.gather(*tasks)
                
                fn_responses = []
                for tool_name, args, result in tool_results:
                    tool_def = next((t for t in available_tool_defs if t["name"] == tool_name), None)
                    if tool_def and tool_def.get("action_type") == "preview":
                        action_type = "create_job" if tool_name == "preview_create_job" else "delete_job"
                        description = (
                            f"Tạo tin tuyển dụng: {args.get('name', 'N/A')}"
                            if tool_name == "preview_create_job"
                            else f"Xóa tin tuyển dụng: {args.get('job_name', 'Không rõ tên')}"
                        )
                        pending_action = ActionItem(
                            action_type=action_type,
                            description=description,
                            data=result.get("job_data"),
                            requires_confirmation=True,
                            tool_name=tool_name
                        )
                    else:
                        actions_taken.append(ActionItem(
                            action_type=f"tool_{tool_name}",
                            description=f"Đã truy vấn: {tool_name}",
                            data=result,
                            requires_confirmation=False,
                            tool_name=tool_name
                        ))
                        
                    serialized_res = json.dumps(result, ensure_ascii=False)
                    if len(serialized_res) > 15000:
                        serialized_res = serialized_res[:15000] + "... [TRUNCATED]"
                        
                    fn_responses.append(
                        Part.from_function_response(
                            name=tool_name,
                            response={"result": serialized_res}
                        )
                    )
                    
                response = await chat.send_message_async(
                    fn_responses,
                    generation_config=GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=2048,
                    )
                )
                
            final_text = response.text
            
            # Fallback if no valid text
            if not final_text or final_text.strip() == "Tôi đã xử lý yêu cầu của bạn.":
                fallback_msg = build_fallback_message(actions_taken)
                if fallback_msg:
                    final_text = (
                        fallback_msg
                        + "\n\n*(Lưu ý: Phản hồi này được tự động tạo từ dữ liệu truy vấn "
                        "vì kết nối AI chính bị gián đoạn hoặc quá tải)*"
                    )
                else:
                    final_text = (
                        "Tôi đã xử lý yêu cầu của bạn nhưng không nhận được phản hồi từ AI. "
                        "Vui lòng thử lại sau ít phút hoặc dùng câu hỏi khác."
                    )
                    
            save_to_session(session_id, request.message, final_text)
            suggestions = _generate_suggestions(user_role, actions_taken)
            
            return AssistantChatResponse(
                reply=final_text,
                actions_taken=actions_taken,
                pending_action=pending_action,
                suggestions=suggestions
            )
            
        except Exception as e:
            logger.error(f"[VertexAI] Thất bại khi xử lý tin nhắn Vertex AI: {e}")
            return AssistantChatResponse(
                reply="Xin lỗi, AI Assistant (Vertex AI) đang gặp sự cố kỹ thuật. Vui lòng thử lại sau ít phút.",
                error=f"Vertex AI failed: {str(e)}"
            )

    # Load Gemini API keys
    keys = _load_api_keys()
    if not keys:
        return AssistantChatResponse(
            reply="Xin lỗi, AI Assistant chưa được cấu hình API key. Vui lòng liên hệ Admin.",
            error="No API keys configured"
        )

    models_to_try = [
        "gemini-3.5-flash",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash-latest",
    ]


    actions_taken = []
    pending_action = None

    global _current_key_idx
    num_keys = len(keys)
    num_models = len(models_to_try)
    max_attempts = num_keys * num_models

    attempt = 0
    curr_key_idx = _current_key_idx % num_keys if num_keys > 0 else 0
    curr_model_idx = 0
    last_error = ""

    while attempt < max_attempts and num_keys > 0:
        api_key = keys[curr_key_idx]
        model_name = models_to_try[curr_model_idx]
        attempt += 1

        try:
            genai.configure(api_key=api_key)

            # Build conversation history (last 8 messages)
            history_for_gemini = [
                {"role": msg["role"], "parts": [msg["content"]]}
                for msg in session_history[-8:]
            ]

            # Build user message parts
            user_parts = []
            if request.image_base64:
                image_data = base64.b64decode(request.image_base64)
                user_parts.append(
                    genai.protos.Part(
                        inline_data=genai.protos.Blob(mime_type="image/jpeg", data=image_data)
                    )
                )

            if request.file_content:
                user_parts.append(
                    genai.protos.Part(
                        text=f"[Nội dung file đính kèm]:\n{request.file_content[:3000]}\n\n"
                             f"[Yêu cầu của người dùng]: {request.message}"
                    )
                )
            else:
                user_parts.append(genai.protos.Part(text=request.message))

            # Initialize Gemini model
            model = genai.GenerativeModel(
                model_name=model_name,
                tools=gemini_tools if gemini_tools else None,
                system_instruction=system_prompt,
            )

            chat = model.start_chat(history=history_for_gemini)

            response = await chat.send_message_async(
                genai.protos.Content(parts=user_parts, role="user"),
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=2048,
                )
            )

            # ── Tool-calling loop (max 5 iterations) ──
            max_iterations = 5
            iteration = 0

            while iteration < max_iterations:
                iteration += 1

                # Collect function calls from response
                fn_calls = []
                for part in response.parts:
                    if hasattr(part, 'function_call') and part.function_call and part.function_call.name:
                        fn_calls.append(part.function_call)
                    elif hasattr(part, 'function_calls') and part.function_calls:
                        for fc in part.function_calls:
                            if fc.name:
                                fn_calls.append(fc)

                if not fn_calls:
                    break  # No more tool calls

                # Định nghĩa helper chạy song song các tool calls
                async def run_single_tool(fc):
                    t_name = fc.name
                    r_args = dict(fc.args) if fc.args else {}
                    # Chuẩn hóa RepeatedComposite thành list
                    norm_args = {}
                    for k, v in r_args.items():
                        if hasattr(v, '__iter__') and not isinstance(v, (str, dict)):
                            norm_args[k] = list(v)
                        else:
                            norm_args[k] = v
                    logger.info(f"[AIAssistant] Calling tool in parallel: {t_name}({norm_args})")
                    res = await _execute_tool(t_name, norm_args, user_token)
                    return t_name, norm_args, res

                # Chạy song song tất cả các tool calls trong lượt này để tối ưu hiệu suất (Parallel Tool Calling)
                import asyncio
                tasks = [run_single_tool(fc) for fc in fn_calls]
                tool_results = await asyncio.gather(*tasks)

                # Execute each function call
                fn_responses = []
                for tool_name, args, result in tool_results:
                    tool_def = next((t for t in available_tool_defs if t["name"] == tool_name), None)

                    if tool_def and tool_def.get("action_type") == "preview":
                        action_type = "create_job" if tool_name == "preview_create_job" else "delete_job"
                        description = (
                            f"Tạo tin tuyển dụng: {args.get('name', 'N/A')}"
                            if tool_name == "preview_create_job"
                            else f"Xóa tin tuyển dụng: {args.get('job_name', 'Không rõ tên')}"
                        )
                        pending_action = ActionItem(
                            action_type=action_type,
                            description=description,
                            data=result.get("job_data"),
                            requires_confirmation=True,
                            tool_name=tool_name
                        )
                    else:
                        actions_taken.append(ActionItem(
                            action_type=f"tool_{tool_name}",
                            description=f"Đã truy vấn: {tool_name}",
                            data=result,
                            requires_confirmation=False,
                            tool_name=tool_name
                        ))

                    serialized_res = json.dumps(result, ensure_ascii=False)
                    if len(serialized_res) > 15000:
                        serialized_res = serialized_res[:15000] + "... [TRUNCATED]"

                    fn_responses.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=tool_name,
                                response={"result": serialized_res}
                            )
                        )
                    )

                # Gửi kết quả tool về cho Gemini.
                # Nếu gặp lỗi (như Rate Limit 429), exception sẽ được ném ra ngoài để vòng lặp lớn bắt lấy.
                # Vòng lặp lớn sẽ tự động đổi sang API Key/Model mới và chạy lại toàn bộ lượt chat từ đầu,
                # đảm bảo giữ nguyên ngữ cảnh hội thoại nhất quán 100%.
                response = await chat.send_message_async(
                    genai.protos.Content(parts=fn_responses, role="tool"),
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=2048,
                    )
                )

            # ── Extract final text response ──
            final_text = "".join(
                part.text
                for part in response.parts
                if hasattr(part, 'text') and part.text
            )

            # Fallback nếu không có text hợp lệ
            if not final_text or final_text.strip() == "Tôi đã xử lý yêu cầu của bạn.":
                fallback_msg = build_fallback_message(actions_taken)
                if fallback_msg:
                    final_text = (
                        fallback_msg
                        + "\n\n*(Lưu ý: Phản hồi này được tự động tạo từ dữ liệu truy vấn "
                        "vì kết nối AI chính bị gián đoạn hoặc quá tải)*"
                    )
                else:
                    final_text = (
                        "Tôi đã xử lý yêu cầu của bạn nhưng không nhận được phản hồi từ AI. "
                        "Vui lòng thử lại sau ít phút hoặc dùng câu hỏi khác."
                    )

            # Lưu vào session
            save_to_session(session_id, request.message, final_text)

            suggestions = _generate_suggestions(user_role, actions_taken)

            # Cập nhật key thành công để xoay vòng lần sau
            _current_key_idx = curr_key_idx

            return AssistantChatResponse(
                reply=final_text,
                actions_taken=actions_taken,
                pending_action=pending_action,
                suggestions=suggestions
            )

        except Exception as e:
            err_str = str(e)
            last_error = err_str
            logger.warning(f"[AIAssistant] Model {model_name} key[{curr_key_idx}] failed: {err_str}")

            # Thử model tiếp theo trên cùng 1 key; nếu đã thử hết tất cả model thì mới chuyển sang key tiếp theo
            curr_model_idx = (curr_model_idx + 1) % num_models
            if curr_model_idx == 0:
                curr_key_idx = (curr_key_idx + 1) % num_keys

    return AssistantChatResponse(
        reply="Xin lỗi, AI Assistant đang gặp sự cố kỹ thuật. Vui lòng thử lại sau ít phút.",
        error=f"All models/keys exhausted. Last error: {last_error}"
    )
