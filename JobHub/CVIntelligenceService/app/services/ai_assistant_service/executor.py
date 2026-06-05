import logging
import base64
import json
from .api_client import _call_api

logger = logging.getLogger(__name__)

def _get_customer_id_from_token(token: str) -> str:
    try:
        parts = token.split(".")
        if len(parts) == 3:
            payload_b64 = parts[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding
            payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8", errors="ignore"))
            sub = (payload.get("sub") or 
                   payload.get("id") or 
                   payload.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier") or 
                   "")
            logger.info(f"[AIAssistant] Parsed customerId from token: {sub}")
            return sub
    except Exception as e:
        logger.error(f"[AIAssistant] Error parsing customerId from token: {e}")
    return ""

def _get_role_from_token(token: str) -> str:
    try:
        parts = token.split(".")
        if len(parts) == 3:
            payload_b64 = parts[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding
            payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8", errors="ignore"))
            role = (payload.get("http://schemas.microsoft.com/ws/2008/06/identity/claims/role") or
                    payload.get("role") or
                    "USER")
            return role.upper()
    except Exception as e:
        logger.error(f"[AIAssistant] Error parsing role from token: {e}")
    return "USER"

def _is_path_allowed_for_role(path: str, role: str) -> bool:
    role = (role or "USER").upper()
    if role == "ADMIN":
        return True
        
    path_lower = path.lower()
    
    # 1. Admin paths
    if path_lower.startswith("/admin"):
        return role != "CANDIDATE" and role != "USER"
        
    # 2. HR paths
    if path_lower.startswith("/hr"):
        return role == "HR"
        
    # 3. Candidate restricted paths
    if "/applied-jobs" in path_lower or "/saved-jobs" in path_lower:
        return role == "CANDIDATE"
        
    # 4. Profile & Resume Builder
    if path_lower.startswith("/candidate/"):
        return True
        
    # 5. Public paths
    return True

_VALID_CATEGORIES = [
    "Software Development",
    "Frontend Development",
    "Backend Development",
    "Fullstack Development",
    "Mobile Development",
    "DevOps & Cloud",
    "Data Engineering",
    "Data Science & AI",
    "Cybersecurity",
    "QA & Testing",
    "UI/UX Design",
    "Product Management",
    "Business Analysis",
    "ERP & Enterprise Systems",
    "Network & Sysadmin",
    "IT Support",
    "Game Development",
    "Blockchain & Web3",
    "Embedded & IoT",
    "Engineering",
    "Marketing",
    "Sales",
    "Other"
]

_CATEGORY_MAPPING = {
    "lập trình": "Software Development",
    "phần mềm": "Software Development",
    "software": "Software Development",
    "frontend": "Frontend Development",
    "giao diện": "Frontend Development",
    "backend": "Backend Development",
    "fullstack": "Fullstack Development",
    "mobile": "Mobile Development",
    "android": "Mobile Development",
    "ios": "Mobile Development",
    "devops": "DevOps & Cloud",
    "cloud": "DevOps & Cloud",
    "data engineer": "Data Engineering",
    "dữ liệu": "Data Engineering",
    "data science": "Data Science & AI",
    "trí tuệ nhân tạo": "Data Science & AI",
    "ai": "Data Science & AI",
    "machine learning": "Data Science & AI",
    "an ninh mạng": "Cybersecurity",
    "cybersecurity": "Cybersecurity",
    "bảo mật": "Cybersecurity",
    "qa": "QA & Testing",
    "qc": "QA & Testing",
    "testing": "QA & Testing",
    "kiểm thử": "QA & Testing",
    "ui/ux": "UI/UX Design",
    "design": "UI/UX Design",
    "thiết kế": "UI/UX Design",
    "product manager": "Product Management",
    "quản trị sản phẩm": "Product Management",
    "ba": "Business Analysis",
    "business analyst": "Business Analysis",
    "erp": "ERP & Enterprise Systems",
    "sap": "ERP & Enterprise Systems",
    "network": "Network & Sysadmin",
    "hệ thống": "Network & Sysadmin",
    "system admin": "Network & Sysadmin",
    "support": "IT Support",
    "helpdesk": "IT Support",
    "game": "Game Development",
    "web3": "Blockchain & Web3",
    "blockchain": "Blockchain & Web3",
    "embedded": "Embedded & IoT",
    "iot": "Embedded & IoT",
    "nhúng": "Embedded & IoT",
    "kỹ thuật": "Engineering",
    "công nghệ": "Engineering",
    "marketing": "Marketing",
    "tiếp thị": "Marketing",
    "sales": "Sales",
    "kinh doanh": "Sales",
    "bán hàng": "Sales"
}

def normalize_category(category_input: str) -> str:
    """Chuẩn hóa category nhập vào về một trong các giá trị của _VALID_CATEGORIES."""
    if not category_input:
        return "Other"
        
    val = category_input.strip()
    # Nếu đã khớp chính xác
    if val in _VALID_CATEGORIES:
        return val
        
    val_lower = val.lower()
    # So khớp chính xác lowercase
    for cat in _VALID_CATEGORIES:
        if val_lower == cat.lower():
            return cat
            
    # Tìm kiếm theo từ khóa mapping
    for kw, target in _CATEGORY_MAPPING.items():
        if kw in val_lower:
            return target
            
    return "Other"

async def _execute_tool(tool_name: str, args: dict, user_token: str) -> dict:
    """Thực thi một tool cụ thể với token của user."""
    try:
        if tool_name == "search_jobs":
            params = {"pageSize": args.get("pageSize", 10)}
            if args.get("keyword"):
                params["searchTerm"] = args["keyword"]
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
                        print(f"Error querying skill '{s_name}': {e}")
                if skill_ids:
                    params["SkillIds"] = skill_ids

            result = await _call_api("GET", "http://jobhub_jobservice:8080/api/v1/jobs", user_token, params)
            raw_jobs = result.get("data", {}).get("result", [])
            jobs = []
            for j in raw_jobs:
                jobs.append({
                    "id": j.get("id"),
                    "name": j.get("name"),
                    "companyName": j.get("companyName"),
                    "location": j.get("location"),
                    "salaryMin": j.get("salaryMin"),
                    "salaryMax": j.get("salaryMax"),
                    "salaryCurrency": j.get("salaryCurrency", "VND"),
                    "status": j.get("status")
                })
            return {"jobs": jobs, "total": result.get("data", {}).get("meta", {}).get("total", 0)}

        elif tool_name == "get_job_detail":
            job_id = args.get("job_id", "")
            result = await _call_api("GET", f"http://jobhub_jobservice:8080/api/v1/jobs/{job_id}", user_token)
            return {"job": result.get("data", {})}

        elif tool_name == "get_my_jobs":
            customer_id = _get_customer_id_from_token(user_token)
            params = {"pageSize": args.get("pageSize", 20)}
            if customer_id:
                params["customerId"] = customer_id
            result = await _call_api("GET", "http://jobhub_jobservice:8080/api/v1/jobs", user_token, params)
            raw_jobs = result.get("data", {}).get("result", [])
            jobs = []
            for j in raw_jobs:
                jobs.append({
                    "id": j.get("id"),
                    "name": j.get("name"),
                    "status": j.get("status"),
                    "createdDate": j.get("createdDate"),
                    "location": j.get("location"),
                    "salaryMin": j.get("salaryMin"),
                    "salaryMax": j.get("salaryMax"),
                    "salaryCurrency": j.get("salaryCurrency", "VND")
                })
            return {"jobs": jobs, "total": result.get("data", {}).get("meta", {}).get("total", 0)}

        elif tool_name == "preview_create_job":
            # Return the preview data without actually creating
            return {
                "preview": True,
                "job_data": {
                    "name": args.get("name", ""),
                    "description": args.get("description", ""),
                    "requirements": args.get("requirements", ""),
                    "benefits": args.get("benefits", ""),
                    "location": args.get("location", ""),
                    "salary_min": args.get("salary_min"),
                    "salary_max": args.get("salary_max"),
                    "salary_currency": args.get("salary_currency", "VND"),
                    "quantity": args.get("quantity", 1),
                    "deadline": args.get("deadline", ""),
                    "skill_names": args.get("skill_names", []),
                    "experience_required": args.get("experience_required", ""),
                    "category": normalize_category(args.get("category", ""))
                },
                "message": "Preview job - chưa tạo thực sự. Cần xác nhận từ HR."
            }
        elif tool_name == "delete_job":
            return {
                "preview": True,
                "job_data": {
                    "job_id": args.get("job_id", ""),
                    "job_name": args.get("job_name", "Không rõ tên")
                },
                "message": f"Xác nhận xóa tin tuyển dụng '{args.get('job_name', 'Không rõ tên')}' (ID: {args.get('job_id')})?"
            }

        elif tool_name == "search_candidates":
            params = {"pageSize": args.get("pageSize", 10)}
            if args.get("keyword"):
                params["name"] = args["keyword"]
            result = await _call_api("GET", "http://profileservice:8080/api/v1/customers", user_token, params)
            candidates = result.get("data", {}).get("result", [])
            return {"candidates": candidates[:10], "total": result.get("data", {}).get("meta", {}).get("total", 0)}

        elif tool_name == "get_applications_for_job":
            job_id = args.get("job_id", "")
            params = {"jobId": job_id, "pageSize": 20}
            result = await _call_api("GET", "http://resumeservice:8080/api/v1/applications", user_token, params)
            apps = result.get("data", {}).get("result", [])
            return {"applications": apps, "total": result.get("data", {}).get("meta", {}).get("total", 0)}

        elif tool_name == "predict_salary":
            payload = {
                "jobTitle": args.get("job_title", ""),
                "experienceYears": args.get("experience_years", 1),
                "skills": args.get("skills", []),
                "location": args.get("location", "Hà Nội")
            }
            result = await _call_api("POST", "http://dataanalyticsservice:5007/api/v1/analytics/salary/predict", user_token, payload)
            return result.get("data", result)

        elif tool_name == "get_my_company_info":
            # 1. Fetch user profile to get companyId
            company_id = ""
            try:
                prof_result = await _call_api("GET", "http://profileservice:8080/api/v1/customers/me", user_token)
                prof_data = prof_result.get("data") if isinstance(prof_result, dict) and "data" in prof_result else prof_result
                if isinstance(prof_data, dict):
                    company_id = prof_data.get("companyId", "")
            except Exception as e:
                logger.error(f"[AIAssistant] get_my_company_info failed to get profile: {e}")
                
            if company_id:
                # 2. Fetch company details
                result = await _call_api("GET", f"http://companyservice:8080/api/v1/companies/{company_id}", user_token)
                company_data = result.get("data") if isinstance(result, dict) and "data" in result else result
                return {"company": company_data}
            
            # If no companyId, return None
            return {"company": None, "message": "Tài khoản của bạn chưa được liên kết với công ty nào."}

        elif tool_name == "search_companies":
            keyword = args.get("keyword", "")
            params = {"pageSize": args.get("pageSize", 10)}
            if keyword:
                params["searchTerm"] = keyword
            result = await _call_api("GET", "http://companyservice:8080/api/v1/companies", user_token, params)
            companies_raw = result.get("data", {}).get("result", [])
            companies = []
            for c in companies_raw:
                companies.append({
                    "id": c.get("id"),
                    "name": c.get("name"),
                    "industry": c.get("industry"),
                    "address": c.get("address"),
                    "size": c.get("size"),
                    "website": c.get("website")
                })
            return {"companies": companies, "total": result.get("data", {}).get("meta", {}).get("total", len(companies))}

        elif tool_name == "navigate_to_page":
            page_name = args.get("page_name", "")
            path = args.get("path", "")
            role = _get_role_from_token(user_token)
            
            allowed = _is_path_allowed_for_role(path, role)
            if not allowed:
                logger.warning(f"[AIAssistant] Role {role} is not authorized to navigate to path: {path}")
                return {
                    "status": "unauthorized",
                    "message": "Bạn không có quyền truy cập trang này.",
                    "path": path,
                    "page_name": page_name
                }
            
            logger.info(f"[AIAssistant] Navigating to page {page_name} (path: {path}) for role {role}")
            return {
                "status": "success",
                "message": f"Chuyển hướng đến trang {page_name}...",
                "path": path,
                "page_name": page_name
            }
        elif tool_name == "update_my_profile":
            username_result = None
            if args.get("username") is not None:
                username_payload = {"username": args["username"]}
                logger.info(f"[AIAssistant] Updating display name (username) with: {username_payload}")
                username_result = await _call_api("PUT", "http://authservice:8080/api/v1/auth/username", user_token, json_data=username_payload)
            
            # Check if there are other profile fields to update
            profile_fields = ["fullName", "phone", "address", "summary", "yearsOfExperience", "expectedSalary", "gender", "position", "jobSearchStatus"]
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
                
                logger.info(f"[AIAssistant] Updating profile with: {payload}")
                profile_result = await _call_api("PUT", "http://profileservice:8080/api/v1/customers/me", user_token, json_data=payload)
            
            # Combine responses
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

        elif tool_name == "get_my_saved_jobs":
            params = {"pageSize": args.get("pageSize", 10)}
            result = await _call_api("GET", "http://jobhub_jobservice:8080/api/v1/saved-jobs", user_token, params)
            return result

        elif tool_name == "save_job":
            job_id = args.get("job_id", "")
            params = {}
            if args.get("note"):
                params["note"] = args["note"]
            result = await _call_api("POST", f"http://jobhub_jobservice:8080/api/v1/saved-jobs/{job_id}", user_token, params)
            return result

        elif tool_name == "unsave_job":
            job_id = args.get("job_id", "")
            result = await _call_api("DELETE", f"http://jobhub_jobservice:8080/api/v1/saved-jobs/{job_id}", user_token)
            return result

        elif tool_name == "get_my_resumes":
            params = {"pageSize": args.get("pageSize", 10)}
            result = await _call_api("GET", "http://resumeservice:8080/api/v1/resumes", user_token, params)
            return result

        elif tool_name == "set_default_resume":
            resume_id = args.get("resume_id", "")
            result = await _call_api("PATCH", f"http://resumeservice:8080/api/v1/resumes/{resume_id}/set-default", user_token)
            return result

        elif tool_name == "delete_resume":
            resume_id = args.get("resume_id", "")
            result = await _call_api("DELETE", f"http://resumeservice:8080/api/v1/resumes/{resume_id}", user_token)
            return result

        elif tool_name == "get_my_applications":
            params = {"pageSize": args.get("pageSize", 10)}
            result = await _call_api("GET", "http://resumeservice:8080/api/v1/applications", user_token, params)
            return result

        elif tool_name == "apply_job":
            payload = {
                "jobId": args.get("job_id", ""),
                "resumeId": args.get("resume_id", ""),
                "coverLetter": args.get("cover_letter")
            }
            result = await _call_api("POST", "http://resumeservice:8080/api/v1/applications", user_token, json_data=payload)
            return result

        elif tool_name == "cancel_application":
            app_id = args.get("application_id", "")
            result = await _call_api("DELETE", f"http://resumeservice:8080/api/v1/applications/{app_id}", user_token)
            return result

        elif tool_name == "review_application":
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
            result = await _call_api("PATCH", f"http://resumeservice:8080/api/v1/applications/{app_id}/status", user_token, json_data=payload)
            return result

        elif tool_name == "update_company_info":
            comp_id = args.get("company_id", "")
            payload = {}
            if args.get("name") is not None:
                payload["name"] = args["name"]
            if args.get("description") is not None:
                payload["description"] = args["description"]
            if args.get("address") is not None:
                payload["address"] = args["address"]
            if args.get("industry") is not None:
                payload["industry"] = args["industry"]
            if args.get("website") is not None:
                payload["website"] = args["website"]
            if args.get("contactEmail") is not None:
                payload["contactEmail"] = args["contactEmail"]
            if args.get("taxCode") is not None:
                payload["taxCode"] = args["taxCode"]
            if args.get("companySize") is not None:
                sz = str(args["companySize"]).upper()
                if "STARTUP" in sz:
                    payload["companySize"] = 0
                elif "ENTERPRISE" in sz:
                    payload["companySize"] = 2
                else:
                    payload["companySize"] = 1 # SME default
            
            result = await _call_api("PUT", f"http://companyservice:8080/api/v1/companies/{comp_id}", user_token, json_data=payload)
            return result

        elif tool_name == "get_my_hire_agent_campaigns":
            result = await _call_api("GET", "http://notificationservice:8080/api/v1/hire-agent/campaigns", user_token)
            return result

        elif tool_name == "create_hire_agent_campaign":
            payload = {
                "jobId": args.get("job_id", ""),
                "jobName": args.get("job_name", ""),
                "jobDescription": args.get("job_description", ""),
                "targetCount": args.get("target_count", 5),
                "jobLocation": args.get("job_location"),
                "jobType": args.get("job_type")
            }
            result = await _call_api("POST", "http://notificationservice:8080/api/v1/hire-agent/campaigns", user_token, json_data=payload)
            return result

        elif tool_name == "schedule_campaign_interview":
            camp_id = args.get("campaign_id", "")
            payload = {
                "interviewDate": args.get("interview_date", "")
            }
            result = await _call_api("POST", f"http://notificationservice:8080/api/v1/hire-agent/campaigns/{camp_id}/schedule", user_token, json_data=payload)
            return result

        elif tool_name == "broadcast_notification":
            payload = {
                "title": args.get("title", ""),
                "message": args.get("message", ""),
                "type": args.get("type", "default"),
                "targetGroup": args.get("target_group", "ALL")
            }
            result = await _call_api("POST", "http://authservice:8080/api/v1/users/notifications/broadcast", user_token, json_data=payload)
            return result

        else:
            return {"error": f"Tool '{tool_name}' chưa được triển khai"}

    except Exception as e:
        logger.error(f"[AIAssistant] Tool '{tool_name}' failed: {e}")
        return {"error": str(e)}

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
