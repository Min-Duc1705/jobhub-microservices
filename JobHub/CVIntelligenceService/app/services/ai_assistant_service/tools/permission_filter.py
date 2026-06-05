# app/services/ai_assistant_service/tools/permission_filter.py
"""
Lọc tools theo permissions thực tế của user (fetch từ AuthService DB qua Redis cache).
"""
import re
from .definitions import _ALL_TOOL_DEFS


def normalize_path(path: str) -> str:
    """Chuẩn hóa path parameters dạng {id}, {job_id}, {jobId}... về {id}."""
    path = path.strip().lower()
    path = re.sub(r'\{[^}]+\}', '{id}', path)
    return path


def _filter_tools_by_permission(user_permissions: list[dict], user_role: str = "USER") -> list[dict]:
    """
    Lọc danh sách tools dựa trên permissions thực tế của role user (từ AuthService DB).

    - ADMIN: luôn có toàn bộ tools.
    - Các role khác: tool được cấp phép nếu user có ít nhất 1 permission khớp với permissions_required.
    - Tool không yêu cầu permission (public): luôn được cấp phép.

    user_permissions: danh sách {"method": "GET", "apiPath": "/api/v1/jobs"} từ AuthService.
    """
    role_upper = (user_role or "USER").upper()
    if role_upper == "ADMIN":
        return _ALL_TOOL_DEFS

    # Build set các permission user có — normalize path để so sánh
    user_perm_set: set[str] = set()
    for p in user_permissions:
        method = (p.get("method") or "").upper()
        api_path = normalize_path(p.get("apiPath") or "")
        if method and api_path:
            user_perm_set.add(f"{method}:{api_path}")

    available = []
    for tool_def in _ALL_TOOL_DEFS:
        req_perms = tool_def.get("permissions_required", [])
        if not req_perms:
            # Tool public — luôn hiển thị
            available.append(tool_def)
            continue
        # Kiểm tra user có ít nhất 1 permission khớp
        for method, path in req_perms:
            norm = f"{method.upper()}:{normalize_path(path)}"
            if norm in user_perm_set:
                available.append(tool_def)
                break

    return available
