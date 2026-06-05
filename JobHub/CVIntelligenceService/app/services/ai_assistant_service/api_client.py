# app/services/ai_assistant_service/api_client.py
import httpx


async def _call_api(
    method: str,
    url: str,
    token: str,
    json_data: dict = None,
    params: dict = None,
) -> dict:
    """Helper gọi internal API với Bearer token của user."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=15.0) as client:
        kw = dict(headers=headers, params=params or {})
        if method.upper() == "GET":
            resp = await client.get(url, **kw)
        elif method.upper() == "POST":
            resp = await client.post(url, json=json_data or {}, **kw)
        elif method.upper() == "PUT":
            resp = await client.put(url, json=json_data or {}, **kw)
        elif method.upper() == "PATCH":
            resp = await client.patch(url, json=json_data or {}, **kw)
        elif method.upper() == "DELETE":
            resp = await client.delete(url, **kw)
        else:
            return {"error": f"Unsupported method: {method}"}

        if 200 <= resp.status_code < 300:
            try:
                return resp.json()
            except Exception:
                return {"raw": resp.text}
        else:
            try:
                return {"error": resp.json().get("message", f"HTTP {resp.status_code}")}
            except Exception:
                return {"error": f"HTTP {resp.status_code}: {resp.text[:200]}"}


async def _call_api_multipart(
    url: str,
    token: str,
    file_bytes: bytes,
    filename: str,
    content_type: str = "application/octet-stream",
) -> dict:
    """
    Forward file bytes đến một endpoint dưới dạng multipart/form-data.
    Dùng cho các import API: users/import, skills/import, companies/import, admin/jobs/import.
    """
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": (filename, file_bytes, content_type)}
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers=headers, files=files)
        if 200 <= resp.status_code < 300:
            try:
                return {"success": True, "data": resp.json()}
            except Exception:
                return {"success": True, "data": {"raw": resp.text}}
        else:
            try:
                err = resp.json().get("message", f"HTTP {resp.status_code}")
            except Exception:
                err = f"HTTP {resp.status_code}: {resp.text[:300]}"
            return {"success": False, "error": err}

