# app/services/ai_assistant_service/executor/company_executor.py
"""
Executor cho các tools liên quan đến Company:
get_my_company_info, search_companies, update_company_info
"""
import logging
from ..api_client import _call_api

logger = logging.getLogger(__name__)


async def execute_get_my_company_info(args: dict, user_token: str) -> dict:
    # Bước 1: Lấy companyId từ profile
    company_id = ""
    try:
        prof_result = await _call_api("GET", "http://profileservice:8080/api/v1/customers/me", user_token)
        prof_data = prof_result.get("data") if isinstance(prof_result, dict) and "data" in prof_result else prof_result
        if isinstance(prof_data, dict):
            company_id = prof_data.get("companyId", "")
    except Exception as e:
        logger.error(f"[CompanyExecutor] get_my_company_info failed to get profile: {e}")

    if company_id:
        # Bước 2: Lấy thông tin công ty
        result = await _call_api("GET", f"http://companyservice:8080/api/v1/companies/{company_id}", user_token)
        company_data = result.get("data") if isinstance(result, dict) and "data" in result else result
        return {"company": company_data}

    return {"company": None, "message": "Tài khoản của bạn chưa được liên kết với công ty nào."}


async def execute_search_companies(args: dict, user_token: str) -> dict:
    keyword = args.get("keyword", "")
    params = {"pageSize": int(args.get("pageSize", 10))}
    if keyword:
        params["searchTerm"] = keyword
    result = await _call_api("GET", "http://companyservice:8080/api/v1/companies", user_token, params=params)
    companies_raw = result.get("data", {}).get("result", [])
    companies = [
        {
            "id": c.get("id"),
            "name": c.get("name"),
            "industry": c.get("industry"),
            "address": c.get("address"),
            "size": c.get("size"),
            "website": c.get("website")
        }
        for c in companies_raw
    ]
    return {"companies": companies, "total": result.get("data", {}).get("meta", {}).get("total", len(companies))}


async def execute_update_company_info(args: dict, user_token: str) -> dict:
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
            payload["companySize"] = 1  # SME default

    return await _call_api(
        "PUT", f"http://companyservice:8080/api/v1/companies/{comp_id}",
        user_token, json_data=payload
    )


async def execute_create_company(args: dict, user_token: str) -> dict:
    """Admin tạo mới công ty."""
    payload = {"name": args.get("name", "").strip()}

    if args.get("description"):
        payload["description"] = args["description"]
    if args.get("address"):
        payload["address"] = args["address"]
    if args.get("industry"):
        payload["industry"] = args["industry"]
    if args.get("website"):
        payload["website"] = args["website"]
    if args.get("contactEmail"):
        payload["contactEmail"] = args["contactEmail"]
    if args.get("taxCode"):
        payload["taxCode"] = args["taxCode"]
    if args.get("companySize"):
        sz = str(args["companySize"]).upper()
        if "STARTUP" in sz:
            payload["companySize"] = 0
        elif "ENTERPRISE" in sz:
            payload["companySize"] = 2
        else:
            payload["companySize"] = 1  # SME default

    return await _call_api(
        "POST", "http://companyservice:8080/api/v1/companies",
        user_token, json_data=payload
    )
