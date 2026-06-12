import psycopg2
import httpx
import json

def get_history_from_db():
    try:
        conn = psycopg2.connect(host='localhost', port=5432, dbname='NotificationService', user='postgres', password='root')
        cur = conn.cursor()
        user_id = '0739d6f3-f96e-4f4e-b4df-3c8261be467c'
        cur.execute('SELECT "Id" FROM "Conversations" WHERE "ParticipantA" = %s OR "ParticipantB" = %s', (user_id, user_id))
        row = cur.fetchone()
        if not row:
            return []
        conv_id = row[0]
        cur.execute('SELECT "SenderId", "Content" FROM "Messages" WHERE "ConversationId" = %s ORDER BY "CreatedAt" ASC', (conv_id,))
        messages = cur.fetchall()
        
        history = []
        for sender, content in messages:
            role = "user" if sender == user_id else "model"
            history.append({
                "role": role,
                "content": content
            })
        conn.close()
        return history
    except Exception as e:
        print("Error getting history:", e)
        return []

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
    history = get_history_from_db()
    
    cleaned_history = []
    for h in history:
        if "xem kĩ" in h["content"] or "xem kĩ lại" in h["content"]:
            break
        cleaned_history.append(h)
        
    assistant_url = "http://localhost:5006/api/v1/assistant/chat"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Session-Id": "session_0739d6f3-f96e-4f4e-b4df-3c8261be467c"
    }
    
    payload = {
        "message": "xem kĩ lại hồ sơ ứng tuyển cho vị trí Java Developer có bao nhiêu ứng viên",
        "conversation_history": cleaned_history
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
