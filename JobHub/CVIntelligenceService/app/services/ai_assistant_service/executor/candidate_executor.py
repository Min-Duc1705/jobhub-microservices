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
    result = await _call_api("GET", "http://profileservice:8080/api/v1/customers", user_token, params=params)
    candidates = result.get("data", {}).get("result", [])
    return {"candidates": candidates[:10], "total": result.get("data", {}).get("meta", {}).get("total", 0)}


async def execute_get_applications_for_job(args: dict, user_token: str) -> dict:
    job_id = args.get("job_id", "")
    params = {"jobId": job_id, "pageSize": 20}
    result = await _call_api("GET", "http://resumeservice:8080/api/v1/applications", user_token, params=params)
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


async def execute_score_candidates_for_job(args: dict, user_token: str) -> dict:
    job_id = args.get("job_id", "")
    top_n = int(args.get("top_n", 10))

    # 1. Fetch Job Description
    job_resp = await _call_api("GET", f"http://jobhub_jobservice:8080/api/v1/jobs/{job_id}", user_token)
    job_data = job_resp.get("data", {})
    if not job_data:
        return {"error": f"Không tìm thấy thông tin tin tuyển dụng ID '{job_id}'"}

    desc = job_data.get("description", "")
    reqs = job_data.get("requirements", "")
    job_desc = f"{desc}\n{reqs}".strip()

    # 2. Fetch Applications for Job
    apps_resp = await _call_api("GET", "http://resumeservice:8080/api/v1/applications", user_token, params={"jobId": job_id, "pageSize": 100})
    apps = apps_resp.get("data", {}).get("result", [])
    if not apps:
        return {"message": "Không có ứng viên nào ứng tuyển vào vị trí này để chấm điểm.", "results": []}

    # 3. Helper to extract text
    def _extract_cv_text(resume: dict) -> str:
        if not resume:
            return ""
        
        # Try extractedText
        txt = resume.get("extractedText") or resume.get("extracted_text")
        if txt:
            return txt

        # Try contentJson
        content_json = resume.get("contentJson") or resume.get("content_json")
        if content_json:
            if isinstance(content_json, str):
                try:
                    import json
                    content = json.loads(content_json)
                except Exception:
                    content = {}
            else:
                content = content_json
            
            if content:
                parts = []
                personal = content.get("personal", {})
                parts.append(personal.get("fullName", ""))
                parts.append(personal.get("title", ""))
                parts.append(personal.get("summary", ""))
                
                for skill in content.get("skills", []):
                    parts.append(skill.get("category", ""))
                    parts.extend(skill.get("items", []))
                    
                for exp in content.get("experiences", []):
                    parts.append(exp.get("position", ""))
                    parts.append(exp.get("company", ""))
                    parts.append(exp.get("description", ""))
                    parts.extend(exp.get("bullets", []))
                    parts.extend(exp.get("tags", []))
                    
                for proj in content.get("projects", []):
                    parts.append(proj.get("name", ""))
                    parts.append(proj.get("description", ""))
                    parts.extend(proj.get("tags", []))
                    
                for edu in content.get("education", []):
                    parts.append(edu.get("school", ""))
                    parts.append(edu.get("degree", ""))
                    
                for cert in content.get("certifications", []):
                    parts.append(cert.get("name", ""))
                    parts.append(cert.get("issuer", ""))
                    
                return "\n".join([p for p in parts if p])
        
        return resume.get("title", "")

    # 4. Build cv_list
    cv_list = []
    for app in apps:
        resume = app.get("resume") or {}
        cv_text = _extract_cv_text(resume)
        cv_list.append({
            "application_id": app.get("id"),
            "job_id": job_id,
            "customer_id": app.get("customerId") or app.get("customer_id"),
            "cv_text": cv_text
        })

    # 5. Call cv_service.batch_score
    from app.services.cv_service import batch_score
    from app.schemas.cv_scoring import SkillScoringRequest

    scoring_req = SkillScoringRequest(
        job_description=job_desc,
        cv_list=cv_list
    )

    try:
        score_res = await batch_score(scoring_req, top_n=top_n)
        return score_res.model_dump()
    except Exception as e:
        logger.error(f"[CandidateExecutor] Error running batch_score: {e}")
        return {"error": f"Lỗi khi chạy thuật toán chấm điểm AI: {str(e)}"}
