import os
import sys
import re
import random
import time
import requests
import psycopg2
import pdfplumber
import unicodedata

sys.stdout.reconfigure(encoding='utf-8')

# Import helper data from generate_pdf_resumes
sys.path.append("t:/TryHard_IT_Project/Final/Backend")
from generate_pdf_resumes import ADDRESSES, make_slug

GATEWAY_URL = "http://localhost:5000"
PASSWORD = "Candidate@123456"

def remove_accents_str(input_str):
    s = input_str.replace('Đ', 'D').replace('đ', 'd')
    nfkd_form = unicodedata.normalize('NFKD', s)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

def extract_name_from_text(text, name_slug):
    slug_words = name_slug.lower().split("_")
    words = re.findall(r'[a-zA-ZÀ-ỹ\d]+', text)
    for i in range(len(words) - len(slug_words) + 1):
        candidate_words = words[i : i + len(slug_words)]
        cleaned_candidates = [remove_accents_str(w).lower() for w in candidate_words]
        if cleaned_candidates == slug_words:
            return " ".join(candidate_words).title()
    return name_slug.replace("_", " ").title()

def extract_pdf_info(filepath, name_slug):
    with pdfplumber.open(filepath) as pdf:
        text = "\n".join([page.extract_text() or "" for page in pdf.pages])
        
    original_name = extract_name_from_text(text, name_slug)
    
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    email = email_match.group(0).lower().strip() if email_match else f"{name_slug}@gmail.com"
    
    phone_match = re.search(r'0\d{9}', text)
    phone = phone_match.group(0) if phone_match else f"0900000000"
    
    address = "Hà Nội"
    for addr in ADDRESSES:
        if addr in text:
            address = addr
            break
            
    return {
        "name": original_name,
        "email": email,
        "phone": phone,
        "address": address,
        "text": text
    }

def main():
    cv_dir = "t:/TryHard_IT_Project/Final/Backend/CV PHP"
    if not os.path.exists(cv_dir):
        print(f"❌ Thư mục {cv_dir} không tồn tại!")
        sys.exit(1)
        
    # Get all candidate CV files
    files = sorted([
        f for f in os.listdir(cv_dir) 
        if f.startswith("cv_") and f.endswith(".pdf")
    ])
    
    print(f"=== BẮT ĐẦU SEED {len(files)} ỨNG VIÊN TỪ THƯ MỤC CV PHP ===")
    
    # Connect to PostgreSQL
    auth_conn = psycopg2.connect(host="localhost", port=5432, dbname="AuthService", user="postgres", password="root")
    profile_conn = psycopg2.connect(host="localhost", port=5432, dbname="ProfileService", user="postgres", password="root")
    resume_conn = psycopg2.connect(host="localhost", port=5432, dbname="ResumeService", user="postgres", password="root")
    
    auth_cur = auth_conn.cursor()
    profile_cur = profile_conn.cursor()
    resume_cur = resume_conn.cursor()
    
    success = 0
    skipped = 0
    failed = 0
    
    for i, filename in enumerate(files, 1):
        filepath = os.path.join(cv_dir, filename)
        parts = filename[:-4].split("_")
        name_slug = "_".join(parts[1:4])
        
        try:
            info = extract_pdf_info(filepath, name_slug)
        except Exception as e:
            print(f"[{i}/{len(files)}] ❌ Lỗi khi đọc file {filename}: {e}")
            failed += 1
            continue
            
        email = info["email"]
        name = info["name"]
        phone = info["phone"]
        address = info["address"]
        text_content = info["text"]
        
        # Check if user already exists in AuthDb
        user_id = None
        auth_cur.execute('SELECT "Id" FROM "AppUsers" WHERE "Email" = %s', (email,))
        row = auth_cur.fetchone()
        if row:
            user_id = row[0]
            # Check if CV is already uploaded for this user
            resume_cur.execute('SELECT COUNT(*) FROM "Resumes" WHERE "CustomerId" = %s AND "Title" = %s', (user_id, filename))
            if resume_cur.fetchone()[0] > 0:
                print(f"[{i}/{len(files)}] ⏩ Đã bỏ qua (đã tồn tại): {name} | {email}")
                skipped += 1
                continue
                
        print(f"[{i}/{len(files)}] Đang xử lý: {name} | {email} | {phone} | {address}...")
        
        # Register candidate account if not exists
        if not user_id:
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
                    if "data" in res_json and res_json["data"]:
                        user_id = res_json["data"].get("id")
                    else:
                        user_id = res_json.get("id")
                elif r.status_code == 400 and "đã tồn tại" in r.text:
                    auth_cur.execute('SELECT "Id" FROM "AppUsers" WHERE "Email" = %s', (email,))
                    row = auth_cur.fetchone()
                    if row:
                        user_id = row[0]
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
            
        # Activate candidate account in AuthDb
        try:
            auth_cur.execute('UPDATE "AppUsers" SET "Status" = \'Active\' WHERE "Id" = %s', (user_id,))
            auth_conn.commit()
            print(f"  -> Đã kích hoạt tài khoản trong AuthDb (Status = 'Active')")
        except Exception as e:
            auth_conn.rollback()
            print(f"  ❌ Lỗi khi kích hoạt tài khoản trong AuthDb: {e}")
            failed += 1
            continue
            
        # Wait for profile to be created via MassTransit and update Phone, Address
        try:
            found_profile = False
            for _ in range(50):  # Wait up to 5 seconds
                profile_cur.execute('SELECT "Id" FROM "Customers" WHERE "AppUserId" = %s', (user_id,))
                row = profile_cur.fetchone()
                if row:
                    found_profile = True
                    break
                time.sleep(0.1)
                
            if not found_profile:
                profile_cur.execute('''
                    INSERT INTO "Customers" ("Id", "AppUserId", "Type", "FullName", "Phone", "Address", "CreatedDate", "CreatedBy", "IsDeleted")
                    VALUES (%s, %s, 'CANDIDATE', %s, %s, %s, NOW(), 'Seeder', false)
                ''', (user_id, user_id, name, phone, address))
                profile_conn.commit()
                print(f"  -> Không tìm thấy profile từ event, đã tạo trực tiếp Profile")
            else:
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

        # Login to obtain Access Token
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
            
        # Upload CV PDF file
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
            
        # Create Resume record to link CV
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
    resume_cur.close()
    resume_conn.close()
    
    print(f"\n=== KẾT QUẢ SEEDING THƯ MỤC CV PHP ===")
    print(f"Tổng số: {len(files)}")
    print(f"Đã bỏ qua (trùng lặp): {skipped}")
    print(f"Thành công mới: {success}")
    print(f"Thất bại: {failed}")

if __name__ == "__main__":
    main()
