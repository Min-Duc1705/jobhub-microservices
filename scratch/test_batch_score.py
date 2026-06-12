import httpx
import json
import asyncio
import sys

# Add app to python path
sys.path.append('t:/TryHard_IT_Project/Final/Backend/JobHub/CVIntelligenceService')

async def main():
    # 1. Login
    login_url = "http://localhost:5001/api/v1/auth/login"
    login_data = {
        "email": "hr.fecredit@jobhub.vn",
        "password": "HRPassword@123456"
    }
    
    print("Logging in...")
    resp = httpx.post(login_url, json=login_data)
    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code}")
        return
        
    token = resp.json().get("data", {}).get("accessToken")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get job description
    job_id = "90229569-027b-4328-aef7-2b41e710ef3b"
    job_url = f"http://localhost:5002/api/v1/jobs/{job_id}"
    resp_job = httpx.get(job_url, headers=headers)
    job_data = resp_job.json().get("data", {})
    desc = job_data.get("description", "")
    reqs = job_data.get("requirements", "")
    job_desc = f"{desc}\n{reqs}".strip()
    
    # 3. Get applications
    app_url = f"http://localhost:5005/api/v1/applications?jobId={job_id}&pageSize=100"
    resp_app = httpx.get(app_url, headers=headers)
    apps = resp_app.json().get("data", {}).get("result", [])
    
    print(f"Found {len(apps)} applications in API.")
    
    # 4. Build cv_list
    cv_list = []
    def _extract_cv_text(resume: dict) -> str:
        if not resume: return ""
        return resume.get("extractedText") or ""
        
    for app in apps:
        resume = app.get("resume") or {}
        cv_text = _extract_cv_text(resume)
        cv_list.append({
            "application_id": app.get("id"),
            "job_id": job_id,
            "customer_id": app.get("customerId") or app.get("customer_id"),
            "cv_text": cv_text
        })
        
    # 5. Call batch_score
    from app.services.cv_service import batch_score
    from app.schemas.cv_scoring import SkillScoringRequest
    
    scoring_req = SkillScoringRequest(
        job_description=job_desc,
        cv_list=cv_list
    )
    
    print("Calling batch_score...")
    score_res = await batch_score(scoring_req, top_n=10)
    print("Result:")
    print(json.dumps(score_res.model_dump(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
