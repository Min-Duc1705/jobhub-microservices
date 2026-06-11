# app/services/ai_assistant_service/executor/misc_executor.py
"""
Executor cho các tools đa năng và utilities:
navigate_to_page, predict_salary, broadcast_notification, save_job, unsave_job, get_my_saved_jobs
Và hàm _generate_suggestions.
"""
import logging
from ..api_client import _call_api
from .token_utils import _get_role_from_token, _is_path_allowed_for_role

logger = logging.getLogger(__name__)


async def execute_navigate_to_page(args: dict, user_token: str) -> dict:
    page_name = args.get("page_name", "")
    path = args.get("path", "")
    role = _get_role_from_token(user_token)

    allowed = _is_path_allowed_for_role(path, role)
    if not allowed:
        logger.warning(f"[MiscExecutor] Role {role} is not authorized to navigate to path: {path}")
        return {
            "status": "unauthorized",
            "message": "Bạn không có quyền truy cập trang này.",
            "path": path,
            "page_name": page_name
        }

    logger.info(f"[MiscExecutor] Navigating to page {page_name} (path: {path}) for role {role}")
    return {
        "status": "success",
        "message": f"Chuyển hướng đến trang {page_name}...",
        "path": path,
        "page_name": page_name
    }


async def execute_predict_salary(args: dict, user_token: str) -> dict:
    level_raw = args.get("level", "MIDDLE")
    level = "MIDDLE"
    if level_raw:
        level_upper = str(level_raw).upper()
        if "INTERN" in level_upper:
            level = "INTERN"
        elif "JUNIOR" in level_upper:
            level = "JUNIOR"
        elif "SENIOR" in level_upper:
            level = "SENIOR"
        elif "MID" in level_upper:
            level = "MIDDLE"
        elif level_upper in ["INTERN", "JUNIOR", "MIDDLE", "SENIOR"]:
            level = level_upper

    payload = {
        "job_title": args.get("job_title", ""),
        "years_of_experience": int(args.get("experience_years") or args.get("years_of_experience") or 1),
        "skill_set": args.get("skills") or args.get("skill_set") or [],
        "location": args.get("location", "Hà Nội"),
        "level": level
    }
    result = await _call_api(
        "POST", "http://dataanalyticsservice:5007/api/v1/analytics/salary/predict",
        user_token, payload
    )
    return result.get("data", result)


async def execute_broadcast_notification(args: dict, user_token: str) -> dict:
    payload = {
        "title": args.get("title", ""),
        "message": args.get("message", ""),
        "type": args.get("type", "default"),
        "targetGroup": args.get("target_group", "ALL")
    }
    return await _call_api(
        "POST", "http://authservice:8080/api/v1/users/notifications/broadcast",
        user_token, json_data=payload
    )


async def execute_get_my_saved_jobs(args: dict, user_token: str) -> dict:
    params = {"pageSize": int(args.get("pageSize", 10))}
    return await _call_api("GET", "http://jobhub_jobservice:8080/api/v1/saved-jobs", user_token, params)


async def execute_save_job(args: dict, user_token: str) -> dict:
    job_id = args.get("job_id", "")
    params = {}
    if args.get("note"):
        params["note"] = args["note"]
    return await _call_api(
        "POST", f"http://jobhub_jobservice:8080/api/v1/saved-jobs/{job_id}", user_token, params
    )


async def execute_unsave_job(args: dict, user_token: str) -> dict:
    job_id = args.get("job_id", "")
    return await _call_api("DELETE", f"http://jobhub_jobservice:8080/api/v1/saved-jobs/{job_id}", user_token)


def _generate_suggestions(user_role: str, actions_taken: list) -> list[str]:
    """Tạo gợi ý câu hỏi tiếp theo dựa trên context."""
    hr_suggestions = [
        "Xem danh sách ứng viên đã nộp đơn",
        "Dự đoán mức lương phù hợp cho vị trí này",
        "Tìm ứng viên phù hợp với yêu cầu công việc",
        "Xem thống kê tin tuyển dụng của công ty",
        "Tạo chiến dịch AI để tìm ứng viên tự động",
    ]

    if "EMPLOYER" in user_role.upper() or "HR" in user_role.upper():
        return hr_suggestions[:3]

    return [
        "Tìm việc làm phù hợp với kỹ năng của tôi",
        "Xem trạng thái hồ sơ đã nộp",
        "Cập nhật thông tin profile",
    ]


# ── Import tools (Admin) — trigger file upload flow ──────────────────────────

def _import_action(import_type: str, label: str, admin_path: str) -> dict:
    """
    Trả về action trigger để frontend hiển thị file picker và gọi POST /assistant/import.
    Không redirect sang Admin UI nữa — AI xử lý trực tiếp sau khi nhận file.
    """
    return {
        "status":      "import_required",
        "import_type": import_type,
        "label":       label,
        "message": (
            f"Vui lòng chọn file Excel (.xlsx) hoặc CSV (.csv) chứa danh sách {label} "
            f"để AI thực hiện import. File sẽ được gửi đến POST /assistant/import?import_type={import_type}."
        ),
        "upload_endpoint": f"/api/v1/assistant/import?import_type={import_type}",
        "accepted_formats": [".xlsx", ".xls", ".csv"],
        # Fallback nếu user muốn tự import qua Admin UI
        "navigate": {"page_name": f"admin_{import_type}", "path": admin_path},
    }


async def execute_import_users(args: dict, user_token: str) -> dict:
    return _import_action("users", "Users", "/admin/customers")


async def execute_import_skills(args: dict, user_token: str) -> dict:
    return _import_action("skills", "Skills", "/admin/skills")


async def execute_import_companies(args: dict, user_token: str) -> dict:
    return _import_action("companies", "Companies", "/admin/companies")


async def execute_import_jobs(args: dict, user_token: str) -> dict:
    return _import_action("jobs", "Jobs", "/admin/jobs")
