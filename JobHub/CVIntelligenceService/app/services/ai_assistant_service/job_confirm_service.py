# app/services/ai_assistant_service/job_confirm_service.py
"""
Xử lý xác nhận tạo/xóa Job và trích xuất thông tin Job từ ảnh.
"""
import json
import logging
import base64

import google.generativeai as genai
from app.ml.llm_generator import _load_api_keys
from .api_client import _call_api
from .executor.category_utils import normalize_category
from .executor.level_utils import infer_level_smart

logger = logging.getLogger(__name__)


async def confirm_create_job(
    job_data: dict,
    user_token: str,
    company_id: str,
) -> dict:
    """Thực sự tạo job sau khi HR đã xác nhận preview."""
    try:
        # Tự động lấy companyId từ ProfileService nếu không có
        if not company_id:
            try:
                prof_result = await _call_api("GET", "http://profileservice:8080/api/v1/customers/me", user_token)
                prof_data = prof_result.get("data") if isinstance(prof_result, dict) and "data" in prof_result else prof_result
                if isinstance(prof_data, dict):
                    company_id = prof_data.get("companyId", "")
                    logger.info(f"[JobConfirm] Retrieved companyId from ProfileService: {company_id}")
            except Exception as e:
                logger.error(f"[JobConfirm] Failed to get companyId from profile: {e}")

        # Lấy chi tiết công ty (companyName, companyLogo) từ CompanyService theo companyId
        company_name = None
        company_logo = None
        if company_id:
            try:
                comp_result = await _call_api("GET", f"http://companyservice:8080/api/v1/companies/{company_id}", user_token)
                comp_data = comp_result.get("data") if isinstance(comp_result, dict) and "data" in comp_result else comp_result
                if isinstance(comp_data, dict):
                    company_name = comp_data.get("name")
                    company_logo = comp_data.get("logo")
                    logger.info(f"[JobConfirm] Resolved company: {company_name} (ID: {company_id})")
            except Exception as e:
                logger.error(f"[JobConfirm] Failed to resolve company info for {company_id}: {e}")

        # Fallback nếu không có company_id (admin test)
        if not company_id:
            try:
                comp_result = await _call_api("GET", "http://companyservice:8080/api/v1/companies", user_token)
                companies = comp_result.get("data", {}).get("result", [])
                if companies:
                    matched_company = companies[0]
                    company_id = matched_company.get("id", "")
                    company_name = matched_company.get("name")
                    company_logo = matched_company.get("logo")
                    logger.warning(f"[JobConfirm] Fallback resolve company: {company_name} (ID: {company_id})")
            except Exception as e:
                logger.error(f"[JobConfirm] Fallback company resolve failed: {e}")

        # Resolve skill names to skillIds
        skill_ids = []
        skill_names = job_data.get("skill_names", [])
        if skill_names:
            try:
                skills_resp = await _call_api("GET", "http://jobhub_jobservice:8080/api/v1/skills/dropdown", user_token)
                skills_list = skills_resp.get("data") if isinstance(skills_resp, dict) and "data" in skills_resp else skills_resp
                if not isinstance(skills_list, list):
                    skills_list = []

                skill_map = {s.get("name", "").lower().strip(): s.get("id") for s in skills_list if s.get("name") and s.get("id")}

                for name in skill_names:
                    name_lower = name.lower().strip()
                    if name_lower in skill_map:
                        skill_ids.append(skill_map[name_lower])
                    else:
                        for k, v in skill_map.items():
                            if name_lower in k or k in name_lower:
                                skill_ids.append(v)
                                break
                        else:
                            logger.warning(f"[JobConfirm] Skill not found in dropdown: {name}")
            except Exception as e:
                logger.error(f"[JobConfirm] Failed to resolve skill IDs: {e}")

        # Format EndDate (deadline)
        deadline = job_data.get("deadline")
        end_date = None
        if deadline:
            try:
                end_date = f"{deadline}T23:59:59Z"
            except Exception:
                end_date = None

        # Build API payload
        exp_req = job_data.get("experience_required")
        job_name = job_data.get("name", "")
        inferred_lvl = infer_level_smart(job_name, exp_req, current_level=job_data.get("level"))
        
        salary_min = job_data.get("salary_min")
        salary_max = job_data.get("salary_max")
        has_numeric = (salary_min is not None and salary_min > 0) or (salary_max is not None and salary_max > 0)
        if has_numeric:
            is_negotiable = False
        else:
            is_negotiable = bool(job_data.get("is_salary_negotiable"))
            if salary_min is None and salary_max is None:
                is_negotiable = True

        payload = {
            "name": job_name,
            "description": job_data.get("description", ""),
            "requirements": job_data.get("requirements", ""),
            "benefits": job_data.get("benefits", ""),
            "location": job_data.get("location", "Hà Nội"),
            "salaryMin": salary_min,
            "salaryMax": salary_max,
            "salaryCurrency": job_data.get("salary_currency", "VND"),
            "isSalaryNegotiable": is_negotiable,
            "level": str(inferred_lvl).upper(),
            "quantity": job_data.get("quantity", 1),
            "startDate": None,
            "endDate": end_date,
            "experienceRequired": exp_req,
            "category": normalize_category(job_data.get("category")),
            "skillIds": skill_ids,
            "companyId": company_id,
            "companyName": company_name,
            "companyLogo": company_logo
        }

        result = await _call_api("POST", "http://jobhub_jobservice:8080/api/v1/jobs", user_token, payload)

        if "error" in result and result["error"] is not None:
            return {"success": False, "message": result["error"]}

        job = result.get("data", result)
        return {
            "success": True,
            "message": f"Đã tạo thành công tin tuyển dụng '{job_data.get('name')}'",
            "job": job
        }
    except Exception as e:
        logger.error(f"[JobConfirm] confirm_create_job failed: {e}")
        return {"success": False, "message": str(e)}


async def confirm_delete_job(
    job_id: str,
    user_token: str
) -> dict:
    """Thực sự xóa job sau khi HR đã xác nhận preview."""
    try:
        result = await _call_api("DELETE", f"http://jobhub_jobservice:8080/api/v1/jobs/{job_id}", user_token)
        if "error" in result and result["error"] is not None:
            return {"success": False, "message": result["error"]}
        return {
            "success": True,
            "message": f"Đã xóa thành công tin tuyển dụng ID: {job_id}",
            "job": result.get("data")
        }
    except Exception as e:
        logger.error(f"[JobConfirm] confirm_delete_job failed: {e}")
        return {"success": False, "message": str(e)}


async def extract_job_from_image(image_base64: str) -> dict:
    """Dùng Gemini Vision để trích xuất thông tin JD từ ảnh."""
    keys = _load_api_keys()
    if not keys:
        return {}

    prompt = """
Hãy phân tích ảnh này và trích xuất thông tin tuyển dụng theo định dạng JSON thuần túy (không dùng markdown).

Đối với các trường văn bản dài (description, requirements, benefits), bạn BẮT BUỘC phải sử dụng ký tự xuống dòng '\\n' để phân tách các dòng/ý tuyển dụng rõ ràng, không được viết dồn tất cả trên cùng một dòng.
Riêng trường 'requirements' và 'benefits', mỗi ý tuyển dụng phải là một dòng bắt đầu bằng '- ' và cách nhau bằng ký tự '\\n' (ví dụ: "- Ý 1\\n- Ý 2").

Trả về JSON với các trường sau (bỏ trống nếu không có thông tin):
{
  "name": "Tên vị trí tuyển dụng",
  "description": "Mô tả công việc chi tiết (sử dụng '\\n' để ngắt dòng/đoạn văn)",
  "requirements": "Yêu cầu ứng viên (dạng danh sách gạch đầu dòng bắt đầu bằng '- ', ngắt dòng bằng '\\n')",
  "benefits": "Quyền lợi và phúc lợi (dạng danh sách gạch đầu dòng bắt đầu bằng '- ', ngắt dòng bằng '\\n')",
  "location": "Địa điểm làm việc",
  "salary_min": null,
  "salary_max": null,
  "salary_currency": "VND",
  "is_salary_negotiable": false,
  "quantity": 1,
  "deadline": null,
  "skill_names": ["skill1", "skill2"],
  "experience_required": "Yêu cầu kinh nghiệm",
  "category": "Ngành nghề công việc"
}
    """

    models_to_try = [
        "gemini-3.5-flash",
        "gemini-3.1-flash-lite-preview",
        "gemini-3.1-pro-preview",
        "gemini-3.1-flash-lite",
        "gemini-3-flash-preview",
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash-latest",
    ]
    image_data = base64.b64decode(image_base64)

    for key in keys:
        for model_name in models_to_try:
            try:
                genai.configure(api_key=key)
                model = genai.GenerativeModel(model_name)
                response = await model.generate_content_async(
                    contents=[
                        genai.protos.Part(
                            inline_data=genai.protos.Blob(mime_type="image/jpeg", data=image_data)
                        ),
                        genai.protos.Part(text=prompt)
                    ],
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        response_mime_type="application/json"
                    )
                )
                return json.loads(response.text)
            except Exception as e:
                logger.warning(f"[JobConfirm] extract failed with key and model {model_name}: {e}")
    logger.error("[JobConfirm] extract_job_from_image failed with all keys and models")
    return {}
