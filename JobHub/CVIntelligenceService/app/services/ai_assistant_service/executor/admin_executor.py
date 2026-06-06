# app/services/ai_assistant_service/executor/admin_executor.py
"""
Executor cho các tools dành riêng cho Admin:
  Users    : get_all_users, get_user_detail, update_user, delete_user, reset_user_password
  Roles    : get_all_roles
  Perms    : get_all_permissions
  Company  : verify_company, delete_company
  Customer : delete_customer
"""
import logging
from ..api_client import _call_api

logger = logging.getLogger(__name__)

_AUTH_BASE    = "http://authservice:8080/api/v1"
_COMPANY_BASE = "http://companyservice:8080/api/v1/companies"
_PROFILE_BASE = "http://profileservice:8080/api/v1/customers"


# ── User management ────────────────────────────────────────────────────────────

async def execute_get_all_users(args: dict, user_token: str) -> dict:
    params = {"pageSize": int(args.get("pageSize", 20))}
    if args.get("keyword"):
        params["searchTerm"] = args["keyword"]
    if args.get("status"):
        params["status"] = args["status"]

    result = await _call_api("GET", f"{_AUTH_BASE}/users", user_token, params=params)
    users_raw = result.get("data", {}).get("result", [])
    users = [
        {
            "id":       u.get("id"),
            "email":    u.get("email"),
            "username": u.get("username"),
            "role":     u.get("role"),
            "status":   u.get("status"),
            "isActive": u.get("isActive"),
        }
        for u in users_raw
    ]
    total = result.get("data", {}).get("meta", {}).get("total", len(users))
    return {"users": users, "total": total}


async def execute_get_user_detail(args: dict, user_token: str) -> dict:
    user_id = args.get("user_id", "")
    result = await _call_api("GET", f"{_AUTH_BASE}/users/{user_id}", user_token)
    return {"user": result.get("data", result)}


async def execute_update_user(args: dict, user_token: str) -> dict:
    user_id = args.get("user_id", "")
    
    # Fetch current user info first to get mandatory fields for update request
    try:
        current_resp = await _call_api("GET", f"{_AUTH_BASE}/users/{user_id}", user_token)
        current_data = current_resp.get("data") if isinstance(current_resp, dict) and "data" in current_resp else current_resp
    except Exception as e:
        logger.warning(f"Failed to fetch current user info for update fallback: {e}")
        current_data = {}

    if not isinstance(current_data, dict):
        current_data = {}

    if "user" in current_data:
        current_data = current_data["user"]

    # Extract roleId from current role object if roleId is not provided
    curr_role_id = None
    if isinstance(current_data.get("role"), dict):
        curr_role_id = current_data.get("role", {}).get("id")
    else:
        curr_role_id = current_data.get("roleId")

    payload = {
        "username": args.get("username") or current_data.get("username", ""),
        "email":    args.get("email") or current_data.get("email", ""),
        "status":   current_data.get("status", "Active"),
        "roleId":   args.get("roleId") or curr_role_id
    }

    if args.get("isActive") is not None:
        payload["status"] = "Active" if args["isActive"] else "Deactivated"

    return await _call_api("PUT", f"{_AUTH_BASE}/users/{user_id}", user_token, json_data=payload)


async def execute_delete_user(args: dict, user_token: str) -> dict:
    user_id = args.get("user_id", "")
    return await _call_api("DELETE", f"{_AUTH_BASE}/users/{user_id}", user_token)


async def execute_reset_user_password(args: dict, user_token: str) -> dict:
    user_id      = args.get("user_id", "")
    new_password = args.get("new_password", "")
    
    email = "test@jobhub.vn"  # fallback dummy email
    try:
        current_resp = await _call_api("GET", f"{_AUTH_BASE}/users/{user_id}", user_token)
        current_data = current_resp.get("data") if isinstance(current_resp, dict) and "data" in current_resp else current_resp
        if isinstance(current_data, dict) and "user" in current_data:
            current_data = current_data["user"]
        if isinstance(current_data, dict) and current_data.get("email"):
            email = current_data["email"]
    except Exception as e:
        logger.warning(f"Failed to fetch current user info for reset password fallback email: {e}")
        
    payload = {
        "email": email,
        "otpCode": "000000",
        "newPassword": new_password
    }
    return await _call_api(
        "PATCH", f"{_AUTH_BASE}/users/{user_id}/reset-password",
        user_token, json_data=payload
    )


# ── Roles ──────────────────────────────────────────────────────────────────────

async def execute_get_all_roles(args: dict, user_token: str) -> dict:
    params = {"pageSize": int(args.get("pageSize", 50))}
    if args.get("keyword"):
        params["searchTerm"] = args["keyword"]
    result = await _call_api("GET", f"{_AUTH_BASE}/roles", user_token, params=params)
    roles_raw = result.get("data", {}).get("result", [])
    roles = [
        {
            "id":          r.get("id"),
            "name":        r.get("name"),
            "description": r.get("description"),
            "isActive":    r.get("isActive"),
        }
        for r in roles_raw
    ]
    total = result.get("data", {}).get("meta", {}).get("total", len(roles))
    return {"roles": roles, "total": total}


# ── Permissions ────────────────────────────────────────────────────────────────

async def execute_get_all_permissions(args: dict, user_token: str) -> dict:
    params = {"pageSize": int(args.get("pageSize", 100))}
    if args.get("keyword"):
        params["searchTerm"] = args["keyword"]
    if args.get("module"):
        params["module"] = args["module"].upper()
    if args.get("method"):
        params["method"] = args["method"].upper()

    result = await _call_api("GET", f"{_AUTH_BASE}/permissions", user_token, params=params)
    perms_raw = result.get("data", {}).get("result", [])
    perms = [
        {
            "id":      p.get("id"),
            "name":    p.get("name"),
            "apiPath": p.get("apiPath"),
            "method":  p.get("method"),
            "module":  p.get("module"),
        }
        for p in perms_raw
    ]
    total = result.get("data", {}).get("meta", {}).get("total", len(perms))
    return {"permissions": perms, "total": total}


# ── Company admin actions ──────────────────────────────────────────────────────

async def execute_verify_company(args: dict, user_token: str) -> dict:
    """Admin xác minh công ty (isVerified = true)."""
    company_id = args.get("company_id", "")
    return await _call_api("PATCH", f"{_COMPANY_BASE}/{company_id}/verify", user_token)


async def execute_delete_company(args: dict, user_token: str) -> dict:
    """Admin xóa công ty theo ID."""
    company_id = args.get("company_id", "")
    return await _call_api("DELETE", f"{_COMPANY_BASE}/{company_id}", user_token)


# ── Customer admin actions ─────────────────────────────────────────────────────

async def execute_delete_customer(args: dict, user_token: str) -> dict:
    """Admin xóa hồ sơ customer theo ID."""
    customer_id = args.get("customer_id", "")
    return await _call_api("DELETE", f"{_PROFILE_BASE}/{customer_id}", user_token)


# ── Admin jobs (không bị filter PUBLISHED) ────────────────────────────────────

async def execute_get_admin_jobs(args: dict, user_token: str) -> dict:
    """Admin xem tất cả jobs mọi trạng thái (DRAFT, PUBLISHED, CLOSED)."""
    params = {"pageSize": int(args.get("pageSize", 20))}
    if args.get("keyword"):
        params["searchTerm"] = args["keyword"]
    if args.get("status"):
        params["status"] = args["status"].upper()
    if args.get("companyId"):
        params["companyId"] = args["companyId"]

    result = await _call_api(
        "GET", "http://jobhub_jobservice:8080/api/v1/admin/jobs",
        user_token, params=params
    )
    raw = result.get("data", {}).get("result", [])
    jobs = [
        {
            "id":          j.get("id"),
            "name":        j.get("name"),
            "companyName": j.get("companyName"),
            "status":      j.get("status"),
            "location":    j.get("location"),
            "createdDate": j.get("createdDate"),
        }
        for j in raw
    ]
    total = result.get("data", {}).get("meta", {}).get("total", len(jobs))
    return {"jobs": jobs, "total": total}


# ── Auth/Account ──────────────────────────────────────────────────────────────

async def execute_get_my_account(args: dict, user_token: str) -> dict:
    """Lấy thông tin tài khoản đang đăng nhập (auth info từ AuthService)."""
    result = await _call_api("GET", f"{_AUTH_BASE}/auth/account", user_token)
    return {"account": result.get("data", result)}


# ── Role CRUD (Admin) ──────────────────────────────────────────────────────────

async def execute_create_role(args: dict, user_token: str) -> dict:
    """Admin tạo role mới."""
    payload = {"name": args.get("name", "").strip()}
    if args.get("description"):
        payload["description"] = args["description"]
    if args.get("permissionIds"):
        payload["permissionIds"] = args["permissionIds"]
    return await _call_api("POST", f"{_AUTH_BASE}/roles", user_token, json_data=payload)


async def execute_update_role(args: dict, user_token: str) -> dict:
    """Admin cập nhật role theo ID."""
    role_id = args.get("role_id", "")
    
    try:
        current_resp = await _call_api("GET", f"{_AUTH_BASE}/roles/{role_id}", user_token)
        current_data = current_resp.get("data") if isinstance(current_resp, dict) and "data" in current_resp else current_resp
    except Exception as e:
        logger.warning(f"Failed to fetch current role info: {e}")
        current_data = {}

    if not isinstance(current_data, dict):
        current_data = {}

    if "role" in current_data:
        role_info = current_data["role"]
    else:
        role_info = current_data

    curr_perm_ids = []
    if isinstance(role_info.get("permissions"), list):
        curr_perm_ids = [p.get("id") for p in role_info["permissions"] if isinstance(p, dict) and p.get("id")]

    final_perm_ids = args.get("permissionIds") if args.get("permissionIds") is not None else curr_perm_ids
    if not final_perm_ids:
        try:
            logger.info("No permissions found for update_role. Fetching permissions to use as fallback...")
            perms_resp = await _call_api("GET", f"{_AUTH_BASE}/permissions?pageSize=1", user_token)
            perms_list = perms_resp.get("data", {}).get("result", [])
            if perms_list and perms_list[0].get("id"):
                final_perm_ids = [perms_list[0]["id"]]
                logger.info(f"Using fallback permission ID: {final_perm_ids}")
        except Exception as e:
            logger.warning(f"Failed to fetch permissions fallback: {e}")

    payload = {
        "name":        args.get("name") or role_info.get("name", ""),
        "description": args.get("description") if args.get("description") is not None else role_info.get("description"),
        "isActive":    args.get("isActive") if args.get("isActive") is not None else role_info.get("isActive", True),
        "permissionIds": final_perm_ids
    }
    return await _call_api("PUT", f"{_AUTH_BASE}/roles/{role_id}", user_token, json_data=payload)


async def execute_delete_role(args: dict, user_token: str) -> dict:
    """Admin xóa role theo ID."""
    role_id = args.get("role_id", "")
    return await _call_api("DELETE", f"{_AUTH_BASE}/roles/{role_id}", user_token)


# ── Permission CRUD (Admin) ────────────────────────────────────────────────────

async def execute_create_permission(args: dict, user_token: str) -> dict:
    """Admin tạo permission mới."""
    payload = {
        "name":    args.get("name", ""),
        "apiPath": args.get("api_path", ""),
        "method":  args.get("method", "").upper(),
        "module":  args.get("module", "").upper(),
    }
    return await _call_api("POST", f"{_AUTH_BASE}/permissions", user_token, json_data=payload)


async def execute_update_permission(args: dict, user_token: str) -> dict:
    """Admin cập nhật permission theo ID."""
    perm_id = args.get("permission_id", "")
    payload = {}
    for field, key in [("name", "name"), ("api_path", "apiPath"), ("method", "method"), ("module", "module")]:
        if args.get(field):
            payload[key] = args[field].upper() if field in ("method", "module") else args[field]
    return await _call_api("PUT", f"{_AUTH_BASE}/permissions/{perm_id}", user_token, json_data=payload)


async def execute_delete_permission(args: dict, user_token: str) -> dict:
    """Admin xóa permission theo ID."""
    perm_id = args.get("permission_id", "")
    return await _call_api("DELETE", f"{_AUTH_BASE}/permissions/{perm_id}", user_token)
