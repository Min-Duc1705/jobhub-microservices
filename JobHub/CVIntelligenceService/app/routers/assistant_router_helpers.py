# app/routers/assistant_router_helpers.py
"""
Helper functions cho assistant_router:
- Redis permission cache lookup
- JWT decode
- AuthService profile/permission fetch
- Company name fetch for HR accounts
"""
import base64
import json
import logging
import os
from typing import Optional

import httpx
import redis.asyncio as async_redis
import io
import zipfile
import xml.etree.ElementTree as ET
import csv

logger = logging.getLogger(__name__)

# Redis client (shared)
redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_client = async_redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)


async def fetch_user_permissions_from_redis(email: str) -> Optional[list[dict]]:
    """Thử lấy danh sách permissions của user từ Redis cache (perm:{email})."""
    if not email:
        return None
    try:
        redis_key = f"JobHubAuth_perm:{email}"
        cached_data = await redis_client.hget(redis_key, "data")
        if cached_data:
            raw_perms = json.loads(cached_data)
            if isinstance(raw_perms, list):
                permissions = []
                for p in raw_perms:
                    method = p.get("Method") or p.get("method")
                    api_path = p.get("ApiPath") or p.get("apiPath")
                    if method and api_path:
                        permissions.append({"method": method, "apiPath": api_path})
                logger.info(
                    f"[AssistantHelpers] Loaded {len(permissions)} permissions from Redis for {email}"
                )
                return permissions
    except Exception as e:
        logger.error(f"[AssistantHelpers] Failed to fetch permissions from Redis: {e}")
    return None


def extract_user_info_from_token(authorization: str) -> dict:
    """Parse JWT payload để lấy user info (không verify signature, chỉ decode)."""
    try:
        parts = authorization.replace("Bearer ", "").split(".")
        if len(parts) != 3:
            return {}

        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding

        payload = json.loads(base64.urlsafe_b64decode(payload_b64))

        # Map .NET claim types to standard keys
        role = (
            payload.get("role")
            or payload.get("http://schemas.microsoft.com/ws/2008/06/identity/claims/role")
        )
        if role:
            if isinstance(role, list):
                role = next((r for r in role if r), "USER")
            payload["role"] = str(role)

        username = (
            payload.get("username")
            or payload.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name")
            or payload.get("sub")
        )
        if username:
            if isinstance(username, list):
                username = next((u for u in username if u), "Người dùng")
            payload["username"] = str(username)

        email = (
            payload.get("email")
            or payload.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress")
        )
        if email:
            if isinstance(email, list):
                email = next((e for e in email if e), "")
            payload["email"] = str(email)

        return payload
    except Exception:
        return {}


async def fetch_user_profile_and_permissions(token: str) -> dict:
    """Gọi AuthService để lấy thông tin account chi tiết và permissions thực tế."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = "http://authservice:8080/api/v1/auth/account"
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                body = resp.json()
                data = body.get("data") if "data" in body else body
                if not data:
                    return {}

                user = data.get("user") or {}
                role_obj = user.get("role") or {}
                role_name = role_obj.get("name") or "USER"

                permissions = [
                    {"method": p.get("method"), "apiPath": p.get("apiPath")}
                    for p in (role_obj.get("permissions") or [])
                ]

                return {
                    "role": role_name,
                    "permissions": permissions,
                    "username": user.get("username") or user.get("email", "Người dùng"),
                }
            else:
                logger.warning(
                    f"[AssistantHelpers] Failed to fetch account from authservice: HTTP {resp.status_code}"
                )
                return {}
        except Exception as e:
            logger.error(f"[AssistantHelpers] Error calling authservice: {e}")
            return {}


async def fetch_user_company_name(token: str, role: str) -> str:
    """Nếu user là HR/Employer, fetch tên công ty của họ từ ProfileService → CompanyService."""
    role_upper = (role or "USER").upper()
    if not ("HR" in role_upper or "EMPLOYER" in role_upper or "ADMIN" in role_upper):
        return ""

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    profile_url = "http://profileservice:8080/api/v1/customers/me"
    async with httpx.AsyncClient(timeout=3.0) as client:
        try:
            resp = await client.get(profile_url, headers=headers)
            if resp.status_code == 200:
                body = resp.json()
                data = body.get("data") if "data" in body else body
                if not data:
                    return ""

                company_id = data.get("companyId")
                if not company_id:
                    return ""

                comp_url = f"http://companyservice:8080/api/v1/companies/{company_id}"
                comp_resp = await client.get(comp_url, headers=headers)
                if comp_resp.status_code == 200:
                    comp_body = comp_resp.json()
                    comp_data = comp_body.get("data") if "data" in comp_body else comp_body
                    if comp_data:
                        company_name = comp_data.get("name", "")
                        logger.info(f"[AssistantHelpers] Found company name for HR: {company_name}")
                        return company_name
            return ""
        except Exception as e:
            logger.error(f"[AssistantHelpers] Error fetching user company name: {e}")
            return ""


def parse_skills_from_file_bytes(file_bytes: bytes, filename: str) -> list[str]:
    """
    Parse danh sách kỹ năng từ file bytes (.csv, .xlsx).
    Chỉ dùng thư viện chuẩn của Python để tránh dependencies.
    """
    filename = filename.lower()
    skills = []
    
    if filename.endswith('.csv'):
        try:
            content = file_bytes.decode('utf-8', errors='ignore')
            reader = csv.reader(io.StringIO(content))
            rows = list(reader)
            if not rows:
                return []
            
            # Tìm column index cho 'name'
            header = [col.strip().lower() for col in rows[0]]
            name_idx = 0
            if 'name' in header:
                name_idx = header.index('name')
                
            for row in rows[1:]:
                if len(row) > name_idx:
                    val = row[name_idx].strip()
                    if val:
                        skills.append(val)
        except Exception as e:
            logger.error(f"[AssistantHelpers] Error parsing CSV: {e}")
                    
    elif filename.endswith(('.xlsx', '.xls')):
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                # 1. Đọc shared strings
                shared_strings = []
                if 'xl/sharedStrings.xml' in z.namelist():
                    ss_xml = z.read('xl/sharedStrings.xml')
                    root = ET.fromstring(ss_xml)
                    ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                    for t_node in root.findall('.//ns:t', ns):
                        shared_strings.append(t_node.text or '')
                
                # 2. Đọc sheet1.xml
                sheet_xml = z.read('xl/worksheets/sheet1.xml')
                root = ET.fromstring(sheet_xml)
                ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                
                rows = root.findall('.//ns:row', ns)
                if not rows:
                    return []
                
                for row_node in rows:
                    cells = row_node.findall('ns:c', ns)
                    row_data = {}
                    for cell in cells:
                        r_attr = cell.get('r', '')
                        col_letter = ''.join([c for c in r_attr if c.isalpha()])
                        
                        val = ''
                        t_attr = cell.get('t', '')
                        v_node = cell.find('ns:v', ns)
                        
                        if v_node is not None:
                            v_val = v_node.text or ''
                            if t_attr == 's':
                                idx = int(v_val)
                                if 0 <= idx < len(shared_strings):
                                    val = shared_strings[idx]
                            else:
                                val = v_val
                        else:
                            is_node = cell.find('ns:is/ns:t', ns)
                            if is_node is not None:
                                val = is_node.text or ''
                        
                        row_data[col_letter] = val.strip()
                    
                    if 'A' in row_data:
                        name_val = row_data['A']
                        if name_val and name_val.lower() != 'name':
                            skills.append(name_val)
        except Exception as e:
            logger.error(f"[AssistantHelpers] Error parsing XLSX: {e}")
            
    return skills
