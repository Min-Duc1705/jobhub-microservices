import httpx
import json

def main():
    # 1. Login to get token
    login_url = "http://localhost:5001/api/v1/auth/login"
    login_data = {
        "email": "hr.fecredit@jobhub.vn",
        "password": "HRPassword@123456"
    }
    
    print("Logging in to AuthService...")
    resp = httpx.post(login_url, json=login_data)
    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code} - {resp.text}")
        return
        
    body = resp.json()
    token = body.get("data", {}).get("accessToken")
    if not token:
        print("Token not found in response!")
        return
    print("Login successful! Token acquired.")
    
    # 2. Call Assistant Chat
    assistant_url = "http://localhost:5006/api/v1/assistant/chat"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Session-Id": "test_session_fecredit"
    }
    
    # We clear session first
    clear_url = "http://localhost:5006/api/v1/assistant/session"
    httpx.request("DELETE", clear_url, headers={"X-Session-Id": "test_session_fecredit"})
    
    payload = {
        "message": "xem kĩ lại hồ sơ ứng tuyển cho vị trí Java Developer có bao nhiêu ứng viên",
        "conversation_history": []
    }
    
    print("\nSending message to AI Assistant...")
    resp = httpx.post(assistant_url, json=payload, headers=headers, timeout=30.0)
    
    if resp.status_code != 200:
        print(f"Assistant call failed: {resp.status_code} - {resp.text}")
        return
        
    result = resp.json()
    print("\n--- Assistant Reply ---")
    print(result.get("reply"))
    print("\n--- Actions Taken ---")
    print(json.dumps(result.get("actions_taken"), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
