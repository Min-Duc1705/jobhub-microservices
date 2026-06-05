# app/services/ai_assistant_service/api_client.py
import httpx

async def _call_api(method: str, url: str, token: str, json_data: dict = None) -> dict:
    """Helper gọi internal API với Bearer token của user."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=15.0) as client:
        if method.upper() == "GET":
            resp = await client.get(url, headers=headers, params=json_data or {})
        elif method.upper() == "POST":
            resp = await client.post(url, headers=headers, json=json_data or {})
        elif method.upper() == "PUT":
            resp = await client.put(url, headers=headers, json=json_data or {})
        elif method.upper() == "DELETE":
            resp = await client.delete(url, headers=headers)
        else:
            return {"error": f"Unsupported method: {method}"}

        if resp.status_code >= 200 and resp.status_code < 300:
            try:
                return resp.json()
            except Exception:
                return {"raw": resp.text}
        else:
            try:
                return {"error": resp.json().get("message", f"HTTP {resp.status_code}")}
            except Exception:
                return {"error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
