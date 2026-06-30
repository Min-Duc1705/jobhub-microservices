# app/services/ai_assistant_service/executor/job_executor.py
"""
Executor cho các tools liên quan đến Job:
search_jobs, get_job_detail, get_my_jobs, preview_create_job, delete_job
"""
import logging
from ..api_client import _call_api
from .token_utils import _get_customer_id_from_token
from .category_utils import normalize_category
from .level_utils import infer_level_smart

logger = logging.getLogger(__name__)



async def execute_search_jobs(args: dict, user_token: str) -> dict:
    params = {"pageSize": int(args.get("pageSize", 10))}
    if args.get("keyword"):
        params["searchTerm"] = args["keyword"]
    elif args.get("skills") and len(args["skills"]) > 0:
        params["searchTerm"] = args["skills"][0]
    if args.get("level"):
        lvl = args["level"].upper()
        if lvl in ["INTERN", "JUNIOR", "MIDDLE", "SENIOR", "LEAD", "DIRECTOR"]:
            params["Level"] = lvl
    if args.get("location"):
        params["Location"] = args["location"]
    if args.get("salaryMin"):
        params["SalaryMin"] = args["salaryMin"]
    if args.get("salaryMax"):
        params["SalaryMax"] = args["salaryMax"]

    if args.get("skills"):
        skill_ids = []
        for s_name in args["skills"]:
            try:
                skills_resp = await _call_api(
                    "GET",
                    "http://jobhub_jobservice:8080/api/v1/skills",
                    user_token,
                    {"searchTerm": s_name, "pageSize": 5}
                )
                matched_skills = skills_resp.get("data", {}).get("result", [])
                for ms in matched_skills:
                    if ms.get("name", "").strip().lower() == s_name.strip().lower():
                        skill_ids.append(ms["id"])
                        break
                else:
                    if matched_skills:
                        skill_ids.append(matched_skills[0]["id"])
            except Exception as e:
                logger.warning(f"[JobExecutor] Error querying skill '{s_name}': {e}")
        if skill_ids:
            params["SkillIds"] = skill_ids

    result = await _call_api("GET", "http://jobhub_jobservice:8080/api/v1/jobs", user_token, params=params)
    raw_jobs = result.get("data", {}).get("result", [])
    jobs = [
        {
            "id": j.get("id"),
            "name": j.get("name"),
            "companyName": j.get("companyName"),
            "location": j.get("location"),
            "salaryMin": j.get("salaryMin"),
            "salaryMax": j.get("salaryMax"),
            "salaryCurrency": j.get("salaryCurrency", "VND"),
            "status": j.get("status"),
            "description": j.get("description"),
            "requirements": j.get("requirements")
        }
        for j in raw_jobs
    ]
    return {"jobs": jobs, "total": result.get("data", {}).get("meta", {}).get("total", 0)}


async def execute_get_job_detail(args: dict, user_token: str) -> dict:
    job_id = args.get("job_id", "")
    result = await _call_api("GET", f"http://jobhub_jobservice:8080/api/v1/jobs/{job_id}", user_token)
    return {"job": result.get("data", {})}


async def execute_get_my_jobs(args: dict, user_token: str) -> dict:
    customer_id = _get_customer_id_from_token(user_token)
    params = {"pageSize": int(args.get("pageSize", 20))}
    if customer_id:
        params["customerId"] = customer_id
    result = await _call_api("GET", "http://jobhub_jobservice:8080/api/v1/jobs", user_token, params=params)
    raw_jobs = result.get("data", {}).get("result", [])
    jobs = [
        {
            "id": j.get("id"),
            "name": j.get("name"),
            "status": j.get("status"),
            "createdDate": j.get("createdDate"),
            "location": j.get("location"),
            "salaryMin": j.get("salaryMin"),
            "salaryMax": j.get("salaryMax"),
            "salaryCurrency": j.get("salaryCurrency", "VND"),
            "description": j.get("description"),
            "requirements": j.get("requirements")
        }
        for j in raw_jobs
    ]
    return {"jobs": jobs, "total": result.get("data", {}).get("meta", {}).get("total", 0)}


async def execute_preview_create_job(args: dict, user_token: str) -> dict:
    """Trả về preview data mà không tạo job thực sự."""
    exp_req = args.get("experience_required", "")
    job_name = args.get("name", "")
    inferred_lvl = infer_level_smart(job_name, exp_req, current_level=args.get("level"))
    
    salary_min = args.get("salary_min")
    salary_max = args.get("salary_max")
    has_numeric = (salary_min is not None and salary_min > 0) or (salary_max is not None and salary_max > 0)
    if has_numeric:
        is_negotiable = False
    else:
        is_negotiable = bool(args.get("is_salary_negotiable"))
        if salary_min is None and salary_max is None:
            is_negotiable = True

    # Resolve skill names to clean system names for preview
    resolved_names = []
    skill_names = args.get("skill_names", [])
    if skill_names:
        try:
            skills_resp = await _call_api("GET", "http://jobhub_jobservice:8080/api/v1/skills/dropdown", user_token)
            skills_list = skills_resp.get("data") if isinstance(skills_resp, dict) and "data" in skills_resp else skills_resp
            if isinstance(skills_list, list):
                from ..job_confirm_service import resolve_skills
                _, resolved_names = resolve_skills(skill_names, skills_list)
            else:
                resolved_names = skill_names
        except Exception as e:
            logger.warning(f"[JobExecutor] Failed to resolve skills in preview: {e}")
            resolved_names = skill_names
    else:
        resolved_names = []

    return {
        "preview": True,
        "job_data": {
            "name": job_name,
            "description": args.get("description", ""),
            "requirements": args.get("requirements", ""),
            "benefits": args.get("benefits", ""),
            "location": args.get("location", ""),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_currency": args.get("salary_currency", "VND"),
            "is_salary_negotiable": is_negotiable,
            "level": inferred_lvl,
            "quantity": args.get("quantity", 1),
            "deadline": args.get("deadline", ""),
            "skill_names": resolved_names,
            "experience_required": exp_req,
            "category": normalize_category(args.get("category", ""))
        },
        "message": "Preview job - chưa tạo thực sự. Cần xác nhận từ HR."
    }


async def execute_delete_job(args: dict, user_token: str) -> dict:
    """Trả về preview xác nhận xóa, không xóa ngay."""
    return {
        "preview": True,
        "job_data": {
            "job_id": args.get("job_id", ""),
            "job_name": args.get("job_name", "Không rõ tên")
        },
        "message": f"Xác nhận xóa tin tuyển dụng '{args.get('job_name', 'Không rõ tên')}' (ID: {args.get('job_id')})?"
    }


async def execute_update_job(args: dict, user_token: str) -> dict:
    """HR cập nhật thông tin tin tuyển dụng theo ID."""
    job_id = args.get("job_id", "")
    payload = {}
    for field in ["name", "description", "requirements", "benefits", "location",
                  "quantity", "deadline", "experience_required"]:
        if args.get(field) is not None:
            # Map snake_case → camelCase cho API
            key = {
                "experience_required": "experienceRequired",
            }.get(field, field)
            payload[key] = args[field]

    if args.get("salary_min") is not None:
        payload["salaryMin"] = args["salary_min"]
    if args.get("salary_max") is not None:
        payload["salaryMax"] = args["salary_max"]
    if args.get("salary_currency"):
        payload["salaryCurrency"] = args["salary_currency"].upper()
    if args.get("is_salary_negotiable") is not None:
        payload["isSalaryNegotiable"] = args["is_salary_negotiable"]
    if args.get("skill_names"):
        try:
            skills_resp = await _call_api("GET", "http://jobhub_jobservice:8080/api/v1/skills/dropdown", user_token)
            skills_list = skills_resp.get("data") if isinstance(skills_resp, dict) and "data" in skills_resp else skills_resp
            if isinstance(skills_list, list):
                from ..job_confirm_service import resolve_skills
                skill_ids, _ = resolve_skills(args["skill_names"], skills_list)
                payload["skillIds"] = skill_ids
            else:
                logger.warning("[JobExecutor] Failed to fetch skills dropdown list for update_job")
        except Exception as e:
            logger.error(f"[JobExecutor] Failed to resolve skill IDs in update_job: {e}")
    if args.get("category"):
        payload["category"] = normalize_category(args["category"])

    return await _call_api(
        "PUT", f"http://jobhub_jobservice:8080/api/v1/jobs/{job_id}",
        user_token, json_data=payload
    )


async def execute_change_job_status(args: dict, user_token: str) -> dict:
    """HR/Admin đổi trạng thái tin tuyển dụng (DRAFT → PUBLISHED / CLOSED)."""
    job_id = args.get("job_id", "")
    status = args.get("status", "").upper()
    return await _call_api(
        "PATCH", f"http://jobhub_jobservice:8080/api/v1/jobs/{job_id}/status",
        user_token, params={"status": status}
    )
