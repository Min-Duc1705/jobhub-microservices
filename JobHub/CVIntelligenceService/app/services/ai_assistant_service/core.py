# app/services/ai_assistant_service/core.py
import json
import logging
import base64
import time
from typing import Optional

import google.generativeai as genai
from app.ml.llm_generator import _load_api_keys
from app.schemas.assistant import (
    AssistantChatRequest, AssistantChatResponse,
    AssistantMessage, ActionItem
)

from .prompts import _SYSTEM_PROMPT_TEMPLATE
from .tools import _filter_tools_by_permission, _build_gemini_tools
from .executor import _execute_tool, normalize_category, _generate_suggestions
from .api_client import _call_api

logger = logging.getLogger(__name__)

# In-memory session store: session_id -> list of messages
_SESSIONS: dict[str, list] = {}
_SESSION_TTL = 3600  # 1 hour
_SESSION_TIMESTAMPS: dict[str, float] = {}

# Chỉ số xoay vòng key toàn cục cho Assistant
_current_key_idx = 0

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
    "navigate_to_page": "- Chuyển hướng người dùng nhanh đến các trang chức năng trên hệ thống (ví dụ: quản lý tuyển dụng, profile, dashboard...)",
    "search_companies": "- Tìm kiếm thông tin và xem danh sách các công ty trên hệ thống",
    "update_my_profile": "- Cập nhật thông tin hồ sơ cá nhân của bạn (như tên hiển thị username, họ tên fullName, điện thoại, địa chỉ, giới thiệu...)",
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
    "broadcast_notification": "- Gửi thông báo hệ thống (broadcast) tới người dùng hoặc nhóm đối tượng"
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

    # Clean expired sessions
    now = time.time()
    expired = [k for k, t in _SESSION_TIMESTAMPS.items() if now - t > _SESSION_TTL]
    for k in expired:
        _SESSIONS.pop(k, None)
        _SESSION_TIMESTAMPS.pop(k, None)

    # Get or create session
    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = []
        if request.conversation_history:
            for msg in request.conversation_history:
                _SESSIONS[session_id].append({
                    "role": msg.role,
                    "content": msg.content
                })
            logger.info(f"[AIAssistant] Restored {len(request.conversation_history)} messages for session {session_id}")
    _SESSION_TIMESTAMPS[session_id] = now
    session_history = _SESSIONS[session_id]

    # Filter tools by permission
    available_tool_defs = _filter_tools_by_permission(user_permissions, user_role)
    tool_names = [td["name"] for td in available_tool_defs]
    gemini_tools = _build_gemini_tools(available_tool_defs)

    # Build dynamic capabilities string based on available tools
    capabilities_list = []
    seen_caps = set()
    for name in tool_names:
        cap = _CAPABILITY_MAP.get(name)
        if cap and cap not in seen_caps:
            capabilities_list.append(cap)
            seen_caps.add(cap)
            
    if not capabilities_list:
        capabilities_str = "- Giải đáp thắc mắc và hỗ trợ thông tin chung"
    else:
        capabilities_str = "\n".join(capabilities_list)

    # Build system prompt
    company_info_str = f"Công ty của người dùng (nhà tuyển dụng): **{company_name}**" if company_name else ""
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
        role=user_role,
        username=username,
        company_info=company_info_str,
        available_tools=", ".join(tool_names) if tool_names else "Không có công cụ nào",
        capabilities=capabilities_str
    )

    # Load Gemini API key
    keys = _load_api_keys()
    if not keys:
        return AssistantChatResponse(
            reply="Xin lỗi, AI Assistant chưa được cấu hình API key. Vui lòng liên hệ Admin.",
            error="No API keys configured"
        )

    # Try multiple models
    models_to_try = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-1.5-flash-latest",
    ]

    actions_taken = []
    pending_action = None

    global _current_key_idx
    num_keys = len(keys)
    num_models = len(models_to_try)
    # Tối đa 12 lần thử (vừa xoay vòng key vừa xoay vòng model)
    max_attempts = min(12, num_keys * num_models)

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

            # Build conversation history for Gemini
            history_for_gemini = []
            for msg in session_history[-20:]:  # last 20 messages for context
                history_for_gemini.append(
                    {"role": msg["role"], "parts": [msg["content"]]}
                )

            # Build user message (possibly with image)
            user_parts = []

            # Add file/image context if provided
            if request.image_base64:
                # Gemini Vision - analyze image
                image_data = base64.b64decode(request.image_base64)
                user_parts.append(
                    genai.protos.Part(
                        inline_data=genai.protos.Blob(
                            mime_type="image/jpeg",
                            data=image_data
                        )
                    )
                )

            if request.file_content:
                user_parts.append(
                    genai.protos.Part(text=f"[Nội dung file đính kèm]:\n{request.file_content[:3000]}\n\n[Yêu cầu của người dùng]: {request.message}")
                )
            else:
                user_parts.append(genai.protos.Part(text=request.message))

            # Initialize Gemini model with tools
            model = genai.GenerativeModel(
                model_name=model_name,
                tools=gemini_tools if gemini_tools else None,
                system_instruction=system_prompt,
            )

            chat = model.start_chat(history=history_for_gemini)

            # Send message
            response = await chat.send_message_async(
                genai.protos.Content(parts=user_parts, role="user"),
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=2048,
                )
            )

            # Tool-calling loop (max 5 iterations)
            max_iterations = 5
            iteration = 0

            while iteration < max_iterations:
                iteration += 1

                # Check if there are function calls in the response
                fn_calls = []
                for part in response.parts:
                    if hasattr(part, 'function_call') and part.function_call and part.function_call.name:
                        fn_calls.append(part.function_call)
                    elif hasattr(part, 'function_calls') and part.function_calls:
                        for fc in part.function_calls:
                            if fc.name:
                                fn_calls.append(fc)

                if not fn_calls:
                    break  # No more tool calls, get final text response

                # Execute each function call
                fn_responses = []
                for fn_call in fn_calls:
                    tool_name = fn_call.name
                    raw_args = dict(fn_call.args) if fn_call.args else {}
                    
                    # Convert protobuf RepeatedComposite fields to standard Python lists
                    args = {}
                    for k, v in raw_args.items():
                        if hasattr(v, '__iter__') and not isinstance(v, (str, dict)):
                            args[k] = list(v)
                        else:
                            args[k] = v

                    logger.info(f"[AIAssistant] Calling tool: {tool_name}({args})")

                    # Find tool definition
                    tool_def = next((t for t in available_tool_defs if t["name"] == tool_name), None)

                    if tool_def and tool_def.get("action_type") == "preview":
                        # Preview action - generate preview data
                        result = await _execute_tool(tool_name, args, user_token)
                        action_type = "create_job" if tool_name == "preview_create_job" else "delete_job"
                        description = (f"Tạo tin tuyển dụng: {args.get('name', 'N/A')}" 
                                       if tool_name == "preview_create_job" 
                                       else f"Xóa tin tuyển dụng: {args.get('job_name', 'Không rõ tên')}")
                        pending_action = ActionItem(
                            action_type=action_type,
                            description=description,
                            data=result.get("job_data"),
                            requires_confirmation=True,
                            tool_name=tool_name
                        )
                    else:
                        # Read action - execute immediately
                        result = await _execute_tool(tool_name, args, user_token)
                        actions_taken.append(ActionItem(
                            action_type=f"tool_{tool_name}",
                            description=f"Đã truy vấn: {tool_name}",
                            data=result,
                            requires_confirmation=False,
                            tool_name=tool_name
                        ))

                    fn_responses.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=tool_name,
                                response={"result": json.dumps(result, ensure_ascii=False)[:3000]}
                            )
                        )
                    )

                # Send function results back to model
                success_sending = False
                send_attempts = 0
                max_send_attempts = len(keys)
                last_send_err_str = ""
                
                while send_attempts < max_send_attempts:
                    try:
                        response = await chat.send_message_async(
                            genai.protos.Content(parts=fn_responses, role="tool"),
                            generation_config=genai.types.GenerationConfig(
                                temperature=0.1,
                                max_output_tokens=2048,
                            )
                        )
                        success_sending = True
                        break
                    except Exception as send_err:
                        last_send_err_str = str(send_err)
                        logger.warning(f"[AIAssistant] Failed to send tool response (key index {curr_key_idx}): {last_send_err_str}")
                        send_attempts += 1
                        
                        # Rotate key
                        curr_key_idx = (curr_key_idx + 1) % num_keys
                        new_api_key = keys[curr_key_idx]
                        
                        # Reconfigure genai and recreate chat with history
                        genai.configure(api_key=new_api_key)
                        model = genai.GenerativeModel(
                            model_name=model_name,
                            tools=gemini_tools if gemini_tools else None,
                            system_instruction=system_prompt,
                        )
                        
                        # Start new chat with the current history
                        chat = model.start_chat(history=chat.history)
                
                if not success_sending:
                    raise Exception(f"All keys failed to send tool response. Last error: {last_send_err_str}")

            # Extract final text response
            final_text = ""
            for part in response.parts:
                if hasattr(part, 'text') and part.text:
                    final_text += part.text

            if not final_text or final_text.strip() == "Tôi đã xử lý yêu cầu của bạn.":
                # Try to generate an intelligent fallback message from actions_taken
                fallback_msg = ""
                if actions_taken:
                    for action in actions_taken:
                        tool_name = action.tool_name
                        data = action.data
                        if not data:
                            continue
                        
                        if tool_name in ["search_jobs", "get_my_jobs"]:
                            jobs = data.get("jobs", []) if isinstance(data, dict) else []
                            if not jobs and isinstance(data, list):
                                jobs = data
                            if jobs:
                                job_lines = []
                                for j in jobs[:5]:
                                    salary_str = ""
                                    if j.get("salaryMin") or j.get("salaryMax"):
                                        min_sal = j.get("salaryMin")
                                        max_sal = j.get("salaryMax")
                                        curr = j.get("salaryCurrency", "VND")
                                        if min_sal and max_sal:
                                            salary_str = f" ({min_sal}-{max_sal} {curr})"
                                        elif min_sal:
                                            salary_str = f" (Từ {min_sal} {curr})"
                                        elif max_sal:
                                            salary_str = f" (Lên đến {max_sal} {curr})"
                                    
                                    company = j.get("companyName") or "Chưa rõ công ty"
                                    loc = j.get("location") or "Toàn quốc"
                                    job_lines.append(f"- **{j.get('name')}** tại *{company}* - {loc}{salary_str}")
                                
                                fallback_msg = "Tôi đã tìm kiếm cơ sở dữ liệu và dưới đây là một số tin tuyển dụng phù hợp:\n\n" + "\n".join(job_lines)
                                if len(jobs) > 5:
                                    fallback_msg += f"\n\n*(Và {len(jobs) - 5} công việc khác. Hãy hỏi tôi chi tiết nếu cần!)*"
                                break
                                
                        elif tool_name == "get_job_detail":
                            job = data.get("job") if isinstance(data, dict) else data
                            if isinstance(job, dict) and job.get("name"):
                                name = job.get("name")
                                desc = job.get("description", "Không có mô tả")[:200]
                                reqs = job.get("requirements", "Không có yêu cầu")[:200]
                                comp = job.get("companyName") or "Chưa rõ công ty"
                                loc = job.get("location") or "Toàn quốc"
                                fallback_msg = (
                                    f"Dưới đây là chi tiết công việc **{name}** tại **{comp}**:\n"
                                    f"- **Địa điểm:** {loc}\n"
                                    f"- **Mô tả ngắn:** {desc}...\n"
                                    f"- **Yêu cầu:** {reqs}...\n\n"
                                    f"*(Nếu bạn muốn ứng tuyển hoặc xem đầy đủ hơn, vui lòng báo cho tôi!)*"
                                )
                                break
                                
                        elif tool_name == "predict_salary":
                            pred = data
                            if isinstance(pred, dict) and (pred.get("predictedSalary") or pred.get("salary_range")):
                                sal = pred.get("predictedSalary") or pred.get("predicted_salary")
                                sal_range = pred.get("salary_range") or f"{pred.get('minSalary')}-{pred.get('maxSalary')}" if pred.get('minSalary') else ""
                                title = pred.get("jobTitle") or "vị trí yêu cầu"
                                fallback_msg = (
                                    f"Kết quả phân tích mức lương cho **{title}**:\n"
                                    f"- Mức lương dự đoán trung bình: **{sal:,} VND**\n"
                                )
                                if sal_range:
                                    fallback_msg += f"- Dải lương phổ biến: **{sal_range}**\n"
                                break
                                
                        elif tool_name == "search_candidates":
                            cands = data.get("candidates", []) if isinstance(data, dict) else []
                            if not cands and isinstance(data, list):
                                cands = data
                            if cands:
                                cand_lines = []
                                for c in cands[:5]:
                                    name = c.get("fullName") or c.get("name") or "Ẩn danh"
                                    pos = c.get("position") or "Chưa cập nhật vị trí"
                                    exp = c.get("yearsOfExperience", 0)
                                    cand_lines.append(f"- **{name}** - {pos} ({exp} năm kinh nghiệm)")
                                fallback_msg = "Tôi tìm thấy một số ứng viên phù hợp với tiêu chí của bạn:\n\n" + "\n".join(cand_lines)
                                break
                                
                        elif tool_name == "get_my_company_info":
                            comp = data.get("company") if isinstance(data, dict) else data
                            if isinstance(comp, dict) and comp.get("name"):
                                fallback_msg = (
                                    f"Thông tin công ty của bạn:\n"
                                    f"- **Tên công ty:** {comp.get('name')}\n"
                                    f"- **Ngành nghề:** {comp.get('industry', 'Chưa cập nhật')}\n"
                                    f"- **Quy mô:** {comp.get('size', 'Chưa cập nhật')} nhân sự\n"
                                    f"- **Địa chỉ:** {comp.get('address', 'Chưa cập nhật')}"
                                )
                                break
                                
                        elif tool_name == "search_companies":
                            comps = data.get("companies", []) if isinstance(data, dict) else []
                            if not comps and isinstance(data, list):
                                comps = data
                            if comps:
                                comp_lines = []
                                for c in comps[:5]:
                                    name = c.get("name")
                                    ind = c.get("industry") or "Chưa rõ ngành"
                                    addr = c.get("address") or "Chưa cập nhật"
                                    comp_lines.append(f"- **{name}** ({ind}) - *{addr}*")
                                fallback_msg = "Tôi tìm thấy một số công ty phù hợp với tìm kiếm của bạn:\n\n" + "\n".join(comp_lines)
                                break
                                
                        elif tool_name == "get_my_resumes":
                            resumes = data.get("result", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                            if resumes:
                                res_lines = []
                                for r in resumes[:5]:
                                    name = r.get("title") or r.get("name") or "CV không tên"
                                    is_def = " (Mặc định)" if r.get("isDefault") else ""
                                    res_lines.append(f"- **{name}**{is_def}")
                                fallback_msg = "Danh sách các CV của bạn:\n\n" + "\n".join(res_lines)
                                break

                        elif tool_name == "get_my_applications":
                            apps = data.get("result", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                            if apps:
                                app_lines = []
                                for a in apps[:5]:
                                    j_name = a.get("jobName") or "Công việc không tên"
                                    status = a.get("status") or "Đang chờ duyệt"
                                    app_lines.append(f"- **{j_name}** - Trạng thái: *{status}*")
                                fallback_msg = "Danh sách các đơn ứng tuyển của bạn:\n\n" + "\n".join(app_lines)
                                break

                if fallback_msg:
                    final_text = fallback_msg + "\n\n*(Lưu ý: Phản hồi này được tự động tạo từ dữ liệu truy vấn vì kết nối AI chính bị gián đoạn hoặc quá tải)*"
                else:
                    final_text = "Tôi đã xử lý yêu cầu của bạn nhưng không nhận được phản hồi từ AI. Vui lòng thử lại sau ít phút hoặc dùng câu hỏi khác."

            # Save to session history
            session_history.append({"role": "user", "content": request.message})
            session_history.append({"role": "model", "content": final_text})

            # Keep last 50 messages
            if len(session_history) > 50:
                _SESSIONS[session_id] = session_history[-50:]

            # Build suggestions based on context
            suggestions = _generate_suggestions(user_role, actions_taken)

            # Lưu lại index thành công để lần sau tiếp tục từ đây
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
            logger.warning(f"[AIAssistant] Model {model_name} key index {curr_key_idx} failed: {err_str}")
            
            # Nếu bị lỗi rate limit (429 hoặc quota) hoặc lỗi authentication, đổi key ngay lập tức thay vì thử tiếp các model khác trên key này
            is_rate_limit = "429" in err_str or "quota" in err_str.lower() or "limit" in err_str.lower() or "unauthorized" in err_str.lower()
            if is_rate_limit:
                curr_key_idx = (curr_key_idx + 1) % num_keys
                curr_model_idx = 0
            else:
                # Lỗi khác (ví dụ: model không hỗ trợ 404), thử model tiếp theo của key này
                curr_model_idx = (curr_model_idx + 1) % num_models
                if curr_model_idx == 0:
                    curr_key_idx = (curr_key_idx + 1) % num_keys

    # Nếu tất cả các lần thử đều thất bại
    return AssistantChatResponse(
        reply="Xin lỗi, AI Assistant đang gặp sự cố kỹ thuật. Vui lòng thử lại sau ít phút.",
        error=f"All models/keys exhausted. Last error: {last_error}"
    )


async def confirm_create_job(
    job_data: dict,
    user_token: str,
    company_id: str,
) -> dict:
    """Thực sự tạo job sau khi HR đã xác nhận preview."""
    try:
        # Tự động lấy companyId từ ProfileService nếu không có
        if not company_id:
            try:
                prof_result = await _call_api("GET", "http://profileservice:8080/api/v1/customers/me", user_token)
                prof_data = prof_result.get("data") if isinstance(prof_result, dict) and "data" in prof_result else prof_result
                if isinstance(prof_data, dict):
                    company_id = prof_data.get("companyId", "")
                    logger.info(f"[AIAssistant] Retrieved companyId from ProfileService: {company_id}")
            except Exception as e:
                logger.error(f"[AIAssistant] Failed to get companyId from profile: {e}")

        # Lấy chi tiết công ty (companyName, companyLogo) từ CompanyService theo companyId
        company_name = None
        company_logo = None
        if company_id:
            try:
                comp_result = await _call_api("GET", f"http://companyservice:8080/api/v1/companies/{company_id}", user_token)
                comp_data = comp_result.get("data") if isinstance(comp_result, dict) and "data" in comp_result else comp_result
                if isinstance(comp_data, dict):
                    company_name = comp_data.get("name")
                    company_logo = comp_data.get("logo")
                    logger.info(f"[AIAssistant] Resolved matched company: {company_name} (ID: {company_id})")
            except Exception as e:
                logger.error(f"[AIAssistant] Failed to resolve company info for {company_id}: {e}")

        # Fallback nếu không có company_id (ví dụ tài khoản admin test không có công ty)
        if not company_id:
            try:
                comp_result = await _call_api("GET", "http://companyservice:8080/api/v1/companies", user_token)
                companies = comp_result.get("data", {}).get("result", [])
                if companies:
                    matched_company = companies[0]
                    company_id = matched_company.get("id", "")
                    company_name = matched_company.get("name")
                    company_logo = matched_company.get("logo")
                    logger.warning(f"[AIAssistant] Fallback resolve company for admin/test: {company_name} (ID: {company_id})")
            except Exception as e:
                logger.error(f"[AIAssistant] Fallback company resolve failed: {e}")

        # Resolve skill names to skillIds
        skill_ids = []
        skill_names = job_data.get("skill_names", [])
        if skill_names:
            try:
                skills_resp = await _call_api("GET", "http://jobhub_jobservice:8080/api/v1/skills/dropdown", user_token)
                skills_list = skills_resp.get("data") if isinstance(skills_resp, dict) and "data" in skills_resp else skills_resp
                if not isinstance(skills_list, list):
                    skills_list = []
                
                # Tạo map name -> id (lower case, stripped)
                skill_map = {s.get("name", "").lower().strip(): s.get("id") for s in skills_list if s.get("name") and s.get("id")}
                
                for name in skill_names:
                    name_lower = name.lower().strip()
                    if name_lower in skill_map:
                        skill_ids.append(skill_map[name_lower])
                    else:
                        # Fuzzy match tương đối
                        matched = False
                        for k, v in skill_map.items():
                            if name_lower in k or k in name_lower:
                                skill_ids.append(v)
                                matched = True
                                break
                        if not matched:
                            logger.warning(f"[AIAssistant] Skill not found in dropdown: {name}")
            except Exception as e:
                logger.error(f"[AIAssistant] Failed to resolve skill IDs: {e}")

        # Format EndDate (deadline)
        deadline = job_data.get("deadline")
        end_date = None
        if deadline:
            try:
                # Đảm bảo deadline đúng format ISO hoặc string YYYY-MM-DD
                end_date = f"{deadline}T23:59:59Z"
            except Exception:
                end_date = None

        # Build API payload cho C# CreateJobRequest
        payload = {
            "name": job_data.get("name", ""),
            "description": job_data.get("description", ""),
            "requirements": job_data.get("requirements", ""),
            "benefits": job_data.get("benefits", ""),
            "location": job_data.get("location", "Hà Nội"),
            "salaryMin": job_data.get("salary_min"),
            "salaryMax": job_data.get("salary_max"),
            "salaryCurrency": job_data.get("salary_currency", "VND"),
            "quantity": job_data.get("quantity", 1),
            "startDate": None, # Sẽ để C# tự sinh ngày hiện tại (nếu trống)
            "endDate": end_date,
            "experienceRequired": job_data.get("experience_required"),
            "category": normalize_category(job_data.get("category")),
            "skillIds": skill_ids,
            "companyId": company_id,
            "companyName": company_name,
            "companyLogo": company_logo
        }

        result = await _call_api("POST", "http://jobhub_jobservice:8080/api/v1/jobs", user_token, payload)

        if "error" in result and result["error"] is not None:
            return {"success": False, "message": result["error"]}

        job = result.get("data", result)
        return {
            "success": True,
            "message": f"Đã tạo thành công tin tuyển dụng '{job_data.get('name')}'",
            "job": job
        }
    except Exception as e:
        logger.error(f"[AIAssistant] confirm_create_job failed: {e}")
        return {"success": False, "message": str(e)}

async def confirm_delete_job(
    job_id: str,
    user_token: str
) -> dict:
    """Thực sự xóa job sau khi HR đã xác nhận preview."""
    try:
        result = await _call_api("DELETE", f"http://jobhub_jobservice:8080/api/v1/jobs/{job_id}", user_token)
        if "error" in result and result["error"] is not None:
            return {"success": False, "message": result["error"]}
        return {
            "success": True,
            "message": f"Đã xóa thành công tin tuyển dụng ID: {job_id}",
            "job": result.get("data")
        }
    except Exception as e:
        logger.error(f"[AIAssistant] confirm_delete_job failed: {e}")
        return {"success": False, "message": str(e)}

async def extract_job_from_image(image_base64: str) -> dict:
    """Dùng Gemini Vision để trích xuất thông tin JD từ ảnh."""
    keys = _load_api_keys()
    if not keys:
        return {}

    prompt = """
Hãy phân tích ảnh này và trích xuất thông tin tuyển dụng theo định dạng JSON thuần túy (không dùng markdown).

Trả về JSON với các trường sau (bỏ trống nếu không có thông tin):
{
  "name": "Tên vị trí tuyển dụng",
  "description": "Mô tả công việc",
  "requirements": "Yêu cầu ứng viên",
  "benefits": "Quyền lợi và phúc lợi",
  "location": "Địa điểm làm việc",
  "salary_min": null,
  "salary_max": null,
  "salary_currency": "VND",
  "quantity": 1,
  "deadline": null,
  "skill_names": ["skill1", "skill2"],
  "experience_required": "Yêu cầu kinh nghiệm",
  "category": "Ngành nghề công việc"
}
    """

    genai.configure(api_key=keys[0])
    model = genai.GenerativeModel("gemini-2.5-flash")

    image_data = base64.b64decode(image_base64)

    try:
        response = await model.generate_content_async(
            contents=[
                genai.protos.Part(
                    inline_data=genai.protos.Blob(mime_type="image/jpeg", data=image_data)
                ),
                genai.protos.Part(text=prompt)
            ],
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"[AIAssistant] extract_job_from_image failed: {e}")
        return {}

def clear_session(session_id: str):
    """Xóa lịch sử hội thoại của một session."""
    _SESSIONS.pop(session_id, None)
    _SESSION_TIMESTAMPS.pop(session_id, None)
