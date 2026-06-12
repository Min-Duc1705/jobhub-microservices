import httpx
import json

def main():
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
    
    # 2. Query Resumeservice applications API
    job_id = "90229569-027b-4328-aef7-2b41e710ef3b"
    app_url = f"http://localhost:5005/api/v1/applications?jobId={job_id}&pageSize=100"
    
    print(f"Querying applications from resumeservice at: {app_url}")
    resp_app = httpx.get(app_url, headers=headers)
    print(f"Status: {resp_app.status_code}")
    if resp_app.status_code == 200:
        print(json.dumps(resp_app.json(), indent=2, ensure_ascii=False))
    else:
        print(resp_app.text)

if __name__ == "__main__":
    main()
