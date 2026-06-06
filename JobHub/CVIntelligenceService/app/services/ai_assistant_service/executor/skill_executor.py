# app/services/ai_assistant_service/executor/skill_executor.py
"""
Executor cho các tools liên quan đến Skills:
- get_all_skills       — Admin/HR xem danh sách kỹ năng hệ thống
- create_skill         — Admin tạo kỹ năng mới
- update_skill         — Admin cập nhật kỹ năng
- delete_skill         — Admin xóa kỹ năng
- add_my_skill         — HR/Candidate thêm kỹ năng vào hồ sơ cá nhân
- remove_my_skill      — HR/Candidate xóa kỹ năng khỏi hồ sơ cá nhân
"""
import logging
from ..api_client import _call_api

logger = logging.getLogger(__name__)

_SKILL_BASE = "http://profileservice:8080/api/v1/skills"


async def execute_get_all_skills(args: dict, user_token: str) -> dict:
    """Lấy danh sách kỹ năng hệ thống (Admin/HR)."""
    params = {"pageSize": args.get("pageSize", 20)}
    if args.get("keyword"):
        params["searchTerm"] = args["keyword"]

    result = await _call_api("GET", _SKILL_BASE, user_token, params=params)
    skills_raw = result.get("data", {}).get("result", [])
    skills = [
        {
            "id":          s.get("id"),
            "name":        s.get("name"),
            "description": s.get("description"),
        }
        for s in skills_raw
    ]
    total = result.get("data", {}).get("meta", {}).get("total", len(skills))
    return {"skills": skills, "total": total}


async def execute_create_skill(args: dict, user_token: str) -> dict:
    """Admin tạo mới kỹ năng."""
    payload = {"name": args.get("name", "").strip()}
    if args.get("description"):
        payload["description"] = args["description"]

    return await _call_api("POST", _SKILL_BASE, user_token, json_data=payload)


async def execute_update_skill(args: dict, user_token: str) -> dict:
    """Admin cập nhật kỹ năng theo ID."""
    skill_id = args.get("skill_id", "")
    payload = {}
    if args.get("name"):
        payload["name"] = args["name"]
    if args.get("description") is not None:
        payload["description"] = args["description"]

    return await _call_api(
        "PUT", f"{_SKILL_BASE}/{skill_id}",
        user_token, json_data=payload
    )


async def execute_delete_skill(args: dict, user_token: str) -> dict:
    """Admin xóa kỹ năng theo ID."""
    skill_id = args.get("skill_id", "")
    return await _call_api("DELETE", f"{_SKILL_BASE}/{skill_id}", user_token)


async def execute_add_my_skill(args: dict, user_token: str) -> dict:
    """HR/Candidate thêm kỹ năng vào hồ sơ cá nhân."""
    skill_id = args.get("skill_id", "")
    payload = {"skillId": skill_id}
    return await _call_api("POST", f"{_SKILL_BASE}/me", user_token, json_data=payload)


async def execute_remove_my_skill(args: dict, user_token: str) -> dict:
    """HR/Candidate xóa kỹ năng khỏi hồ sơ cá nhân."""
    skill_id = args.get("skill_id", "")
    return await _call_api("DELETE", f"{_SKILL_BASE}/me/{skill_id}", user_token)


async def execute_import_skills_to_my_profile(args: dict, user_token: str) -> dict:
    """HR/Candidate thêm hàng loạt kỹ năng vào hồ sơ cá nhân từ danh sách tên."""
    skill_names = args.get("skill_names", [])
    if not skill_names:
        return {"success": False, "message": "Danh sách kỹ năng trống."}

    # 1. Lấy dropdown toàn bộ skills trong hệ thống để tìm ID
    try:
        dropdown_url = f"{_SKILL_BASE}/dropdown"
        dropdown_res = await _call_api("GET", dropdown_url, user_token)
        all_skills = dropdown_res if isinstance(dropdown_res, list) else dropdown_res.get("data", [])
        if not isinstance(all_skills, list):
            # Thử lấy data từ data field nếu bọc
            all_skills = dropdown_res.get("data", {}).get("result", []) if isinstance(dropdown_res, dict) else []
            if not all_skills and isinstance(dropdown_res, dict):
                all_skills = dropdown_res.get("data", [])
    except Exception as e:
        logger.error(f"Error fetching skills dropdown: {e}")
        return {"success": False, "message": f"Không thể lấy danh sách kỹ năng hệ thống: {str(e)}"}

    # Map name -> id (case-insensitive)
    skill_map = {}
    if isinstance(all_skills, list):
        for s in all_skills:
            name = s.get("name")
            if name:
                skill_map[name.strip().lower()] = s.get("id")

    success_added = []
    already_had = []
    not_found = []
    failed = []

    # 2. Thêm từng skill tuần tự để tránh race conditions trong EF Core DB
    for name in skill_names:
        name_clean = name.strip()
        name_lower = name_clean.lower()
        
        if name_lower not in skill_map:
            not_found.append(name_clean)
            continue
            
        skill_id = skill_map[name_lower]
        
        try:
            payload = {"skillId": skill_id}
            res = await _call_api("POST", f"{_SKILL_BASE}/me", user_token, json_data=payload)
            success_added.append(name_clean)
        except Exception as e:
            err_msg = str(e)
            if "đã có" in err_msg or "Conflict" in err_msg or "BadRequest" in err_msg or "400" in err_msg:
                already_had.append(name_clean)
            else:
                failed.append(f"{name_clean} (Lỗi: {err_msg})")

    # Sinh câu summary phản hồi tự nhiên dễ hiểu
    summary_text = f"Đã hoàn thành việc thêm kỹ năng vào hồ sơ của bạn:\n"
    if success_added:
        summary_text += f"- ✅ Thành công: {', '.join(success_added)}\n"
    if already_had:
        summary_text += f"- ℹ️ Đã có sẵn: {', '.join(already_had)}\n"
    if not_found:
        summary_text += f"- ❌ Không tìm thấy trên hệ thống: {', '.join(not_found)}\n"
    if failed:
        summary_text += f"- ⚠️ Thất bại: {', '.join(failed)}\n"

    return {
        "success": True,
        "message": summary_text,
        "details": {
            "added": success_added,
            "already_present": already_had,
            "not_found_in_system": not_found,
            "failed": failed
        }
    }

