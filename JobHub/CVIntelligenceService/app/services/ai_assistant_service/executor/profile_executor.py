# app/services/ai_assistant_service/executor/profile_executor.py
"""
Executor cho các tools liên quan đến Profile/Resume của ứng viên:
update_my_profile, get_my_resumes, set_default_resume, delete_resume, get_my_applications
"""
import logging
from ..api_client import _call_api

logger = logging.getLogger(__name__)


async def execute_update_my_profile(args: dict, user_token: str) -> dict:
    username_result = None
    if args.get("username") is not None:
        username_payload = {"username": args["username"]}
        logger.info(f"[ProfileExecutor] Updating display name (username): {username_payload}")
        username_result = await _call_api(
            "PUT", "http://authservice:8080/api/v1/auth/username",
            user_token, json_data=username_payload
        )

    # Kiểm tra các trường profile khác
    profile_fields = [
        "fullName", "phone", "address", "summary",
        "yearsOfExperience", "expectedSalary", "gender", "position", "jobSearchStatus"
    ]
    has_profile_fields = any(args.get(f) is not None for f in profile_fields)

    profile_result = {}
    if has_profile_fields:
        payload = {}
        if args.get("fullName") is not None:
            payload["fullName"] = args["fullName"]
        if args.get("phone") is not None:
            payload["phone"] = args["phone"]
        if args.get("address") is not None:
            payload["address"] = args["address"]
        if args.get("summary") is not None:
            payload["summary"] = args["summary"]
        if args.get("yearsOfExperience") is not None:
            payload["yearsOfExperience"] = args["yearsOfExperience"]
        if args.get("expectedSalary") is not None:
            payload["expectedSalary"] = args["expectedSalary"]
        if args.get("gender") is not None:
            g = str(args["gender"]).upper()
            if "FEMALE" in g:
                payload["gender"] = 1
            elif "MALE" in g:
                payload["gender"] = 0
            else:
                payload["gender"] = 2
        if args.get("position") is not None:
            payload["position"] = args["position"]
        if args.get("jobSearchStatus") is not None:
            s = str(args["jobSearchStatus"]).upper()
            if "ACTIVELY_LOOKING" in s or "ACTIVE" in s or "FINDING" in s:
                payload["jobSearchStatus"] = 0
            elif "OPEN" in s or "OFFER" in s:
                payload["jobSearchStatus"] = 1
            else:
                payload["jobSearchStatus"] = 2

        logger.info(f"[ProfileExecutor] Updating profile: {payload}")
        profile_result = await _call_api(
            "PUT", "http://profileservice:8080/api/v1/customers/me",
            user_token, json_data=payload
        )

    # Kết hợp response
    if username_result and has_profile_fields:
        return {
            "statusCode": 200,
            "message": "Cập nhật hồ sơ và tên hiển thị thành công",
            "data": {
                "username_update": username_result,
                "profile_update": profile_result
            }
        }
    elif username_result:
        return username_result
    else:
        return profile_result


async def execute_get_my_resumes(args: dict, user_token: str) -> dict:
    params = {"pageSize": int(args.get("pageSize", 10))}
    return await _call_api("GET", "http://resumeservice:8080/api/v1/resumes", user_token, params=params)


async def execute_set_default_resume(args: dict, user_token: str) -> dict:
    resume_id = args.get("resume_id", "")
    return await _call_api(
        "PATCH", f"http://resumeservice:8080/api/v1/resumes/{resume_id}/set-default", user_token
    )


async def execute_delete_resume(args: dict, user_token: str) -> dict:
    resume_id = args.get("resume_id", "")
    return await _call_api("DELETE", f"http://resumeservice:8080/api/v1/resumes/{resume_id}", user_token)


async def execute_get_my_applications(args: dict, user_token: str) -> dict:
    params = {"pageSize": int(args.get("pageSize", 10))}
    return await _call_api("GET", "http://resumeservice:8080/api/v1/applications", user_token, params=params)
