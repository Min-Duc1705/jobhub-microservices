import httpx
import json

def main():
    login_url = "http://localhost:5001/api/v1/auth/login"
    login_data = {
        "email": "hr.fecredit@jobhub.vn",
        "password": "HRPassword@123456"
    }
    
    resp = httpx.post(login_url, json=login_data)
    if resp.status_code != 200:
        print("Login failed")
        return
        
    token = resp.json().get("data", {}).get("accessToken")
    headers = {"Authorization": f"Bearer {token}"}
    
    job_id = "90229569-027b-4328-aef7-2b41e710ef3b"
    app_url = f"http://localhost:5005/api/v1/applications?jobId={job_id}&pageSize=100"
    resp_app = httpx.get(app_url, headers=headers)
    result = resp_app.json().get("data", {})
    
    json_str = json.dumps(result, ensure_ascii=False)
    print(f"Total JSON length: {len(json_str)}")
    
    truncated = json_str[:3000]
    print("\n--- TRUNCATED JSON STRING (LAST 400 CHARACTERS) ---")
    print(truncated[-400:])

if __name__ == "__main__":
    main()
