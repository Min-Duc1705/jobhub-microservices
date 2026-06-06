# app/services/ai_assistant_service/executor/candidate_executor.py
"""
Executor cho các tools liên quan đến Candidate/Application:
search_candidates, get_applications_for_job, apply_job, cancel_application, review_application
"""
import logging
from ..api_client import _call_api

logger = logging.getLogger(__name__)


async def execute_search_candidates(args: dict, user_token: str) -> dict:
    params = {"pageSize": int(args.get("pageSize", 10))}
    if args.get("keyword"):
        params["name"] = args["keyword"]
    result = await _call_api("GET", "http://profileservice:8080/api/v1/customers", user_token, params)
    candidates = result.get("data", {}).get("result", [])
    return {"candidates": candidates[:10], "total": result.get("data", {}).get("meta", {}).get("total", 0)}


async def execute_get_applications_for_job(args: dict, user_token: str) -> dict:
    job_id = args.get("job_id", "")
    params = {"jobId": job_id, "pageSize": 20}
    result = await _call_api("GET", "http://resumeservice:8080/api/v1/applications", user_token, params)
    apps = result.get("data", {}).get("result", [])
    return {"applications": apps, "total": result.get("data", {}).get("meta", {}).get("total", 0)}


async def execute_apply_job(args: dict, user_token: str) -> dict:
    payload = {
        "jobId": args.get("job_id", ""),
        "resumeId": args.get("resume_id", ""),
        "coverLetter": args.get("cover_letter")
    }
    return await _call_api("POST", "http://resumeservice:8080/api/v1/applications", user_token, json_data=payload)


async def execute_cancel_application(args: dict, user_token: str) -> dict:
    app_id = args.get("application_id", "")
    return await _call_api("DELETE", f"http://resumeservice:8080/api/v1/applications/{app_id}", user_token)


async def execute_review_application(args: dict, user_token: str) -> dict:
    app_id = args.get("application_id", "")
    status_str = str(args.get("status", "")).upper()

    status_val = 0
    if "REVIEWING" in status_str:
        status_val = 1
    elif "APPROVED" in status_str or "ACCEPT" in status_str or "DUYET" in status_str:
        status_val = 2
    elif "REJECTED" in status_str or "DENY" in status_str or "TU_CHOI" in status_str:
        status_val = 3

    payload = {
        "status": status_val,
        "reviewNote": args.get("review_note")
    }
    return await _call_api(
        "PATCH",
        f"http://resumeservice:8080/api/v1/applications/{app_id}/status",
        user_token,
        json_data=payload
    )
