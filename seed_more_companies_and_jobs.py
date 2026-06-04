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

# Database connection config
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

def generate_100_companies():
    print("\n=== ĐANG TẠO THÔNG TIN 100 CÔNG TY MỚI ===")
    
    prefixes = ['Apex', 'Blue', 'Cloud', 'Delta', 'Eco', 'Forte', 'Genesis', 'Helix', 'Intellect', 'Jet', 'Krypton', 'Lumina', 'Matrix', 'Nova', 'Omni', 'Prime', 'Quantum', 'Rift', 'Sigma', 'Titan', 'Ultra', 'Vertex', 'Wave', 'Zenith', 'Smart', 'Global', 'Cyber', 'Data', 'Nexus', 'Vina', 'Saigon', 'Hanoi', 'Mekong', 'SongHong', 'Viet']
    suffixes = ['Software', 'Solutions', 'Systems', 'Tech', 'Digital', 'Technologies', 'Labs', 'Analytics', 'Consulting', 'Hub', 'Innovation', 'Networks', 'Code', 'Soft', 'Intelligence', 'Media', 'Works', 'Space']
    
    # Query existing company names to avoid collisions
    try:
        conn = psycopg2.connect(host=DB_CONFIG["host"], port=DB_CONFIG["port"], dbname="CompanyService", user=DB_CONFIG["user"], password=DB_CONFIG["password"])
        cur = conn.cursor()
        cur.execute('SELECT "Name" FROM "Companies"')
        existing_names = {r[0].lower().strip() for r in cur.fetchall()}
        cur.close()
        conn.close()
    except Exception as e:
        print(f"  [Warning] Không lấy được danh sách công ty cũ: {e}")
        existing_names = set()
        
    new_companies = []
    generated_names = set()
    random.seed(2026)
    
    attempts = 0
    while len(new_companies) < 100 and attempts < 2000:
        attempts += 1
        p = random.choice(prefixes)
        s = random.choice(suffixes)
        suffix2 = ""
        if random.random() < 0.3:
            suffix2 = " Vietnam" if random.random() < 0.5 else " Global"
        name = f"{p} {s}{suffix2}"
        
        name_lower = name.lower().strip()
        if name_lower not in existing_names and name_lower not in generated_names:
            generated_names.add(name_lower)
            
            comp_id = str(uuid.uuid4())
            slug = make_slug(name).replace(".", "-")
            website = f"https://www.{slug}.com"
            email = f"contact@{slug}.com"
            tax_code = "".join([str(random.randint(0, 9)) for _ in range(10)])
            size = random.choice(['STARTUP', 'SME', 'ENTERPRISE'])
            industry = random.choice(['Software Outsourcing', 'Product Development', 'Fintech Solutions', 'AI & Data Analytics', 'E-commerce Platform', 'Game Development'])
            address = random.choice([
                "Duy Tân, Cầu Giấy, Hà Nội",
                "Nguyễn Chí Thanh, Đống Đa, Hà Nội",
                "Lê Đại Hành, Quận 11, TP. Hồ Chí Minh",
                "Nguyễn Huệ, Quận 1, TP. Hồ Chí Minh",
                "Hàm Nghi, Thanh Khê, Đà Nẵng",
                "3 Tháng 2, Ninh Kiều, Cần Thơ"
            ])
            logo = f"https://picsum.photos/id/{random.randint(10, 200)}/100/100"
            cover = f"https://picsum.photos/id/{random.randint(10, 200)}/800/400"
            desc = f"Chúng tôi là {name}, đơn vị đi đầu trong lĩnh vực {industry.lower()}. Chúng tôi tập trung vào việc cung cấp các giải pháp chất lượng cao cho khách hàng trong nước và quốc tế."
            
            new_companies.append({
                "id": comp_id,
                "name": name,
                "website": website,
                "email": email,
                "tax_code": tax_code,
                "size": size,
                "industry": industry,
                "address": address,
                "logo": logo,
                "cover": cover,
                "description": desc
            })
            
    print(f"Đã tạo danh sách {len(new_companies)} công ty mới độc nhất.")
    return new_companies

def seed_companies_to_db(companies):
    print("\n=== ĐANG LƯU 100 CÔNG TY VÀO DATABASE ===")
    try:
        conn = psycopg2.connect(host=DB_CONFIG["host"], port=DB_CONFIG["port"], dbname="CompanyService", user=DB_CONFIG["user"], password=DB_CONFIG["password"])
        cur = conn.cursor()
        
        for c in companies:
            cur.execute('''
                INSERT INTO "Companies" (
                    "Id", "Name", "Description", "Address", "Logo", "CoverImage", "Industry",
                    "Website", "ContactEmail", "TaxCode", "CompanySize", "IsVerified", "IsDeleted",
                    "CreatedDate", "LastModifiedDate", "CreatedBy", "LastModifiedBy", "ActivityImages"
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    NOW(), NOW(), 'CompanySeeder', 'CompanySeeder', '[]'::jsonb
                )
            ''', (
                c["id"], c["name"], c["description"], c["address"], c["logo"], c["cover"], c["industry"],
                c["website"], c["email"], c["tax_code"], c["size"], True, False
            ))
            
        conn.commit()
        print(f"✅ Đã chèn thành công {len(companies)} công ty mới.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Lỗi khi chèn công ty: {e}")
        sys.exit(1)

def seed_hr_accounts(companies):
    print("\n=== ĐANG SEED TÀI KHOẢN HR CHO CÁC CÔNG TY MỚI ===")
    auth_conn = psycopg2.connect(host=DB_CONFIG["host"], port=DB_CONFIG["port"], dbname="AuthService", user=DB_CONFIG["user"], password=DB_CONFIG["password"])
    profile_conn = psycopg2.connect(host=DB_CONFIG["host"], port=DB_CONFIG["port"], dbname="ProfileService", user=DB_CONFIG["user"], password=DB_CONFIG["password"])
    
    auth_cur = auth_conn.cursor()
    profile_cur = profile_conn.cursor()
    
    company_hr_map = {}
    
    for idx, c in enumerate(companies, 1):
        slug = make_slug(c["name"]).replace(".", "_")
        email = f"hr.{slug}@jobhub.vn"
        username = f"HR {c['name']}"
        comp_id = c["id"]
        
        # Register via HTTP to trigger event-driven handlers
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
        except Exception:
            # Fallback direct DB query if gateway is down
            auth_cur.execute('SELECT "Id" FROM "AppUsers" WHERE "Email" = %s', (email.lower().strip(),))
            row = auth_cur.fetchone()
            if row:
                user_id = row[0]
            else:
                print(f"  ❌ Lỗi kết nối đăng ký {email}")
                continue
                
        if not user_id:
            print(f"  ❌ Không lấy được User ID cho {email}")
            continue
            
        company_hr_map[comp_id] = user_id
        
        # Activate in AuthService
        try:
            auth_cur.execute('UPDATE "AppUsers" SET "Status" = \'Active\' WHERE "Id" = %s', (user_id,))
            auth_conn.commit()
        except Exception as e:
            auth_conn.rollback()
            print(f"  ❌ Lỗi kích hoạt HR {email}: {e}")
            continue
            
        # Update Profile in ProfileService Customers table
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
                profile_cur.execute('''
                    INSERT INTO "Customers" ("Id", "AppUserId", "Type", "FullName", "CreatedDate", "CreatedBy", "IsDeleted", "CompanyId")
                    VALUES (%s, %s, 'EMPLOYER', %s, NOW(), 'Seeder', false, %s)
                ''', (user_id, user_id, username, comp_id))
                profile_conn.commit()
            else:
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
            
        if idx % 20 == 0 or idx == len(companies):
            print(f"  -> Đã seed xong {idx}/{len(companies)} tài khoản HR.")
            
    auth_cur.close()
    auth_conn.close()
    profile_cur.close()
    profile_conn.close()
    
    print("✅ Hoàn thành Seeding tài khoản HR.")
    return company_hr_map

def crawl_more_jobs():
    print("\n=== CÀO TIN TUYỂN DỤNG THÊM TỪ ITVIEC (TRANG 4-6) ===")
    
    keywords = [
        'react-native', 'reactjs', 'nodejs', 'java', 'python', 'golang', 'tester', 'qa', 'devops', 
        'android', 'ios', 'php', 'angular', 'vuejs', 'typescript', 'javascript', 'aws', 'docker'
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Query existing jobs in database to prevent overlap
    try:
        conn = psycopg2.connect(host=DB_CONFIG["host"], port=DB_CONFIG["port"], dbname="JobService", user=DB_CONFIG["user"], password=DB_CONFIG["password"])
        cur = conn.cursor()
        cur.execute('SELECT "CompanyName", "Name" FROM "Jobs"')
        existing_jobs = {(r[0].lower().strip(), r[1].lower().strip()) for r in cur.fetchall()}
        cur.close()
        conn.close()
        print(f"Đã tải {len(existing_jobs)} jobs hiện tại để lọc trùng.")
    except Exception as e:
        print(f"  [Warning] Không tải được danh sách jobs cũ: {e}")
        existing_jobs = set()
        
    unique_jobs = {}
    page = 4
    
    while len(unique_jobs) < 550 and page <= 6:
        print(f"\n[Crawler] --- ĐANG CÀO TRANG {page} ---")
        for kw in keywords:
            if len(unique_jobs) >= 550:
                break
                
            url = f"https://itviec.com/it-jobs/{kw}?page={page}"
            print(f"[Crawler] Đang quét: {url} (Mới thu thập thêm: {len(unique_jobs)} jobs)")
            
            try:
                time.sleep(random.uniform(0.3, 0.7))
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(res.text, 'html.parser')
                cards = soup.find_all(class_=lambda x: x and 'job-card' in x)
                real_cards = [c for c in cards if 'segment-job-card' not in ' '.join(c.get('class', []))]
                
                for card in real_cards:
                    if len(unique_jobs) >= 550:
                        break
                        
                    # Job Title
                    title_el = card.find(attrs={"data-search--job-selection-target": "jobTitle"}) or card.find('h3') or card.find('h2')
                    if not title_el:
                        continue
                    title = title_el.text.strip()
                    
                    # Company Name
                    company_el = card.find('a', class_='text-rich-grey') or card.find(class_='text-hover-underline')
                    if not company_el:
                        continue
                    company_name = company_el.text.strip()
                    
                    job_key = (company_name.lower().strip(), title.lower().strip())
                    if job_key in existing_jobs or job_key in unique_jobs:
                        continue
                        
                    # Location
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
                                location = loc_div.text.strip()
                                
                    # Skills
                    skills = []
                    tag_list_div = card.find('div', attrs={"data-controller": "responsive-tag-list"})
                    if tag_list_div:
                        skills = [a.text.strip() for a in tag_list_div.find_all('a')]
                        
                    # Benefits
                    benefits_list = []
                    benefits_div = card.find('div', class_=lambda x: x and 'small-text' in x and 'text-it-black' in x)
                    if benefits_div:
                        benefits_list = [li.text.strip() for li in benefits_div.find_all('li')]
                    benefits_str = "\n".join([f"- {b}" for b in benefits_list]) if benefits_list else "- Chế độ lương thưởng cạnh tranh.\n- Cơ hội thăng tiến nghề nghiệp.\n- Môi trường làm việc năng động."
                    
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
        
    print(f"\n[Crawler] ✅ Đã hoàn thành cào! Tổng cộng thu thập thêm được: {len(unique_jobs)} jobs độc lập mới.")
    return list(unique_jobs.values())

def main():
    # 1. Generate 100 new companies
    companies = generate_100_companies()
    
    # 2. Insert companies to DB
    seed_companies_to_db(companies)
    
    # 3. Create 100 HR Accounts
    company_hr_map = seed_hr_accounts(companies)
    
    # 4. Crawl 500 new jobs
    jobs_pool = crawl_more_jobs()
    if len(jobs_pool) < 500:
        print(f"[Warning] Chỉ cào thêm được {len(jobs_pool)} jobs độc lập mới. Tiến hành nhân bản để đủ 500...")
        needed = 500 - len(jobs_pool)
        for i in range(needed):
            base_job = random.choice(jobs_pool)
            padded_job = base_job.copy()
            padded_job["title"] = f"{base_job['title']} (Senior)" if i % 2 == 0 else f"{base_job['title']} (Middle)"
            jobs_pool.append(padded_job)
            
    # 5. Distribute exactly 500 jobs evenly among 100 new companies (exactly 5 jobs per company)
    print("\n=== ĐANG PHÂN BỔ 500 JOBS CHO 100 CÔNG TY MỚI ===")
    company_jobs_map = {c["id"]: [] for c in companies}
    
    for idx, job in enumerate(jobs_pool[:500]):
        comp_id = companies[idx % 100]["id"]
        company_jobs_map[comp_id].append(job)
        
    print("Mỗi công ty mới nhận chính xác 5 jobs.")
    
    # 6. Connect to JobService DB
    try:
        conn_job = psycopg2.connect(host=DB_CONFIG["host"], port=DB_CONFIG["port"], dbname="JobService", user=DB_CONFIG["user"], password=DB_CONFIG["password"])
        cur_job = conn_job.cursor()
    except Exception as e:
        print(f"❌ Lỗi kết nối JobService DB: {e}")
        sys.exit(1)
        
    # Get skills map
    skill_map = {}
    cur_job.execute('SELECT "Id", "Name" FROM "Skills"')
    for sid, sname in cur_job.fetchall():
        skill_map[sname.lower().strip()] = sid
        
    # 7. Bulk Insert Jobs
    print("\n=== ĐANG CHÈN 500 JOBS MỚI VÀO DATABASE ===")
    job_insert_count = 0
    job_skills_to_insert = []
    
    now = datetime.now(timezone.utc)
    
    for c in companies:
        comp_id = c["id"]
        comp_name = c["name"]
        comp_logo = c["logo"]
        hr_user_id = company_hr_map.get(comp_id)
        if not hr_user_id:
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
                
                # Skills matching
                for tag in job["skills"]:
                    clean_tag = tag.lower().strip()
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
    print(f"✅ Đã lưu {job_insert_count} Jobs mới thành công.")
    
    # 8. Insert JobSkills safely
    print("\n=== ĐANG LIÊN KẾT KỸ NĂNG VÀO JOBSKILLS ===")
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
    
    print("\n=== KẾT QUẢ SEEDING BỔ SUNG HOÀN TẤT ===")
    print(f"Số lượng công ty mới chèn: {len(companies)}")
    print(f"Số lượng tài khoản HR mới kích hoạt: {len(company_hr_map)}")
    print(f"Số lượng Jobs mới được chèn thành công: {job_insert_count}")

if __name__ == "__main__":
    main()
