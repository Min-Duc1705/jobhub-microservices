import base64
import logging
import uuid
import os
import json
import redis.asyncio as async_redis
from fastapi import APIRouter, HTTPException, Header, UploadFile, File
from typing import Optional

from app.schemas.assistant import (
    AssistantChatRequest, AssistantChatResponse, AssistantConfirmRequest
)
from app.services import ai_assistant_service

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])
logger = logging.getLogger(__name__)

redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_client = async_redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)

async def _fetch_user_permissions_from_redis(email: str) -> Optional[list[dict]]:
    """Thử lấy danh sách permissions của user từ Redis cache (perm:{email})."""
    if not email:
        return None
    try:
        redis_key = f"perm:{email}"
        cached_data = await redis_client.get(redis_key)
        if cached_data:
            raw_perms = json.loads(cached_data)
            if isinstance(raw_perms, list):
                permissions = []
                for p in raw_perms:
                    method = p.get("Method") or p.get("method")
                    api_path = p.get("ApiPath") or p.get("apiPath")
                    if method and api_path:
                        permissions.append({
                            "method": method,
                            "apiPath": api_path
                        })
                logger.info(f"[AssistantRouter] Loaded {len(permissions)} permissions from Redis cache for {email}")
                return permissions
    except Exception as e:
        logger.error(f"[AssistantRouter] Failed to fetch permissions from Redis: {e}")
    return None


import httpx

def _extract_user_info_from_token(authorization: str) -> dict:
    """Parse JWT payload để lấy user info (không verify signature, chỉ decode)."""
    import base64, json
    try:
        # JWT format: header.payload.signature
        parts = authorization.replace("Bearer ", "").split(".")
        if len(parts) != 3:
            return {}

        # Decode payload (base64url)
        payload_b64 = parts[1]
        # Add padding
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding

        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        
        # Map .NET claim types to standard keys
        role = payload.get("role") or payload.get("http://schemas.microsoft.com/ws/2008/06/identity/claims/role")
        if role:
            payload["role"] = role
            
        username = payload.get("username") or payload.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name") or payload.get("sub")
        if username:
            payload["username"] = username
            
        email = payload.get("email") or payload.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress")
        if email:
            payload["email"] = email
            
        return payload
    except Exception:
        return {}


async def _fetch_user_profile_and_permissions(token: str) -> dict:
    """Gọi AuthService để lấy thông tin account chi tiết và permissions thực tế."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = "http://authservice:8080/api/v1/auth/account"
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                body = resp.json()
                
                # Check wrapper "data"
                data = body.get("data") if "data" in body else body
                if not data:
                    return {}
                    
                user = data.get("user") or {}
                role_obj = user.get("role") or {}
                role_name = role_obj.get("name") or "USER"
                
                raw_perms = role_obj.get("permissions") or []
                permissions = []
                for p in raw_perms:
                    permissions.append({
                        "method": p.get("method"),
                        "apiPath": p.get("apiPath")
                    })
                    
                return {
                    "role": role_name,
                    "permissions": permissions,
                    "username": user.get("username") or user.get("email", "Người dùng")
                }
            else:
                logger.warning(f"[AssistantRouter] Failed to fetch account from authservice: HTTP {resp.status_code}")
                return {}
        except Exception as e:
            logger.error(f"[AssistantRouter] Error calling authservice: {e}")
            return {}


async def _fetch_user_company_name(token: str, role: str) -> str:
    """Nếu user là HR/Employer, fetch tên công ty của họ từ ProfileService -> CompanyService."""
    role_upper = (role or "USER").upper()
    if not ("HR" in role_upper or "EMPLOYER" in role_upper or "ADMIN" in role_upper):
        return ""
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Bước 1: Gọi ProfileService lấy profile của tôi
    profile_url = "http://profileservice:8080/api/v1/customers/me"
    async with httpx.AsyncClient(timeout=3.0) as client:
        try:
            resp = await client.get(profile_url, headers=headers)
            if resp.status_code == 200:
                body = resp.json()
                data = body.get("data") if "data" in body else body
                if not data:
                    return ""
                
                company_id = data.get("companyId")
                if not company_id:
                    return ""
                
                # Bước 2: Gọi CompanyService lấy chi tiết công ty theo ID
                comp_url = f"http://companyservice:8080/api/v1/companies/{company_id}"
                comp_resp = await client.get(comp_url, headers=headers)
                if comp_resp.status_code == 200:
                    comp_body = comp_resp.json()
                    comp_data = comp_body.get("data") if "data" in comp_body else comp_body
                    if comp_data:
                        company_name = comp_data.get("name", "")
                        logger.info(f"[AssistantRouter] Found company name for HR: {company_name}")
                        return company_name
            return ""
        except Exception as e:
            logger.error(f"[AssistantRouter] Error fetching user company name: {e}")
            return ""


@router.post("/chat", response_model=AssistantChatResponse, summary="Chat với AI Assistant")
async def chat(
    request: AssistantChatRequest,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    """
    Gửi tin nhắn đến AI Assistant và nhận phản hồi thông minh.
    AI sẽ phân tích yêu cầu và thực hiện các hành động phù hợp với quyền hạn của user.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    user_token = authorization.replace("Bearer ", "")
    session_id = x_session_id or str(uuid.uuid4())

    # Decode JWT để lấy thông tin fallback
    jwt_payload = _extract_user_info_from_token(authorization)
    email = jwt_payload.get("email", "")
    role_name = jwt_payload.get("role", "USER")
    username = jwt_payload.get("username", "Người dùng")
    permissions = []

    # 1. Thử lấy permissions từ Redis cache
    redis_permissions = await _fetch_user_permissions_from_redis(email)
    if redis_permissions is not None:
        permissions = redis_permissions
    else:
        # 2. Fallback gọi authservice
        auth_data = await _fetch_user_profile_and_permissions(user_token)
        if auth_data:
            permissions = auth_data.get("permissions", [])
            role_name = auth_data.get("role", role_name)
            username = auth_data.get("username", username)

    # Fetch tên công ty của HR
    company_name = await _fetch_user_company_name(user_token, role_name)

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
        return {
            "statusCode": 200,
            "message": "Đã hủy hành động",
            "data": {"cancelled": True}
        }

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

    if content_type.startswith("image/"):
        # Return base64 for image
        image_b64 = base64.b64encode(file_bytes).decode("utf-8")

        # Try to extract job info from image
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
        # For PDF/Word, return raw bytes as text (simplified)
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
