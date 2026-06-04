import os
import sys
import re
import uuid
import json
import random
import time
import requests
import psycopg2
import unicodedata
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

sys.stdout.reconfigure(encoding='utf-8')

GATEWAY_URL = "http://localhost:5000"
PASSWORD = "HRPassword@123456"

# Connect configurations
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "root"
}

def remove_accents_str(input_str):
    s = input_str.replace('Đ', 'D').replace('đ', 'd')
    nfkd_form = unicodedata.normalize('NFKD', s)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

def make_slug(name):
    clean_name = remove_accents_str(name.lower())
    clean_name = re.sub(r'[^a-z0-9\s]', '', clean_name)
    parts = clean_name.split()
    if not parts:
        return "hr"
    return ".".join(parts)

def clean_company_name(name):
    s = remove_accents_str(name).lower()
    s = re.sub(r'[^a-z0-9\s]', '', s)
    words = s.split()
    exclusions = {'vietnam', 'software', 'solution', 'solutions', 'co', 'ltd', 'corp', 'corporation', 'technology', 'technologies', 'jsc', 'asia', 'global', 'viet', 'nam'}
    filtered = [w for w in words if w not in exclusions]
    if not filtered:
        return s
    return " ".join(filtered)

def crawl_itviec_jobs():
    print("\n=== BẮT ĐẦU CÀO DỮ LIỆU TUYỂN DỤNG TỪ ITVIEC ===")
    
    keywords = [
        'react-native', 'reactjs', 'nodejs', 'java', 'python', 'golang', 'tester', 'qa', 'devops', 
        'android', 'ios', 'php', 'angular', 'vuejs', 'typescript', 'javascript', 'aws', 'docker'
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,vi;q=0.8"
    }
    
    unique_jobs = {}
    page = 1
    
    # Crawl until we have at least 550 unique jobs to ensure we can easily slice exactly 500
    while len(unique_jobs) < 550 and page <= 3:
        print(f"\n[Crawler] --- ĐANG CÀO TRANG {page} ---")
        for kw in keywords:
            if len(unique_jobs) >= 550:
                break
                
            url = f"https://itviec.com/it-jobs/{kw}?page={page}"
            print(f"[Crawler] Đang quét: {url} (Đã có: {len(unique_jobs)} jobs)")
            
            try:
                # Add delay to avoid getting blocked
                time.sleep(random.uniform(0.3, 0.7))
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code != 200:
                    print(f"  [Error] HTTP Status {res.status_code}")
                    continue
                    
                soup = BeautifulSoup(res.text, 'html.parser')
                cards = soup.find_all(class_=lambda x: x and 'job-card' in x)
                real_cards = [c for c in cards if 'segment-job-card' not in ' '.join(c.get('class', []))]
                
                for card in real_cards:
                    if len(unique_jobs) >= 550:
                        break
                        
                    # 1. Job Title
                    title_el = card.find(attrs={"data-search--job-selection-target": "jobTitle"}) or card.find('h3') or card.find('h2')
                    if not title_el:
                        continue
                    title = title_el.text.strip()
                    
                    # 2. Company Name
                    company_el = card.find('a', class_='text-rich-grey') or card.find(class_='text-hover-underline')
                    if not company_el:
                        continue
                    company_name = company_el.text.strip()
                    
                    job_key = (company_name.lower().strip(), title.lower().strip())
                    if job_key in unique_jobs:
                        continue
                        
                    # 3. Location
                    location = "Hà Nội"
                    use_tag = card.find('use', href=lambda x: x and '#map-pin' in x)
                    if use_tag:
                        svg_tag = use_tag.parent
                        loc_div = svg_tag.find_next_sibling('div')
                        if loc_div:
                            loc_text = loc_div.text.strip().lower()
                            if 'ho chi minh' in loc_text or 'hồ chí minh' in loc_text or 'hcm' in loc_text:
                                location = "TP. Hồ Chí Minh"
                            elif 'da nang' in loc_text or 'đà nẵng' in loc_text:
                                location = "Đà Nẵng"
                            elif 'ha noi' in loc_text or 'hà nội' in loc_text:
                                location = "Hà Nội"
                            else:
                                # default clean format for other locations
                                location = loc_div.text.strip()
                                
                    # 4. Skills
                    skills = []
                    tag_list_div = card.find('div', attrs={"data-controller": "responsive-tag-list"})
                    if tag_list_div:
                        skills = [a.text.strip() for a in tag_list_div.find_all('a')]
                        
                    # 5. Benefits
                    benefits_list = []
                    benefits_div = card.find('div', class_=lambda x: x and 'small-text' in x and 'text-it-black' in x)
                    if benefits_div:
                        benefits_list = [li.text.strip() for li in benefits_div.find_all('li')]
                    benefits_str = "\n".join([f"- {b}" for b in benefits_list]) if benefits_list else "- Chế độ lương thưởng cạnh tranh.\n- Cơ hội thăng tiến nghề nghiệp.\n- Môi trường làm việc năng động."
                    
                    # 6. Store job info
                    unique_jobs[job_key] = {
                        "title": title,
                        "company_name_raw": company_name,
                        "location": location,
                        "skills": skills,
                        "benefits": benefits_str
                    }
                    
            except Exception as e:
                print(f"  [Error] {e}")
                continue
                
        page += 1
        
    print(f"\n[Crawler] ✅ Đã hoàn thành cào! Tổng cộng thu thập được: {len(unique_jobs)} jobs độc bản.")
    return list(unique_jobs.values())

def main():
    # 1. Fetch companies
    try:
        conn_comp = psycopg2.connect(host="localhost", port=5432, dbname="CompanyService", user="postgres", password="root")
        cur_comp = conn_comp.cursor()
        cur_comp.execute('SELECT "Id", "Name", "Logo" FROM "Companies" WHERE "IsDeleted" = FALSE')
        companies = cur_comp.fetchall()
        cur_comp.close()
        conn_comp.close()
    except Exception as e:
        print(f"❌ Lỗi kết nối CompanyService: {e}")
        sys.exit(1)
        
    print(f"Database có: {len(companies)} công ty.")
    
    # 2. Seed HR accounts
    auth_conn = psycopg2.connect(host="localhost", port=5432, dbname="AuthService", user="postgres", password="root")
    profile_conn = psycopg2.connect(host="localhost", port=5432, dbname="ProfileService", user="postgres", password="root")
    
    auth_cur = auth_conn.cursor()
    profile_cur = profile_conn.cursor()
    
    print("\n=== BẮT ĐẦU SEED TÀI KHOẢN HR ===")
    
    company_hr_map = {} # Maps company_id to hr_user_id
    
    for idx, (comp_id, comp_name, comp_logo) in enumerate(companies, 1):
        slug = make_slug(comp_name).replace(".", "_")
        email = f"hr.{slug}@jobhub.vn"
        username = f"HR {comp_name}"
        
        # 2a. Register HR account via HTTP to trigger MassTransit events
        user_id = None
        register_url = f"{GATEWAY_URL}/api/v1/auth/register"
        register_body = {
            "email": email,
            "username": username,
            "password": PASSWORD,
            "role": "HR"
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
                auth_cur.execute('SELECT "Id" FROM "AppUsers" WHERE "Email" = %s', (email.lower().strip(),))
                row = auth_cur.fetchone()
                if row:
                    user_id = row[0]
            else:
                print(f"  ❌ Đăng ký thất bại cho {email}: {r.text}")
                continue
        except Exception as e:
            # Fallback direct query if HTTP fails
            auth_cur.execute('SELECT "Id" FROM "AppUsers" WHERE "Email" = %s', (email.lower().strip(),))
            row = auth_cur.fetchone()
            if row:
                user_id = row[0]
            else:
                print(f"  ❌ Lỗi kết nối đăng ký {email}: {e}")
                continue
                
        if not user_id:
            print(f"  ❌ Không lấy được User ID cho {email}")
            continue
            
        company_hr_map[comp_id] = user_id
        
        # 2b. Activate HR in AuthService
        try:
            auth_cur.execute('UPDATE "AppUsers" SET "Status" = \'Active\' WHERE "Id" = %s', (user_id,))
            auth_conn.commit()
        except Exception as e:
            auth_conn.rollback()
            print(f"  ❌ Lỗi kích hoạt HR {email}: {e}")
            continue
            
        # 2c. Check / Update Profile in ProfileService Customers table
        try:
            found_profile = False
            for _ in range(50):
                profile_cur.execute('SELECT "Id" FROM "Customers" WHERE "AppUserId" = %s', (user_id,))
                row = profile_cur.fetchone()
                if row:
                    found_profile = True
                    break
                time.sleep(0.1)
                
            if not found_profile:
                # Insert directly if not created by worker
                profile_cur.execute('''
                    INSERT INTO "Customers" ("Id", "AppUserId", "Type", "FullName", "CreatedDate", "CreatedBy", "IsDeleted", "CompanyId")
                    VALUES (%s, %s, 'EMPLOYER', %s, NOW(), 'Seeder', false, %s)
                ''', (user_id, user_id, username, comp_id))
                profile_conn.commit()
            else:
                # Update CompanyId
                profile_cur.execute('''
                    UPDATE "Customers"
                    SET "CompanyId" = %s, "Type" = 'EMPLOYER'
                    WHERE "AppUserId" = %s
                ''', (comp_id, user_id))
                profile_conn.commit()
        except Exception as e:
            profile_conn.rollback()
            print(f"  ❌ Lỗi cập nhật Profile HR {email}: {e}")
            continue
            
        if idx % 10 == 0 or idx == len(companies):
            print(f"  -> Đã seed xong {idx}/{len(companies)} tài khoản HR.")
            
    auth_cur.close()
    auth_conn.close()
    profile_cur.close()
    profile_conn.close()
    
    print("✅ Hoàn thành Seeding tài khoản HR.")
    
    # 3. Crawl Jobs
    jobs_pool = crawl_itviec_jobs()
    if len(jobs_pool) < 500:
        print(f"[Warning] Chỉ cào được {len(jobs_pool)} jobs. Đang tự động nhân bản/sinh thêm job mẫu để đạt đủ 500...")
        needed = 500 - len(jobs_pool)
        for i in range(needed):
            base_job = random.choice(jobs_pool)
            padded_job = base_job.copy()
            padded_job["title"] = f"{base_job['title']} (Senior)" if i % 2 == 0 else f"{base_job['title']} (Middle)"
            jobs_pool.append(padded_job)
        
    # 4. Job Distribution Logic
    print("\n=== ĐANG PHÂN BỔ 500 JOBS CHO 60 CÔNG TY ===")
    
    company_jobs_map = {comp_id: [] for comp_id, _, _ in companies}
    leftover_jobs = []
    
    # Match jobs by company name
    for job in jobs_pool:
        raw_name = job["company_name_raw"]
        matched_comp_id = None
        for comp_id, comp_name, comp_logo in companies:
            c1 = clean_company_name(raw_name)
            c2 = clean_company_name(comp_name)
            if c1 and c2 and (c1 in c2 or c2 in c1):
                matched_comp_id = comp_id
                break
                
        if matched_comp_id:
            company_jobs_map[matched_comp_id].append(job)
        else:
            leftover_jobs.append(job)
            
    # Print matching stats
    matched_count = sum(len(j) for j in company_jobs_map.values())
    print(f"Có {matched_count} jobs khớp trực tiếp với tên công ty trong DB.")
    print(f"Có {len(leftover_jobs)} jobs dư thừa sẽ được phân phối xoay vòng.")
    
    # Fill each company up to 8 jobs using leftovers
    leftover_idx = 0
    for comp_id, _, _ in companies:
        while len(company_jobs_map[comp_id]) < 8 and leftover_idx < len(leftover_jobs):
            company_jobs_map[comp_id].append(leftover_jobs[leftover_idx])
            leftover_idx += 1
            
    # Distribute remaining in round-robin until we have exactly 500 jobs total
    total_assigned = sum(len(j) for j in company_jobs_map.values())
    print(f"Tổng số jobs sau bước điền tối thiểu: {total_assigned}")
    
    while total_assigned < 500 and leftover_idx < len(leftover_jobs):
        for comp_id, _, _ in companies:
            if total_assigned >= 500:
                break
            company_jobs_map[comp_id].append(leftover_jobs[leftover_idx])
            leftover_idx += 1
            total_assigned += 1
            
    print(f"Tổng số jobs phân bổ cuối cùng: {sum(len(j) for j in company_jobs_map.values())} (Đã dùng {leftover_idx} jobs dư).")
    
    # 5. Connect to JobService DB
    try:
        conn_job = psycopg2.connect(host="localhost", port=5432, dbname="JobService", user="postgres", password="root")
        cur_job = conn_job.cursor()
    except Exception as e:
        print(f"❌ Lỗi kết nối JobService DB: {e}")
        sys.exit(1)
        
    # Truncate tables for fresh seed
    print("🧹 Đang làm sạch bảng Jobs và JobSkills cũ...")
    cur_job.execute('DELETE FROM "JobSkills"')
    cur_job.execute('DELETE FROM "SavedJobs"')
    cur_job.execute('DELETE FROM "Jobs"')
    conn_job.commit()
    
    # Query all skills to build a mapper
    skill_map = {}
    cur_job.execute('SELECT "Id", "Name" FROM "Skills"')
    for sid, sname in cur_job.fetchall():
        skill_map[sname.lower().strip()] = sid
        
    print(f"Đã tải {len(skill_map)} kỹ năng phục vụ so khớp.")
    
    # 6. Bulk Insert Jobs
    print("🚀 Đang tiến hành chèn 500 Jobs vào database...")
    
    job_insert_count = 0
    job_skills_to_insert = []
    
    now = datetime.now(timezone.utc)
    
    levels_list = ["INTERN", "FRESHER", "JUNIOR", "MIDDLE", "SENIOR", "LEADER", "MANAGER"]
    job_types_list = ["FULL_TIME", "PART_TIME", "REMOTE", "HYBRID", "INTERNSHIP"]
    
    for comp_id, comp_name, comp_logo in companies:
        hr_user_id = company_hr_map.get(comp_id)
        if not hr_user_id:
            # Fallback if HR account was not created successfully
            continue
            
        jobs_to_seed = company_jobs_map[comp_id]
        
        for job in jobs_to_seed:
            job_id = str(uuid.uuid4())
            job_name = job["title"]
            location = job["location"]
            benefits = job["benefits"]
            
            # Map level & job type based on title
            level = "MIDDLE"
            title_lower = job_name.lower()
            if "intern" in title_lower: level = "INTERN"
            elif "fresher" in title_lower: level = "FRESHER"
            elif "junior" in title_lower: level = "JUNIOR"
            elif "middle" in title_lower: level = "MIDDLE"
            elif "senior" in title_lower: level = "SENIOR"
            elif "leader" in title_lower or "lead" in title_lower: level = "LEADER"
            elif "manager" in title_lower: level = "MANAGER"
            else: level = random.choice(["JUNIOR", "MIDDLE", "SENIOR"])
                
            job_type = "FULL_TIME"
            if "part time" in title_lower or "part-time" in title_lower: job_type = "PART_TIME"
            elif "remote" in title_lower: job_type = "REMOTE"
            elif "hybrid" in title_lower: job_type = "HYBRID"
            elif "internship" in title_lower or "intern" in title_lower: job_type = "INTERNSHIP"
            else: job_type = random.choice(["FULL_TIME", "FULL_TIME", "HYBRID", "REMOTE"])
                
            # Random Salary
            salary_min = random.choice([500, 800, 1000, 1200, 1500, 2000, 2500])
            salary_max = salary_min + random.choice([300, 500, 800, 1000, 1500, 2000])
            is_negotiable = random.choice([True, False, False])
            
            quantity = random.randint(1, 5)
            exp_required = "1-3 năm kinh nghiệm" if level in ["JUNIOR", "MIDDLE"] else "Không yêu cầu kinh nghiệm" if level in ["INTERN", "FRESHER"] else "5+ năm kinh nghiệm"
            
            # Build Description and Requirements
            skills_str = ", ".join(job["skills"]) if job["skills"] else "Lập trình & Phát triển phần mềm"
            description = f"Chúng tôi cần tuyển vị trí {job_name} để làm việc trực tiếp trong dự án cốt lõi của công ty. Bạn sẽ tham gia vào toàn bộ vòng đời sản phẩm từ thiết kế đến triển khai hệ thống."
            requirements = f"Yêu cầu có kinh nghiệm thực tế tốt với các công nghệ liên quan: {skills_str}. Có tư duy giải quyết vấn đề tốt, trách nhiệm cao và kỹ năng giao tiếp phối hợp tốt."
            
            # StartDate & EndDate
            start_date = now
            end_date = now + timedelta(days=random.randint(15, 45))
            category = job["skills"][0] if job["skills"] else "Software Development"
            
            # Insert Job
            try:
                cur_job.execute('''
                    INSERT INTO "Jobs" (
                        "Id", "CompanyId", "CompanyName", "CompanyLogo", "CustomerId",
                        "Name", "Location", "SalaryMin", "SalaryMax", "SalaryCurrency",
                        "IsSalaryNegotiable", "Quantity", "Level", "JobType", "ExperienceRequired",
                        "Description", "Requirements", "Benefits", "Status", "StartDate", "EndDate",
                        "CreatedDate", "LastModifiedDate", "CreatedBy", "LastModifiedBy", "IsDeleted", "ViewCount", "Category"
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s
                    )
                ''', (
                    job_id, comp_id, comp_name, comp_logo, hr_user_id,
                    job_name, location, float(salary_min), float(salary_max), "USD",
                    is_negotiable, quantity, level, job_type, exp_required,
                    description, requirements, benefits, "PUBLISHED", start_date, end_date,
                    now, now, "Seeder", "Seeder", False, random.randint(5, 400), category
                ))
                job_insert_count += 1
                
                # Skill mappings
                for tag in job["skills"]:
                    clean_tag = tag.lower().strip()
                    # Standardized ITviec tag mapping
                    tag_mappings = {
                        'reactjs': 'react',
                        'golang': 'go (golang)',
                        '.net': 'c#',
                        'net': 'c#',
                        'nodejs': 'node.js',
                        'node.js': 'node.js',
                        'vuejs': 'vue.js',
                        'vue': 'vue.js',
                        'angularjs': 'angular',
                        'c++': 'c/c++',
                        'c': 'c/c++',
                        'aws': 'aws ec2',
                        'gcp': 'google cloud platform (gcp)',
                        'azure': 'microsoft azure',
                        'kubernetes': 'kubernetes',
                        'k8s': 'kubernetes',
                        'qa': 'testing',
                        'tester': 'testing',
                        'test': 'testing',
                        'sql server': 'microsoft sql server',
                        'mssql': 'microsoft sql server',
                        'django': 'django',
                        'flask': 'flask',
                        'spring boot': 'java spring boot',
                        'spring': 'java spring boot',
                        'react-native': 'react native',
                        'nextjs': 'next.js',
                        'nuxtjs': 'nuxt.js',
                        'express': 'express.js',
                        'nestjs': 'nestjs',
                        'laravel': 'laravel',
                        'fastapi': 'fastapi',
                        'ml': 'machine learning',
                        'dl': 'deep learning',
                        'nlp': 'natural language processing (nlp)',
                        'ai': 'generative ai',
                        'microservices': 'microservices architecture',
                        'restful': 'rest api',
                        'rest': 'rest api',
                        'rabbitmq': 'rabbitmq',
                        'ef': 'entity framework core',
                    }
                    if clean_tag in tag_mappings:
                        clean_tag = tag_mappings[clean_tag]
                    
                    if clean_tag in skill_map:
                        skill_id = skill_map[clean_tag]
                        job_skills_to_insert.append((job_id, skill_id))
                        
            except Exception as e:
                print(f"❌ Lỗi khi chèn Job {job_name}: {e}")
                continue
                
    conn_job.commit()
    print(f"✅ Đã lưu {job_insert_count} Jobs thành công.")
    
    # Bulk insert JobSkills
    print("🚀 Đang liên kết các kỹ năng vào JobSkills...")
    job_skill_success = 0
    unique_job_skills = set(job_skills_to_insert)
    for jid, sid in unique_job_skills:
        try:
            cur_job.execute('INSERT INTO "JobSkills" ("JobId", "SkillId") VALUES (%s, %s) ON CONFLICT DO NOTHING', (jid, sid))
            conn_job.commit()
            job_skill_success += 1
        except Exception as e:
            conn_job.rollback()
            print(f"  [Warning] Lỗi chèn kỹ năng ({jid}, {sid}): {e}")
            
    print(f"✅ Đã liên kết {job_skill_success} bản ghi kỹ năng thành công.")
    
    cur_job.close()
    conn_job.close()
    
    print("\n=== KẾT QUẢ SEEDING HOÀN TẤT ===")
    print(f"Số lượng tài khoản HR hoạt động: {len(company_hr_map)}")
    print(f"Số lượng Jobs được chèn thành công: {job_insert_count}")

if __name__ == "__main__":
    main()
