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
        print(f"Login failed: {resp.status_code}")
        return
        
    token = resp.json().get("data", {}).get("accessToken")
    
    # Clean session first
    clear_url = "http://localhost:5006/api/v1/assistant/session"
    httpx.request("DELETE", clear_url, headers={"X-Session-Id": "test_session_clean_java"})
    
    assistant_url = "http://localhost:5006/api/v1/assistant/chat"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Session-Id": "test_session_clean_java"
    }
    
    payload = {
        "message": "Xem kĩ lại hồ sơ ứng tuyển cho vị trí Java Developer (ID: 90229569-027b-4328-aef7-2b41e710ef3b) có bao nhiêu ứng viên",
        "conversation_history": []
    }
    
    resp = httpx.post(assistant_url, json=payload, headers=headers, timeout=30.0)
    
    if resp.status_code != 200:
        print(f"Assistant call failed: {resp.status_code} - {resp.text}")
        return
        
    result = resp.json()
    print("\n--- Assistant Reply ---")
    print(result.get("reply"))
    print("\n--- Actions Taken (Summarized) ---")
    for act in result.get("actions_taken", []):
        print(f"Action: {act.get('tool_name')} | Args: {act.get('data', {}).get('job_id') or act.get('data', {}).get('jobId')}")
        if 'applications' in act.get('data', {}):
            apps = act['data']['applications']
            print(f"  Returned {len(apps)} applications:")
            for a in apps:
                res = a.get('resume', {})
                print(f"    - Candidate CustomerId: {a.get('customerId')}, CV Title: {res.get('title')}")

if __name__ == "__main__":
    main()
