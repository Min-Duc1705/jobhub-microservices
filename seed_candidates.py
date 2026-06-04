import os
import sys
import re
import random
import time
import requests
import psycopg2
import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')

# Import names mapping logic from generate_pdf_resumes
sys.path.append("t:/TryHard_IT_Project/Final/Backend")
from generate_pdf_resumes import FIRST_NAMES, MIDDLE_NAMES, LAST_NAMES, make_slug

GATEWAY_URL = "http://localhost:5000"
PASSWORD = "Candidate@123456"

def build_slug_to_name():
    existing_slugs = set()
    for folder in ["CV", "CV-1"]:
        folder_path = os.path.join("t:/TryHard_IT_Project/Final/Backend", folder)
        if os.path.exists(folder_path):
            for f in os.listdir(folder_path):
                if f.startswith("cv_") and f.endswith(".pdf"):
                    parts = f[3:-4].split("_")
                    if len(parts) >= 3:
                        existing_slugs.add("_".join(parts[:3]))
                        
    names_pool = []
    for f in FIRST_NAMES:
        for m in MIDDLE_NAMES:
            for l in LAST_NAMES:
                names_pool.append((f, m, l))
                
    random.seed(2026)
    random.shuffle(names_pool)
    
    slug_to_name = {}
    selected_count = 0
    for n in names_pool:
        full_name = f"{n[0]} {n[1]} {n[2]}"
        slug = make_slug(full_name).replace(".", "_")
        if slug not in existing_slugs:
            slug_to_name[slug] = full_name
            selected_count += 1
            if selected_count == 100:
                break
    return slug_to_name

def extract_pdf_info(filepath, name_slug, slug_to_name):
    # 1. Name
    original_name = slug_to_name.get(name_slug)
    if not original_name:
        name_slug_alt = "_".join(name_slug.split("_")[:2])
        original_name = slug_to_name.get(name_slug_alt, name_slug.replace("_", " ").title())
        
    # 2. Extract text from PDF
    with pdfplumber.open(filepath) as pdf:
        text = "\n".join([page.extract_text() or "" for page in pdf.pages])
        
    # 3. Email
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    email = email_match.group(0) if email_match else f"{name_slug}@gmail.com"
    
    # 4. Phone
    phone_match = re.search(r'0\d{9}', text)
    phone = phone_match.group(0) if phone_match else f"0900000000"
    
    # 5. Address
    address = "Hà Nội"
    if "Hồ Chí Minh" in text or "Ho Chi Minh" in text:
        address = "TP. Hồ Chí Minh"
        
    return {
        "name": original_name,
        "email": email,
        "phone": phone,
        "address": address
    }

def main():
    slug_to_name = build_slug_to_name()
    cv_dir = "t:/TryHard_IT_Project/Final/Backend/CV-1"
    files = sorted([f for f in os.listdir(cv_dir) if f.endswith(".pdf")])
    
    print(f"=== BẮT ĐẦU SEED {len(files)} ỨNG VIÊN ===")
    
    # Connect to PostgreSQL
    auth_conn = psycopg2.connect(host="localhost", port=5432, dbname="AuthService", user="postgres", password="root")
    profile_conn = psycopg2.connect(host="localhost", port=5432, dbname="ProfileService", user="postgres", password="root")
    
    auth_cur = auth_conn.cursor()
    profile_cur = profile_conn.cursor()
    
    success = 0
    failed = 0
    
    for i, filename in enumerate(files, 1):
        filepath = os.path.join(cv_dir, filename)
        parts = filename[:-4].split("_")
        name_slug = "_".join(parts[1:4])
        
        info = extract_pdf_info(filepath, name_slug, slug_to_name)
        email = info["email"]
        name = info["name"]
        phone = info["phone"]
        address = info["address"]
        
        print(f"[{i}/{len(files)}] Đang xử lý: {name} | {email} | {phone} | {address}...")
        
        # 1. Register candidate account
        user_id = None
        register_url = f"{GATEWAY_URL}/api/v1/auth/register"
        register_body = {
            "email": email,
            "username": name,
            "password": PASSWORD,
            "role": "CANDIDATE"
        }
        
        try:
            r = requests.post(register_url, json=register_body, timeout=10)
            res_json = r.json()
            if r.status_code == 201:
                # Registration successful, extract User ID
                if "data" in res_json and res_json["data"]:
                    user_id = res_json["data"].get("id")
                else:
                    user_id = res_json.get("id")
            elif r.status_code == 400 and "đã tồn tại" in r.text:
                # User already exists, retrieve ID from DB
                auth_cur.execute('SELECT "Id" FROM "AppUsers" WHERE "Email" = %s', (email.lower().strip(),))
                row = auth_cur.fetchone()
                if row:
                    user_id = row[0]
                print(f"  -> Tài khoản đã tồn tại. Đã lấy Id: {user_id}")
            else:
                print(f"  ❌ Đăng ký thất bại với mã {r.status_code}: {r.text}")
                failed += 1
                continue
        except Exception as e:
            print(f"  ❌ Lỗi kết nối khi đăng ký: {e}")
            failed += 1
            continue
            
        if not user_id:
            print(f"  ❌ Không thể lấy User ID cho {email}")
            failed += 1
            continue
            
        # 2. Activate candidate account in AuthDb
        try:
            auth_cur.execute('UPDATE "AppUsers" SET "Status" = \'Active\' WHERE "Id" = %s', (user_id,))
            auth_conn.commit()
            print(f"  -> Đã kích hoạt tài khoản trong AuthDb (Status = 'Active')")
        except Exception as e:
            auth_conn.rollback()
            print(f"  ❌ Lỗi khi kích hoạt tài khoản trong AuthDb: {e}")
            failed += 1
            continue
            
        # 3. Wait for profile to be created via MassTransit and update Address, Phone in ProfileDb
        customer_id = None
        try:
            found_profile = False
            for _ in range(50):  # Wait up to 5 seconds
                profile_cur.execute('SELECT "Id" FROM "Customers" WHERE "AppUserId" = %s', (user_id,))
                row = profile_cur.fetchone()
                if row:
                    customer_id = row[0]
                    found_profile = True
                    break
                time.sleep(0.1)
                
            if not found_profile:
                # If profile was not created by worker, create it directly
                profile_cur.execute('''
                    INSERT INTO "Customers" ("Id", "AppUserId", "Type", "FullName", "Phone", "Address", "CreatedDate", "CreatedBy", "IsDeleted")
                    VALUES (%s, %s, 'CANDIDATE', %s, %s, %s, NOW(), 'Seeder', false)
                ''', (user_id, user_id, name, phone, address))
                profile_conn.commit()
                print(f"  -> Không tìm thấy profile từ event, đã tạo trực tiếp Profile")
            else:
                # Update existing profile with phone and address
                profile_cur.execute('''
                    UPDATE "Customers"
                    SET "Phone" = %s, "Address" = %s, "YearsOfExperience" = %s
                    WHERE "AppUserId" = %s
                ''', (phone, address, random.randint(1, 10), user_id))
                profile_conn.commit()
                print(f"  -> Đã cập nhật Phone và Address vào ProfileDb")
        except Exception as e:
            profile_conn.rollback()
            print(f"  ❌ Lỗi khi xử lý profile: {e}")
            failed += 1
            continue

        # 4. Login to obtain Access Token
        token = None
        login_url = f"{GATEWAY_URL}/api/v1/auth/login"
        login_body = {
            "email": email,
            "password": PASSWORD
        }
        
        try:
            r = requests.post(login_url, json=login_body, timeout=10)
            res_json = r.json()
            if r.status_code == 200:
                if "data" in res_json and res_json["data"]:
                    token = res_json["data"].get("accessToken")
                else:
                    token = res_json.get("accessToken")
            else:
                print(f"  ❌ Đăng nhập thất bại: {r.text}")
                failed += 1
                continue
        except Exception as e:
            print(f"  ❌ Lỗi kết nối khi đăng nhập: {e}")
            failed += 1
            continue
            
        if not token:
            print(f"  ❌ Không lấy được access token cho {email}")
            failed += 1
            continue
            
        # 5. Upload CV PDF file
        upload_data = None
        upload_url = f"{GATEWAY_URL}/api/v1/resumes/upload"
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            with open(filepath, 'rb') as f:
                files_payload = {'file': (filename, f, 'application/pdf')}
                r = requests.post(upload_url, headers=headers, files=files_payload, timeout=30)
                res_json = r.json()
                if r.status_code == 200:
                    if "data" in res_json and res_json["data"]:
                        upload_data = res_json["data"]
                    else:
                        upload_data = res_json
                else:
                    print(f"  ❌ Upload CV thất bại: {r.text}")
                    failed += 1
                    continue
        except Exception as e:
            print(f"  ❌ Lỗi kết nối khi upload CV: {e}")
            failed += 1
            continue
            
        if not upload_data or "url" not in upload_data:
            print(f"  ❌ Dữ liệu upload không hợp lệ: {upload_data}")
            failed += 1
            continue
            
        # 6. Create Resume record to link CV
        create_resume_url = f"{GATEWAY_URL}/api/v1/resumes"
        create_body = {
            "title": filename,
            "url": upload_data["url"],
            "extractedText": upload_data.get("extractedText", ""),
            "isDefault": True
        }
        
        try:
            r = requests.post(create_resume_url, headers=headers, json=create_body, timeout=10)
            if r.status_code == 201 or r.status_code == 200:
                print(f"  ✅ Đăng ký + Kích hoạt + Upload CV thành công cho {name}!")
                success += 1
            else:
                print(f"  ❌ Tạo Resume record thất bại với mã {r.status_code}: {r.text}")
                failed += 1
        except Exception as e:
            print(f"  ❌ Lỗi kết nối khi tạo Resume record: {e}")
            failed += 1
            
    # Close database cursors and connections
    auth_cur.close()
    auth_conn.close()
    profile_cur.close()
    profile_conn.close()
    
    print(f"\n=== KẾT QUẢ SEEDING ===")
    print(f"Tổng số: {len(files)}")
    print(f"Thành công: {success}")
    print(f"Thất bại: {failed}")

if __name__ == "__main__":
    main()
