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
