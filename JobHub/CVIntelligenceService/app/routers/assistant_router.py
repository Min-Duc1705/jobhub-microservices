# app/routers/assistant_router.py
"""
API endpoints cho AI Assistant.
Helper logic (Redis, JWT, auth fetch) đã tách sang assistant_router_helpers.py.
"""
import base64
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, UploadFile, File

from app.schemas.assistant import (
    AssistantChatRequest, AssistantChatResponse, AssistantConfirmRequest
)
from app.services import ai_assistant_service
from .assistant_router_helpers import (
    fetch_user_permissions_from_redis,
    extract_user_info_from_token,
    fetch_user_profile_and_permissions,
    fetch_user_company_name,
    parse_skills_from_file_bytes,
)

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=AssistantChatResponse, summary="Chat với AI Assistant")
async def chat(
    request: AssistantChatRequest,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    """
    Gửi tin nhắn đến AI Assistant và nhận phản hồi thông minh.
    Permissions được lấy từ Redis cache (perm:{email}) — được AuthService ghi khi login/refresh.
    Fallback gọi AuthService chỉ khi Redis miss.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    user_token = authorization.replace("Bearer ", "")
    session_id = x_session_id or str(uuid.uuid4())

    # Decode JWT — lấy email, role, username trực tiếp (không verify signature)
    jwt_payload = extract_user_info_from_token(authorization)
    email     = jwt_payload.get("email", "")
    role_name = jwt_payload.get("role", "USER")
    username  = jwt_payload.get("username", "Người dùng")

    # ── Lấy permissions và company_name song song để tối ưu hiệu suất (Parallel setup) ──
    import asyncio
    permissions_task = fetch_user_permissions_from_redis(email)
    company_task = fetch_user_company_name(user_token, role_name)
    permissions, company_name = await asyncio.gather(permissions_task, company_task)

    if permissions is None:
        # Redis miss → gọi AuthService một lần duy nhất
        logger.warning(f"[AssistantRouter] Redis miss cho '{email}', fallback AuthService")
        auth_data = await fetch_user_profile_and_permissions(user_token)
        permissions = auth_data.get("permissions", []) if auth_data else []
        if auth_data:
            # AuthService trả role/username mới nhất (vd admin vừa đổi role user)
            role_name = auth_data.get("role", role_name)
            username  = auth_data.get("username", username)
    else:
        # Redis hit — dùng permissions từ cache, role/username từ JWT là đủ
        logger.info(f"[AssistantRouter] Redis hit: {len(permissions)} perms cho '{email}' (role={role_name})")

    try:
        response = await ai_assistant_service.process_assistant_message(
            request=request,
            user_token=user_token,
            user_permissions=permissions,
            user_role=role_name,
            username=username,
            session_id=session_id,
            company_name=company_name,
        )
        return response
    except Exception as e:
        import traceback
        logger.error(f"[AssistantRouter] Uncaught error: {e}\n{traceback.format_exc()}")
        return AssistantChatResponse(
            reply="⚠️ Đã xảy ra lỗi kỹ thuật nội bộ. Vui lòng thử lại sau.",
            error=str(e)
        )


@router.post("/confirm-action", summary="Xác nhận thực hiện một hành động đề xuất")
async def confirm_action(
    request: AssistantConfirmRequest,
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    Xác nhận hoặc hủy bỏ một hành động mà AI đã đề xuất (ví dụ: tạo job sau khi xem preview).
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    user_token = authorization.replace("Bearer ", "")

    if not request.confirmed:
        return {"statusCode": 200, "message": "Đã hủy hành động", "data": {"cancelled": True}}

    if request.action_type == "create_job":
        job_data = request.payload
        company_id = request.payload.get("company_id", "")
        result = await ai_assistant_service.confirm_create_job(
            job_data=job_data,
            user_token=user_token,
            company_id=company_id
        )
        return {
            "statusCode": 200 if result.get("success") else 500,
            "message": result.get("message"),
            "data": result.get("job")
        }

    elif request.action_type == "delete_job":
        job_id = request.payload.get("job_id", "")
        result = await ai_assistant_service.confirm_delete_job(
            job_id=job_id,
            user_token=user_token
        )
        return {
            "statusCode": 200 if result.get("success") else 500,
            "message": result.get("message"),
            "data": result.get("job")
        }

    return {
        "statusCode": 400,
        "message": f"Loại action '{request.action_type}' chưa được hỗ trợ",
        "data": None
    }


@router.post("/upload", summary="Upload file/ảnh để AI phân tích")
async def upload_file(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    Upload file (PDF, Word, ảnh JPG/PNG) để AI trích xuất nội dung.
    Trả về file_content (text) để dùng trong endpoint /chat.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    content_type = file.content_type or ""
    file_bytes = await file.read()
    filename = file.filename or ""

    if filename.lower().endswith((".csv", ".xlsx", ".xls")):
        skills = parse_skills_from_file_bytes(file_bytes, filename)
        skills_str = ", ".join(skills) if skills else ""
        text_content = f"Danh sách các kỹ năng trích xuất từ file: {skills_str}" if skills_str else "Không tìm thấy kỹ năng nào trong file."
        return {
            "statusCode": 200,
            "message": "Đã đọc file import kỹ năng thành công",
            "data": {
                "type": "skills_file",
                "file_content": text_content,
                "file_name": filename,
            }
        }

    if content_type.startswith("image/"):
        image_b64 = base64.b64encode(file_bytes).decode("utf-8")
        extracted = await ai_assistant_service.extract_job_from_image(image_b64)
        return {
            "statusCode": 200,
            "message": "Đã phân tích ảnh thành công",
            "data": {
                "type": "image",
                "image_base64": image_b64,
                "extracted_data": extracted,
                "file_name": file.filename,
            }
        }

    elif content_type == "text/plain":
        text_content = file_bytes.decode("utf-8", errors="ignore")
        return {
            "statusCode": 200,
            "message": "Đã đọc file text thành công",
            "data": {
                "type": "text",
                "file_content": text_content[:5000],
                "file_name": file.filename,
            }
        }

    else:
        try:
            text_content = file_bytes.decode("utf-8", errors="ignore")
        except Exception:
            text_content = ""
        return {
            "statusCode": 200,
            "message": "Đã nhận file",
            "data": {
                "type": "document",
                "file_content": text_content[:3000],
                "file_name": file.filename,
            }
        }


@router.delete("/session", summary="Xóa lịch sử hội thoại")
async def clear_session(
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    """Xóa lịch sử hội thoại của session hiện tại."""
    if x_session_id:
        ai_assistant_service.clear_session(x_session_id)
    return {"statusCode": 200, "message": "Đã xóa lịch sử hội thoại"}


@router.get("/tools/definitions", summary="Lấy danh sách tất cả tool definitions (dùng cho Admin UI)")
async def get_tool_definitions(
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    Trả về danh sách toàn bộ AI tool definitions từ tools/definitions.py.
    Admin dùng endpoint này để biết các tool hợp lệ khi tạo mới AI Tool qua UI.
    """
    from app.services.ai_assistant_service.tools import _ALL_TOOL_DEFS

    result = [
        {
            "name": t["name"],
            "description": t.get("description", ""),
            "action_type": t.get("action_type", "read"),
            "permissions_required": [
                {"method": m, "apiPath": p}
                for m, p in t.get("permissions_required", [])
            ],
        }
        for t in _ALL_TOOL_DEFS
    ]

    return {
        "statusCode": 200,
        "message": "Lấy danh sách tool definitions thành công",
        "data": result
    }


@router.post("/import", summary="AI Import dữ liệu từ file Excel/CSV")
async def ai_import(
    import_type: str,
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    AI thực hiện import dữ liệu từ file Excel/CSV thay mặt Admin.

    - **import_type**: `users` | `skills` | `companies` | `jobs`
    - **file**: File Excel (.xlsx) hoặc CSV (.csv)

    Endpoint này validate permission của user trước, sau đó forward file
    đến đúng microservice tương ứng.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    user_token = authorization.replace("Bearer ", "")
    jwt_payload = extract_user_info_from_token(authorization)
    email = jwt_payload.get("email", "")

    # ── Validate permission ──────────────────────────────────────────────────
    permissions = await fetch_user_permissions_from_redis(email)
    if permissions is None:
        auth_data = await fetch_user_profile_and_permissions(user_token)
        permissions = auth_data.get("permissions", []) if auth_data else []

    _IMPORT_PERMISSION_MAP = {
        "users":     ("POST", "/api/v1/users/import"),
        "skills":    ("POST", "/api/v1/skills/import"),
        "companies": ("POST", "/api/v1/companies/import"),
        "jobs":      ("POST", "/api/v1/admin/jobs/import"),
    }

    if import_type not in _IMPORT_PERMISSION_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"import_type không hợp lệ. Chỉ nhận: {list(_IMPORT_PERMISSION_MAP.keys())}"
        )

    required_method, required_path = _IMPORT_PERMISSION_MAP[import_type]
    has_permission = any(
        p.get("method") == required_method and p.get("apiPath") == required_path
        for p in permissions
    )
    if not has_permission:
        raise HTTPException(
            status_code=403,
            detail=f"Bạn không có quyền import {import_type}. Cần permission: {required_method} {required_path}"
        )

    # ── Validate file type ───────────────────────────────────────────────────
    allowed_types = {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
        "application/vnd.ms-excel",                                            # .xls
        "text/csv",
        "application/csv",
    }
    filename = file.filename or f"import_{import_type}.xlsx"
    content_type = file.content_type or "application/octet-stream"

    if content_type not in allowed_types and not filename.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(
            status_code=400,
            detail="Chỉ hỗ trợ file Excel (.xlsx, .xls) hoặc CSV (.csv)"
        )

    file_bytes = await file.read()

    # ── Forward đến đúng service ─────────────────────────────────────────────
    _IMPORT_URL_MAP = {
        "users":     "http://authservice:8080/api/v1/users/import",
        "skills":    "http://jobhub_jobservice:8080/api/v1/skills/import",
        "companies": "http://companyservice:8080/api/v1/companies/import",
        "jobs":      "http://jobhub_jobservice:8080/api/v1/admin/jobs/import",
    }

    from app.services.ai_assistant_service.api_client import _call_api_multipart
    result = await _call_api_multipart(
        url=_IMPORT_URL_MAP[import_type],
        token=user_token,
        file_bytes=file_bytes,
        filename=filename,
        content_type=content_type,
    )

    if result.get("success"):
        data = result.get("data", {})
        # Lấy summary từ response của service (nếu có)
        inner = data.get("data", data)
        total       = inner.get("total", inner.get("totalImported", "?"))
        success_cnt = inner.get("success", inner.get("successCount", total))
        failed_cnt  = inner.get("failed",  inner.get("failedCount", 0))

        return {
            "statusCode": 200,
            "message": f"✅ Import {import_type} thành công!",
            "data": {
                "import_type":   import_type,
                "file_name":     filename,
                "total":         total,
                "success_count": success_cnt,
                "failed_count":  failed_cnt,
                "details":       inner.get("errors", inner.get("failedRows", [])),
            }
        }
    else:
        raise HTTPException(
            status_code=422,
            detail=f"Import thất bại: {result.get('error', 'Lỗi không xác định')}"
        )
