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
    job_id = args.get("job_id") or args.get("jobId") or ""
    if not job_id:
        return {"error": "Thiếu tham số job_id để lấy danh sách hồ sơ ứng tuyển.", "applications": [], "total": 0}
    params = {"jobId": job_id, "pageSize": 100}
    result = await _call_api("GET", "http://resumeservice:8080/api/v1/applications", user_token, params=params)
    apps = result.get("data", {}).get("result", [])
    
    # Rút gọn extractedText để tránh vượt quá giới hạn token và lỗi cắt chuỗi JSON (MALFORMED_FUNCTION_CALL)
    cleaned_apps = []
    for app in apps:
        app_copy = app.copy()
        if "resume" in app_copy and app_copy["resume"]:
            resume_copy = app_copy["resume"].copy()
            if "extractedText" in resume_copy and resume_copy["extractedText"]:
                resume_copy["extractedText"] = resume_copy["extractedText"][:500] + "..."
            app_copy["resume"] = resume_copy
        cleaned_apps.append(app_copy)
        
    return {"applications": cleaned_apps, "total": result.get("data", {}).get("meta", {}).get("total", 0)}


async def execute_apply_job(args: dict, user_token: str) -> dict:
    job_id = args.get("job_id") or args.get("jobId") or ""
    resume_id = args.get("resume_id") or args.get("resumeId") or ""
    payload = {
        "jobId": job_id,
        "resumeId": resume_id,
        "coverLetter": args.get("cover_letter")
    }
    return await _call_api("POST", "http://resumeservice:8080/api/v1/applications", user_token, json_data=payload)


async def execute_cancel_application(args: dict, user_token: str) -> dict:
    app_id = args.get("application_id") or args.get("applicationId") or ""
    return await _call_api("DELETE", f"http://resumeservice:8080/api/v1/applications/{app_id}", user_token)


async def execute_review_application(args: dict, user_token: str) -> dict:
    app_id = args.get("application_id") or args.get("applicationId") or ""
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
    job_id = args.get("job_id") or args.get("jobId") or ""
    if not job_id:
        return {"error": "Thiếu tham số job_id để thực hiện chấm điểm ứng viên."}
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


async def execute_get_candidate_evaluation_detail(args: dict, user_token: str) -> dict:
    app_id = args.get("application_id")
    candidate_name = args.get("candidate_name", "").strip().lower()

    if not app_id and not candidate_name:
        return {"error": "Vui lòng cung cấp tên ứng viên hoặc Application ID."}

    # 1. Tìm application
    target_app = None
    if app_id:
        app_resp = await _call_api("GET", f"http://resumeservice:8080/api/v1/applications/{app_id}", user_token)
        target_app = app_resp.get("data")
    else:
        apps_resp = await _call_api("GET", "http://resumeservice:8080/api/v1/applications", user_token, params={"pageSize": 200})
        apps = apps_resp.get("data", {}).get("result", [])
        
        for app in apps:
            resume = app.get("resume") or {}
            title = (resume.get("title") or "").lower()
            fullname = ""
            content_json = resume.get("contentJson") or resume.get("content_json")
            if content_json:
                import json
                try:
                    if isinstance(content_json, str):
                        content = json.loads(content_json)
                    else:
                        content = content_json
                    fullname = content.get("personal", {}).get("fullName", "")
                except Exception:
                    pass
            
            if candidate_name in title or (fullname and candidate_name in fullname.lower()):
                target_app = app
                break

    if not target_app:
        return {"error": f"Không tìm thấy hồ sơ ứng tuyển của ứng viên '{args.get('candidate_name') or app_id}'."}

    app_id = target_app.get("id")
    job_id = target_app.get("jobId") or target_app.get("job_id")
    customer_id = target_app.get("customerId") or target_app.get("customer_id")
    resume = target_app.get("resume") or {}

    # 2. Kiểm tra xem MongoDB đã có phân tích chi tiết chưa
    from app.core.database import get_resume_analysis_col
    col = get_resume_analysis_col()
    existing = await col.find_one({"application_id": app_id})
    
    if existing and existing.get("ai_feedback"):
        return {
            "application_id": app_id,
            "matching_score": existing.get("matching_score"),
            "extracted_skills": existing.get("extracted_skills", []),
            "strengths": existing.get("strengths", []),
            "weaknesses": existing.get("weaknesses", []),
            "ai_feedback": existing.get("ai_feedback"),
            "candidate_name": resume.get("title") or "Ứng viên"
        }

    # 3. Nếu chưa có feedback chi tiết, ta chạy chấm điểm đơn lẻ để sinh feedback và lưu vào DB
    job_resp = await _call_api("GET", f"http://jobhub_jobservice:8080/api/v1/jobs/{job_id}", user_token)
    job_data = job_resp.get("data", {})
    if not job_data:
        return {"error": f"Không tìm thấy thông tin tin tuyển dụng ID '{job_id}'"}

    desc = job_data.get("description", "")
    reqs = job_data.get("requirements", "")
    job_desc = f"{desc}\n{reqs}".strip()

    def _extract_cv_text(res_obj: dict) -> str:
        if not res_obj:
            return ""
        txt = res_obj.get("extractedText") or res_obj.get("extracted_text")
        if txt:
            return txt
        content_json = res_obj.get("contentJson") or res_obj.get("content_json")
        if content_json:
            import json
            if isinstance(content_json, str):
                try:
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
        return res_obj.get("title", "")

    cv_text = _extract_cv_text(resume)

    from app.services.cv_service import score_single_cv
    from app.schemas.cv_scoring import CvScoringRequest as CvScoringReq
    
    scoring_req = CvScoringReq(
        job_description=job_desc,
        cv_text=cv_text,
        application_id=app_id,
        job_id=job_id,
        customer_id=customer_id,
        generate_feedback=True
    )
    
    try:
        res = await score_single_cv(scoring_req)
        res_dict = res.model_dump()
        res_dict["candidate_name"] = resume.get("title") or "Ứng viên"
        return res_dict
    except Exception as e:
        logger.error(f"[CandidateExecutor] Error in execute_get_candidate_evaluation_detail: {e}")
        return {"error": f"Lỗi khi phân tích chi tiết ứng viên bằng AI: {str(e)}"}
