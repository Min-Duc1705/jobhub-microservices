# app/services/ai_assistant_service/executor/token_utils.py
"""
Tiện ích parse JWT token để lấy customerId, role và kiểm tra quyền điều hướng.
"""
import base64
import json
import logging

logger = logging.getLogger(__name__)


def _get_customer_id_from_token(token: str) -> str:
    try:
        parts = token.split(".")
        if len(parts) == 3:
            payload_b64 = parts[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding
            payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8", errors="ignore"))
            sub = (payload.get("sub") or
                   payload.get("id") or
                   payload.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier") or
                   "")
            if isinstance(sub, list):
                sub = next((s for s in sub if s), "")
            logger.info(f"[AIAssistant] Parsed customerId from token: {sub}")
            return str(sub)
    except Exception as e:
        logger.error(f"[AIAssistant] Error parsing customerId from token: {e}")
    return ""


def _get_role_from_token(token: str) -> str:
    try:
        parts = token.split(".")
        if len(parts) == 3:
            payload_b64 = parts[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding
            payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8", errors="ignore"))
            role = (payload.get("http://schemas.microsoft.com/ws/2008/06/identity/claims/role") or
                    payload.get("role") or
                    "USER")
            if isinstance(role, list):
                role = next((r for r in role if r), "USER")
            return str(role).upper()
    except Exception as e:
        logger.error(f"[AIAssistant] Error parsing role from token: {e}")
    return "USER"


def _is_path_allowed_for_role(path: str, role: str) -> bool:
    role = (role or "USER").upper()
    if role == "ADMIN":
        return True

    path_lower = path.lower()

    # 1. Admin paths
    if path_lower.startswith("/admin"):
        return role != "CANDIDATE" and role != "USER"

    # 2. HR paths
    if path_lower.startswith("/hr"):
        return role == "HR"

    # 3. Candidate restricted paths
    if "/applied-jobs" in path_lower or "/saved-jobs" in path_lower:
        return role == "CANDIDATE"

    # 4. Profile & Resume Builder
    if path_lower.startswith("/candidate/"):
        return True

    # 5. Public paths
    return True
