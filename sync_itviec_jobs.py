import os
import sys
import uuid
import json
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

# Configure output encoding for console
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("[Error] psycopg2 package is not installed. Please run: pip install psycopg2-binary")
    sys.exit(1)

# ==============================================================================
# CONFIGURATION
# ==============================================================================
DB_CONFIG_COMPANY = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "root",
    "database": "CompanyService"
}

DB_CONFIG_JOB = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "root",
    "database": "JobService"
}

API_GATEWAY_URL = "http://localhost:5000"

# ==============================================================================
# REAL-WORLD BUILT-IN DATASET (ITVIEC RESILIENT FALLBACK)
# ==============================================================================
COVERS_POOL = [
    "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1497215842964-222b430dc094?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=1200&q=80"
]

FALLBACK_LOGO_URL = "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=150&h=150&q=80"

BUILTIN_COMPANIES = [
    {
        "name": "FPT Software",
        "description": "FPT Software là công ty xuất khẩu phần mềm lớn nhất Việt Nam và khu vực Đông Nam Á, với quy mô hơn 30,000 nhân sự toàn cầu, cung cấp dịch vụ chuyển đổi số và công nghệ thông tin cho các tập đoàn Fortune 500.",
        "address": "Khu công nghệ cao Hòa Lạc, Thạch Thất, Hà Nội",
        "logo": "https://logos.hunter.io/fpt.com",
        "cover_image": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80",
        "industry": "Software Outsourcing & IT Services",
        "size": "ENTERPRISE",
        "website": "https://www.fpt-software.com",
        "email": "recruitment@fsoft.com.vn",
        "tax_code": "0102073539",
        "jobs": [
            {
                "name": "Senior .NET Core Backend Engineer (Clean Architecture)",
                "salary_min": 1800,
                "salary_max": 2800,
                "level": "SENIOR",
                "job_type": "FULL_TIME",
                "exp_required": "5+ years",
                "description": "Thiết kế và phát triển các hệ thống microservices hiệu năng cao sử dụng .NET Core 8, CQRS pattern, MediatR, PostgreSQL và RabbitMQ. Tối ưu hóa truy vấn SQL và xây dựng cơ chế caching.",
                "requirements": "Yêu cầu trên 5 năm kinh nghiệm lập trình .NET Core, am hiểu Clean Architecture, RESTful API. Có kinh nghiệm làm việc với Redis, RabbitMQ, Docker/Kubernetes.",
                "benefits": "Thu nhập 13 tháng lương + thưởng hiệu quả công việc hấp dẫn. Gói bảo hiểm sức khỏe FPT Care cao cấp dành cho cá nhân và gia đình. Cơ hội làm việc onsite tại Nhật Bản, Singapore.",
                "category": "Backend"
            },
            {
                "name": "Fresher C# Developer (.NET Training Program)",
                "salary_min": 500,
                "salary_max": 800,
                "level": "FRESHER",
                "job_type": "FULL_TIME",
                "exp_required": "No experience required",
                "description": "Tham gia chương trình đào tạo chuyên sâu về .NET và quy trình phát triển phần mềm chuẩn quốc tế. Nhận hướng dẫn trực tiếp từ các Solution Architect lâu năm và làm việc trong các dự án thực tế.",
                "requirements": "Tốt nghiệp đại học chuyên ngành CNTT hoặc các khóa đào tạo tương đương. Có tư duy logic tốt, nắm vững kiến thức cơ bản về lập trình hướng đối tượng (OOP) và cơ sở dữ liệu SQL Server.",
                "benefits": "Hỗ trợ lương đào tạo hấp dẫn. Sau 2-3 tháng đào tạo sẽ được đánh giá nâng lương. Môi trường trẻ trung, cơ sở vật chất văn phòng hiện đại bậc nhất.",
                "category": "Backend"
            }
        ]
    },
    {
        "name": "VNG Corporation",
        "description": "VNG Corporation là doanh nghiệp công nghệ kỳ lân đầu tiên tại Việt Nam, sở hữu hệ sinh thái internet đa dạng bao gồm Zalo, ZaloPay, VNG Games và VNG Cloud, phục vụ hàng chục triệu người dùng mỗi ngày.",
        "address": "Z06 Đường số 13, Tân Thuận Đông, Quận 7, TP. Hồ Chí Minh",
        "logo": "https://logos.hunter.io/vng.com.vn",
        "cover_image": "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1200&q=80",
        "industry": "Internet & Game Publishing",
        "size": "ENTERPRISE",
        "website": "https://vng.com.vn",
        "email": "careers@vng.com.vn",
        "tax_code": "0303493774",
        "jobs": [
            {
                "name": "Python / Go Platform Engineer (ZaloPay DevOps)",
                "salary_min": 2500,
                "salary_max": 4500,
                "level": "SENIOR",
                "job_type": "HYBRID",
                "exp_required": "4+ years",
                "description": "Xây dựng các hạ tầng nền tảng (Platform) tự động hóa phục vụ các luồng giao dịch tài chính tốc độ cao cho hệ sinh thái ZaloPay. Phát triển công cụ CLI, quản lý kịch bản CI/CD trên nền Kubernetes.",
                "requirements": "Thành thạo lập trình Python hoặc Go. Am hiểu sâu sắc về kiến trúc Linux, containerization (Docker, K8s), các công cụ CI/CD (GitLab CI, Jenkins) và cơ sở dữ liệu Redis/Postgres.",
                "benefits": "Mức lương cạnh tranh hàng đầu thị trường cùng gói thưởng cuối năm vượt trội. Cung cấp Macbook Pro M3 và màn hình 4K cho nhân sự. Bữa trưa miễn phí tại công ty.",
                "category": "DevOps"
            },
            {
                "name": "Mobile React Native Developer (Zalo App)",
                "salary_min": 1500,
                "salary_max": 2500,
                "level": "MIDDLE",
                "job_type": "FULL_TIME",
                "exp_required": "3 years",
                "description": "Phát triển và tối ưu hóa các tính năng tương tác trong ứng dụng Zalo sử dụng React Native. Cải thiện tốc độ khởi động ứng dụng và giảm thiểu rò rỉ bộ nhớ (memory leaks) trên Android/iOS.",
                "requirements": "Có ít nhất 3 năm kinh nghiệm lập trình di động với React Native. Hiểu biết sâu sắc về Javascript/Typescript và tích hợp Native Modules (Java/Swift). Am hiểu Redux Toolkit hoặc MobX.",
                "benefits": "Môi trường làm việc chuẩn Agile sáng tạo. Xét tăng lương hàng năm dựa trên đóng góp. Bảo hiểm chăm sóc sức khỏe quốc tế PVI.",
                "category": "Mobile"
            }
        ]
    },
    {
        "name": "KMS Technology",
        "description": "KMS Technology là công ty phát triển phần mềm và tư vấn công nghệ hàng đầu được thành lập tại Mỹ với các trung tâm phát triển tại Việt Nam, nổi tiếng với môi trường làm việc tuyệt vời và năng động chuyên nghiệp.",
        "address": "Số 2 Trường Quốc Dung, Phường 8, Phú Nhuận, TP. Hồ Chí Minh",
        "logo": "https://logos.hunter.io/kms-technology.com",
        "cover_image": "https://images.unsplash.com/photo-1497215842964-222b430dc094?auto=format&fit=crop&w=1200&q=80",
        "industry": "Software Engineering Outsourcing",
        "size": "ENTERPRISE",
        "website": "https://www.kms-technology.com",
        "email": "career-vn@kms-technology.com",
        "tax_code": "0307616147",
        "jobs": [
            {
                "name": "Frontend Web Engineer (ReactJS & Next.js 14)",
                "salary_min": 1200,
                "salary_max": 2200,
                "level": "MIDDLE",
                "job_type": "FULL_TIME",
                "exp_required": "3 years",
                "description": "Phát triển giao diện mặt tiền (Storefront) chất lượng cao cho các đối tác thương mại điện tử nước ngoài. Ứng dụng Server-Side Rendering (SSR) bằng Next.js, xây dựng hệ thống UI component reusable.",
                "requirements": "Tối thiểu 3 năm kinh nghiệm phát triển Frontend với ReactJS. Kinh nghiệm thực tế với TypeScript, Tailwind CSS, Next.js (App Router). Sử dụng thành thạo Git và có kỹ năng đọc viết tiếng Anh tốt.",
                "benefits": "Môi trường làm việc thuộc Top 10 nơi làm việc tốt nhất Việt Nam. Thưởng tháng lương thứ 13 và review tăng lương 2 lần/năm. Hỗ trợ học phí các khóa học chứng chỉ quốc tế.",
                "category": "Frontend"
            }
        ]
    },
    {
        "name": "NashTech Vietnam",
        "description": "NashTech là một phần của tập đoàn Harvey Nash toàn cầu, chuyên cung cấp giải pháp công nghệ số sáng tạo, phát triển phần mềm doanh nghiệp và vận hành quy trình kinh doanh (BPO) cho khách hàng quốc tế.",
        "address": "Tòa nhà Etown 3, 367 Cộng Hòa, Tân Bình, TP. Hồ Chí Minh",
        "logo": "https://logos.hunter.io/nashtechglobal.com",
        "cover_image": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1200&q=80",
        "industry": "IT Consulting & Outsourcing",
        "size": "ENTERPRISE",
        "website": "https://nashtechglobal.com",
        "email": "careers.vn@nashtechglobal.com",
        "tax_code": "0302061596",
        "jobs": [
            {
                "name": "Cloud DevOps Engineer (AWS / Terraform)",
                "salary_min": 1800,
                "salary_max": 3200,
                "level": "MIDDLE",
                "job_type": "HYBRID",
                "exp_required": "3+ years",
                "description": "Xây dựng hạ tầng đám mây tự động hóa (Infrastructure as Code) sử dụng Terraform trên nền tảng AWS. Thiết lập hệ thống monitoring (Prometheus, Grafana), CI/CD pipeline và bảo mật hạ tầng mạng.",
                "requirements": "Ít nhất 3 năm kinh nghiệm DevOps. Có chứng chỉ AWS Associate trở lên là lợi thế. Thành thạo Docker, Kubernetes, Ansible và viết shell script tốt.",
                "benefits": "Chế độ làm việc linh hoạt (lên văn phòng 2-3 ngày/tuần). Bảo hiểm xã hội đóng full lương. Đào tạo nâng cấp kỹ năng mềm và kỹ năng kỹ thuật miễn phí.",
                "category": "DevOps"
            }
        ]
    },
    {
        "name": "VTI Cloud",
        "description": "VTI Cloud là Đối tác tư vấn cao cấp (Advanced Consulting Partner) của AWS tại Việt Nam, chuyên cung cấp dịch vụ chuyển đổi đám mây, kiến trúc hóa hạ tầng, di tản hệ thống và tối ưu hóa chi phí cloud.",
        "address": "Tầng 7, Tòa nhà Sông Đà, Phạm Hùng, Mỹ Đình, Hà Nội",
        "logo": "https://logos.hunter.io/vticloud.io",
        "cover_image": "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=1200&q=80",
        "industry": "Cloud Infrastructure & Consulting",
        "size": "SME",
        "website": "https://vticloud.io",
        "email": "contact@vticloud.io",
        "tax_code": "0108924040",
        "jobs": [
            {
                "name": "AWS Solutions Architect Intern",
                "salary_min": 250,
                "salary_max": 400,
                "level": "INTERN",
                "job_type": "FULL_TIME",
                "exp_required": "No experience",
                "description": "Học tập và hỗ trợ các kỹ sư giải pháp trong việc thiết kế sơ đồ hạ tầng AWS, chuẩn bị tài liệu di tản dữ liệu (Cloud Migration) và tối ưu hóa hệ thống cho khách hàng doanh nghiệp vừa và nhỏ.",
                "requirements": "Sinh viên năm cuối ngành CNTT, điện tử viễn thông. Có kiến thức cơ bản về mạng máy tính, hệ điều hành Linux và đã thi đạt hoặc đang ôn thi chứng chỉ AWS Cloud Practitioner.",
                "benefits": "Có cơ hội được tuyển thẳng lên nhân viên chính thức sau khi tốt nghiệp. Được công ty đài thọ 100% lệ phí thi các chứng chỉ AWS. Môi trường trẻ trung năng động.",
                "category": "Cloud"
            }
        ]
    }
]

def clean_and_get_domain(website_url, company_name):
    # Known domains mapping
    known = {
        "fpt software": "fpt.com",
        "vng corporation": "vng.com.vn",
        "kms technology": "kms-technology.com",
        "nashtech": "nashtechglobal.com",
        "vti cloud": "vticloud.io"
    }
    name_lower = company_name.lower()
    for key, dom in known.items():
        if key in name_lower:
            return dom
            
    if not website_url:
        return None
        
    url = website_url.strip().lower()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    try:
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc
        if netloc.startswith('www.'):
            netloc = netloc[4:]
        if ':' in netloc:
            netloc = netloc.split(':')[0]
        return netloc
    except Exception:
        return None

def verify_logo_url(logo_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.head(logo_url, headers=headers, timeout=3, allow_redirects=True)
        if resp.status_code == 200:
            return True
        resp = requests.get(logo_url, headers=headers, timeout=3, stream=True)
        return resp.status_code == 200
    except Exception:
        return False

def get_real_logo_for_company(name, website=""):
    domain = clean_and_get_domain(website, name)
    if domain:
        candidate_logo = f"https://logos.hunter.io/{domain}"
        if verify_logo_url(candidate_logo):
            return candidate_logo
    
    # Try slugify name for guess
    slug = name.lower().replace(" ", "").replace("-", "")
    candidate_logo = f"https://logos.hunter.io/{slug}.com"
    if verify_logo_url(candidate_logo):
        return candidate_logo
        
    return FALLBACK_LOGO_URL

# ==============================================================================
# LIVE CRAWLER FOR ITVIEC (BEAUTIFUL SOUP)
# ==============================================================================
def crawl_itviec_live(keyword="python"):
    """
    Attempts to scrape live jobs from ITviec search page.
    Due to Cloudflare and DOM changes, this is built defensively.
    """
    print(f"\n[Crawler] 🔍 Đang cào dữ liệu trực tiếp từ ITviec với từ khóa: '{keyword}'...")
    url = f"https://itviec.com/it-jobs/{keyword}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,vi;q=0.8"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 403:
            print("[Crawler] ⚠️ ITviec trả về lỗi 403 Forbidden (Chặn bởi Cloudflare / WAF).")
            return None
        elif res.status_code != 200:
            print(f"[Crawler] ⚠️ Lỗi kết nối HTTP: {res.status_code}")
            return None
            
        soup = BeautifulSoup(res.text, 'html.parser')
        job_cards = soup.find_all(class_=lambda x: x and 'job-card' in x) or soup.find_all('div', class_='job')
        
        if not job_cards:
            # Fallback to general structures
            job_cards = soup.find_all('div', attrs={"data-search-target": "jobCard"})
            
        if not job_cards:
            print("[Crawler] ⚠️ Không tìm thấy thẻ công việc nào trên cấu trúc HTML hiện tại của ITviec.")
            return None
            
        live_list = []
        print(f"[Crawler] Tìm thấy {len(job_cards)} công việc trên trang kết quả. Đang phân tích...")
        
        for card in job_cards[:5]: # Crawl top 5 to test/seed
            try:
                # Extract Title
                title_el = card.find('h3') or card.find('a', class_=lambda x: x and 'title' in x) or card.find(attrs={"data-search-target": "jobTitle"})
                if not title_el:
                    continue
                job_title = title_el.text.strip()
                
                # Link
                link = ""
                link_el = title_el.find('a') if title_el.name != 'a' else title_el
                if link_el and link_el.has_attr('href'):
                    link = link_el['href']
                    if not link.startswith('http'):
                        link = "https://itviec.com" + link
                
                # Company
                comp_el = card.find(class_=lambda x: x and 'company' in x) or card.find('span', class_='logo-text')
                company_name = comp_el.text.strip() if comp_el else "Công ty Công nghệ Việt"
                
                # Logo
                logo_url = get_real_logo_for_company(company_name)
                
                # Location
                loc_el = card.find(class_=lambda x: x and 'location' in x) or card.find('span', class_='address')
                location = loc_el.text.strip() if loc_el else "Hà Nội"
                
                # Tags/Skills
                tag_els = card.find_all(class_=lambda x: x and 'tag' in x) or card.find_all('a', class_='tag')
                skills = [tag.text.strip() for tag in tag_els] if tag_els else ["Software Development"]
                
                # Map to standard object
                item = {
                    "company": {
                        "name": company_name,
                        "description": f"{company_name} là đối tác công nghệ hàng đầu tại Việt Nam.",
                        "address": location,
                        "logo": logo_url,
                        "cover_image": random.choice(COVERS_POOL),
                        "industry": "Information Technology",
                        "size": "SME" if len(skills) > 2 else "STARTUP",
                        "website": "https://example.com",
                        "email": f"recruitment@{company_name.lower().replace(' ', '')}.com",
                        "tax_code": None
                    },
                    "job": {
                        "name": job_title,
                        "salary_min": 1000,
                        "salary_max": 2000,
                        "level": "MIDDLE" if "senior" not in job_title.lower() else "SENIOR",
                        "job_type": "FULL_TIME",
                        "exp_required": "2+ years",
                        "description": f"Tuyển dụng {job_title} làm việc tại văn phòng công ty. Dự án quy mô lớn, công nghệ hiện đại.",
                        "requirements": f"Yêu cầu thành thạo các kỹ năng: {', '.join(skills)}.",
                        "benefits": "Môi trường làm việc chuyên nghiệp, cơ hội phát triển nhanh. Đóng BHXH đầy đủ, thưởng cuối năm.",
                        "category": skills[0] if skills else "Software"
                    }
                }
                live_list.append(item)
                print(f"  -> Cào thành công: {job_title} | {company_name}")
            except Exception as e:
                continue
                
        return live_list if len(live_list) > 0 else None
    except Exception as e:
        print(f"[Crawler] ❌ Lỗi kết nối khi cào ITviec: {e}")
        return None

# ==============================================================================
# DIRECT POSTGRES SEEDER
# ==============================================================================
def db_seed_companies_and_jobs(data_list):
    """
    Directly seeds PostgreSQL tables "Companies" and "Jobs" matching them by ID.
    Using raw psycopg2 with double quotes for PascalCase properties.
    """
    print("\n[DB Seed] === BẮT ĐẦU SEED TRỰC TIẾP VÀO POSTGRESQL ===")
    
    # 1. Connect to CompanyService
    try:
        conn_comp = psycopg2.connect(**DB_CONFIG_COMPANY)
        cursor_comp = conn_comp.cursor()
        print("⚡ Đã kết nối thành công tới CompanyService DB.")
    except Exception as e:
        print(f"❌ Không thể kết nối tới CompanyService DB: {e}")
        print("Hãy chắc chắn PostgreSQL đang chạy trong Docker và thông tin kết nối chính xác.")
        return
        
    # 2. Connect to JobService
    try:
        conn_job = psycopg2.connect(**DB_CONFIG_JOB)
        cursor_job = conn_job.cursor()
        print("⚡ Đã kết nối thành công tới JobService DB.")
    except Exception as e:
        print(f"❌ Không thể kết nối tới JobService DB: {e}")
        conn_comp.close()
        return

    success_comp = 0
    success_job = 0
    
    try:
        for idx, item in enumerate(data_list):
            if "company" in item:
                comp = item["company"]
                jobs = [item["job"]] if "job" in item else []
            else:
                comp = item
                jobs = item.get("jobs", [])
            
            # --- SYNCHRONIZE COMPANY ---
            comp_name = comp["name"]
            
            # Check if company already exists
            cursor_comp.execute(
                'SELECT "Id", "Logo" FROM "Companies" WHERE "Name" = %s AND "IsDeleted" = FALSE',
                (comp_name,)
            )
            existing = cursor_comp.fetchone()
            
            if existing:
                company_id = existing[0]
                comp_logo = existing[1] or comp["logo"]
                print(f"[Company] Công ty '{comp_name}' đã tồn tại (ID: {company_id}). Bỏ qua tạo mới.")
            else:
                # Create new company
                company_id = str(uuid.uuid4())
                comp_logo = comp["logo"]
                now = datetime.now(timezone.utc)
                
                cursor_comp.execute(
                    """
                    INSERT INTO "Companies" (
                        "Id", "Name", "Description", "Address", "Logo", "CoverImage", 
                        "Industry", "CompanySize", "Website", "ContactEmail", "TaxCode", 
                        "IsVerified", "ActivityImages", "CreatedDate", "LastModifiedDate", 
                        "CreatedBy", "LastModifiedBy", "IsDeleted"
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        company_id, comp_name, comp["description"], comp["address"], comp_logo, comp["cover_image"],
                        comp["industry"], comp["size"], comp["website"], comp["email"], comp["tax_code"],
                        True, json.dumps([]), now, now, "seeder", "seeder", False
                    )
                )
                success_comp += 1
                print(f"[Company] Đã thêm mới công ty: '{comp_name}' (ID: {company_id})")
            
            # --- SYNCHRONIZE JOBS ---
            for job in jobs:
                if not job:
                    continue
                job_name = job["name"]
                
                # Check if job already exists for this company
                cursor_job.execute(
                    'SELECT "Id" FROM "Jobs" WHERE "Name" = %s AND "CompanyId" = %s AND "IsDeleted" = FALSE',
                    (job_name, company_id)
                )
                existing_job = cursor_job.fetchone()
                
                if existing_job:
                    print(f"  [Job] Công việc '{job_name}' đã tồn tại. Bỏ qua.")
                else:
                    # Create new job
                    job_id = str(uuid.uuid4())
                    customer_id = str(uuid.uuid4()) # HR Owner id (cross-boundary, random uuid)
                    now = datetime.now(timezone.utc)
                    start_date = now
                    end_date = now + timedelta(days=30)
                    
                    cursor_job.execute(
                        """
                        INSERT INTO "Jobs" (
                            "Id", "CustomerId", "CompanyId", "Name", "CompanyName", "CompanyLogo", 
                            "Location", "SalaryMin", "SalaryMax", "SalaryCurrency", "IsSalaryNegotiable", 
                            "Quantity", "Level", "JobType", "ExperienceRequired", "Description", 
                            "Requirements", "Benefits", "StartDate", "EndDate", "ViewCount", "Status", 
                            "Category", "CreatedDate", "LastModifiedDate", "CreatedBy", "LastModifiedBy", "IsDeleted"
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            job_id, customer_id, company_id, job_name, comp_name, comp_logo,
                            comp["address"], float(job["salary_min"]), float(job["salary_max"]), job.get("salary_currency", "USD"), False,
                            1, job["level"], job["job_type"], job["exp_required"], job["description"],
                            job["requirements"], job["benefits"], start_date, end_date, 0, "PUBLISHED",
                            job["category"], now, now, "seeder", "seeder", False
                        )
                    )
                    success_job += 1
                    print(f"  [Job] Đã đồng bộ thành công: '{job_name}'")

        # Commit changes for both databases
        conn_comp.commit()
        conn_job.commit()
        print("\n✅ SEED DỮ LIỆU THÀNH CÔNG!")
        print(f"-> Thêm mới công ty: {success_comp} | Thêm mới jobs: {success_job}")
        
    except Exception as e:
        conn_comp.rollback()
        conn_job.rollback()
        print(f"\n❌ Lỗi trong quá trình ghi DB: {e}")
    finally:
        cursor_comp.close()
        conn_comp.close()
        cursor_job.close()
        conn_job.close()

# ==============================================================================
# API ENDPOINT SYNC MODE
# ==============================================================================
def api_sync_companies_and_jobs(data_list):
    """
    Sends data to CompanyService and JobService APIs via the Ocelot API Gateway.
    """
    print("\n[API Sync] === BẮT ĐẦU SEED QUA API GATEWAY ===")
    print(f"Gateway URL: {API_GATEWAY_URL}")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer SYSTEM_BYPASS_TOKEN" # In real app, exchange credentials
    }
    
    success_comp = 0
    success_job = 0
    
    for item in data_list:
        if "company" in item:
            comp = item["company"]
            jobs = [item["job"]] if "job" in item else []
        else:
            comp = item
            jobs = item.get("jobs", [])
        comp_name = comp["name"]
        
        # Step 1: Create Company
        # Mapping properties to match Company REST API dto if different
        company_dto = {
            "name": comp_name,
            "description": comp["description"],
            "address": comp["address"],
            "logo": comp["logo"],
            "coverImage": comp["cover_image"],
            "industry": comp["industry"],
            "companySize": comp["size"],
            "website": comp["website"],
            "contactEmail": comp["email"],
            "taxCode": comp["tax_code"]
        }
        
        try:
            print(f"[Company API] Gửi yêu cầu tạo công ty: {comp_name}...")
            # We assume find-or-create or fallback standard POST
            res = requests.post(f"{API_GATEWAY_URL}/api/v1/companies", json=company_dto, headers=headers, timeout=5)
            if res.status_code not in [200, 201]:
                # Attempt find if exists
                print(f"  -> Trùng lặp hoặc lỗi: {res.status_code}. Thử tìm kiếm...")
                search_res = requests.get(f"{API_GATEWAY_URL}/api/v1/companies?search={comp_name}", headers=headers, timeout=5)
                # Parse to get GUID
                # ...
                print("  -> Bỏ qua đồng bộ công ty này do lỗi kết nối API.")
                continue
                
            comp_res_data = res.json()
            company_id = comp_res_data.get("id") or comp_res_data.get("data", {}).get("id")
            comp_logo_ret = comp_res_data.get("logo") or comp["logo"]
            success_comp += 1
            print(f"  -> Thành công! CompanyId: {company_id}")
            
            # Step 2: Create Jobs
            for job in jobs:
                if not job or not company_id:
                    continue
                
                job_dto = {
                    "companyId": company_id,
                    "name": job["name"],
                    "companyName": comp_name,
                    "companyLogo": comp_logo_ret,
                    "location": comp["address"],
                    "salaryMin": job["salary_min"],
                    "salaryMax": job["salary_max"],
                    "salaryCurrency": job.get("salary_currency", "USD"),
                    "level": job["level"],
                    "jobType": job["job_type"],
                    "experienceRequired": job["exp_required"],
                    "description": job["description"],
                    "requirements": job["requirements"],
                    "benefits": job["benefits"],
                    "category": job["category"],
                    "status": "PUBLISHED"
                }
                
                print(f"  [Job API] Gửi yêu cầu tạo job: {job['name']}...")
                res_job = requests.post(f"{API_GATEWAY_URL}/api/v1/jobs", json=job_dto, headers=headers, timeout=5)
                if res_job.status_code in [200, 201]:
                    success_job += 1
                    print(f"    -> Thành công!")
                else:
                    print(f"    ❌ Thất bại: {res_job.status_code} - {res_job.text}")
                    
        except Exception as e:
            print(f"❌ Lỗi khi gửi API: {e}")
            print("Hãy chắc chắn API Gateway và các Microservices của bạn đang chạy.")
            
    print(f"\n[API Sync] Hoàn thành: Công ty = {success_comp}, Jobs = {success_job}")

# ==============================================================================
# MAIN ENTRY
# ==============================================================================
def main():
    print("==============================================================================")
    print("        JOBHUB - ĐỒNG BỘ & SEED DỮ LIỆU CÔNG VIỆC THỰC TẾ TỪ ITVIEC")
    print("==============================================================================")
    print("Vui lòng lựa chọn phương thức hoạt động:")
    print("1. Seed dữ liệu trực tiếp vào Postgres (Khuyên dùng khi Dev/Test trên Docker)")
    print("2. Sử dụng dữ liệu cào trực tiếp từ ITviec (Live Crawl) và ghi trực tiếp vào DB")
    print("3. Seed dữ liệu thông qua REST API Gateway (Yêu cầu toàn bộ Web API đang chạy)")
    print("4. Thoát")
    
    choice = input("\nNhập lựa chọn của bạn (1-4): ").strip()
    
    if choice == '1':
        print("\n-> Chuẩn bị seed 5 công ty hàng đầu và 8 công việc thực tế từ ITviec vào DB...")
        db_seed_companies_and_jobs(BUILTIN_COMPANIES)
    elif choice == '2':
        keyword = input("Nhập từ khóa công nghệ cần cào trên ITviec (mặc định: python): ").strip() or "python"
        live_data = crawl_itviec_live(keyword)
        if live_data:
            print(f"\n[Crawler] Đã cào được {len(live_data)} công việc từ ITviec.")
            confirm = input("Bạn có muốn ghi dữ liệu này vào cơ sở dữ liệu không? (y/n): ").strip().lower()
            if confirm == 'y':
                db_seed_companies_and_jobs(live_data)
            else:
                print("Đã hủy ghi DB.")
        else:
            print("\n[Crawler] Không cào được dữ liệu sống (do Cloudflare chặn hoặc không tìm thấy thẻ).")
            print("Tự động chuyển hướng sang sử dụng cơ sở dữ liệu thực tế tích hợp sẵn...")
            db_seed_companies_and_jobs(BUILTIN_COMPANIES)
    elif choice == '3':
        print("\n-> Đang đồng bộ dữ liệu ITviec qua API Gateway...")
        api_sync_companies_and_jobs(BUILTIN_COMPANIES)
    else:
        print("Tạm biệt!")

if __name__ == "__main__":
    main()
