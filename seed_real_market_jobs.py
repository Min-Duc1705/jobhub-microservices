import hashlib
import json
import re
import sys
import uuid
from datetime import datetime, timedelta, timezone

import psycopg2
from psycopg2.extras import execute_values
from pymongo import MongoClient

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DB_HOST = "localhost"
DB_PORT = 5432
DB_USER = "postgres"
DB_PASSWORD = "root"

MONGO_URI = "mongodb://root:root@localhost:27017/?authSource=admin"
MONGO_DB = "DataAnalyticsDB"
SEED_SOURCE = "real-market-job-seed-2026"
TARGET_JOB_COUNT = 500
VND_UNIT = 1_000_000
PASSWORD_FALLBACK_HASH = "$2a$11$zxoSqX7OaNjBt18a7OKIAOOVFjU0GfBiqfvn6dcI41ctCLPNvwrdG"

COVER = "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1200&q=80"
ACTIVITY_IMAGES = [
    "https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=800&q=80",
]

COMPANIES = [
    {
        "name": "FPT Software",
        "website": "https://www.fpt-software.com",
        "email": "recruitment@fsoft.com.vn",
        "industry": "IT Services and Software Outsourcing",
        "address": "F-Town 3, Thu Duc City, Ho Chi Minh City",
        "size": "ENTERPRISE",
        "logo": "https://logos.hunter.io/fpt.com",
        "description": "FPT Software is a global IT services provider headquartered in Vietnam, serving enterprise clients across software engineering, cloud, data, and digital transformation.",
    },
    {
        "name": "VNGGames",
        "website": "https://vnggames.com",
        "email": "careers@vng.com.vn",
        "industry": "Internet and Game Technology",
        "address": "Z06 Street 13, Tan Thuan Dong, District 7, Ho Chi Minh City",
        "size": "ENTERPRISE",
        "logo": "https://logos.hunter.io/vng.com.vn",
        "description": "VNGGames builds large-scale digital entertainment platforms and game services for Vietnam and international markets.",
    },
    {
        "name": "One Mount Group",
        "website": "https://onemount.com",
        "email": "careers@onemount.com",
        "industry": "Fintech, Retail Tech and Real Estate Tech",
        "address": "Times City, 458 Minh Khai, Hai Ba Trung, Ha Noi",
        "size": "ENTERPRISE",
        "logo": "https://logos.hunter.io/onemount.com",
        "description": "One Mount builds digital ecosystems across retail, financial services, distribution, and property technology.",
    },
    {
        "name": "Katalon Vietnam",
        "website": "https://katalon.com",
        "email": "recruitment@katalon.com",
        "industry": "Software Testing Platform",
        "address": "Flemington Tower, Le Dai Hanh, District 11, Ho Chi Minh City",
        "size": "SME",
        "logo": "https://logos.hunter.io/katalon.com",
        "description": "Katalon develops a global quality management and test automation platform used by software teams worldwide.",
    },
    {
        "name": "FPT Telecom",
        "website": "https://fpt.vn",
        "email": "hr@fpt.vn",
        "industry": "Telecommunications and Digital Services",
        "address": "Tan Thuan Export Processing Zone, District 7, Ho Chi Minh City",
        "size": "ENTERPRISE",
        "logo": "https://logos.hunter.io/fpt.vn",
        "description": "FPT Telecom operates broadband, cloud, media, and digital service platforms across Vietnam.",
    },
    {
        "name": "Capgemini Vietnam",
        "website": "https://www.capgemini.com",
        "email": "careers.vn@capgemini.com",
        "industry": "Technology Consulting",
        "address": "District 1, Ho Chi Minh City",
        "size": "ENTERPRISE",
        "logo": "https://logos.hunter.io/capgemini.com",
        "description": "Capgemini Vietnam delivers consulting, engineering, and digital transformation services for global enterprise clients.",
    },
    {
        "name": "Rakuten Fintech Vietnam",
        "website": "https://rakuten.com",
        "email": "careers.vn@rakuten.com",
        "industry": "Fintech Software Engineering",
        "address": "Ho Chi Minh City",
        "size": "ENTERPRISE",
        "logo": "https://logos.hunter.io/rakuten.com",
        "description": "Rakuten Fintech Vietnam develops financial technology platforms and engineering systems for Rakuten group services.",
    },
    {
        "name": "ACB",
        "website": "https://acb.com.vn",
        "email": "tuyendung@acb.com.vn",
        "industry": "Banking and Financial Technology",
        "address": "442 Nguyen Thi Minh Khai, District 3, Ho Chi Minh City",
        "size": "ENTERPRISE",
        "logo": "https://logos.hunter.io/acb.com.vn",
        "description": "ACB is a major Vietnamese commercial bank investing in core banking, ERP, AI, and digital product engineering.",
    },
    {
        "name": "Shopee Vietnam",
        "website": "https://shopee.vn",
        "email": "careers.vn@shopee.com",
        "industry": "E-commerce and Logistics Technology",
        "address": "Saigon Centre, District 1, Ho Chi Minh City",
        "size": "ENTERPRISE",
        "logo": "https://logos.hunter.io/shopee.vn",
        "description": "Shopee Vietnam operates e-commerce, payments, logistics, and seller platform products at national scale.",
    },
    {
        "name": "Tiki",
        "website": "https://tiki.vn",
        "email": "careers@tiki.vn",
        "industry": "E-commerce Technology",
        "address": "District 7, Ho Chi Minh City",
        "size": "ENTERPRISE",
        "logo": "https://logos.hunter.io/tiki.vn",
        "description": "Tiki builds marketplace, fulfillment, recommendation, and retail technology products for Vietnamese consumers.",
    },
    {
        "name": "MoMo",
        "website": "https://momo.vn",
        "email": "talent@momo.vn",
        "industry": "Fintech and Digital Payments",
        "address": "Phu Nhuan District, Ho Chi Minh City",
        "size": "ENTERPRISE",
        "logo": "https://logos.hunter.io/momo.vn",
        "description": "MoMo develops one of Vietnam's largest digital wallet, payment, and financial services ecosystems.",
    },
    {
        "name": "VinAI Research",
        "website": "https://www.vinai.io",
        "email": "hr.vinai@vinai.io",
        "industry": "Artificial Intelligence Research",
        "address": "Vinhomes Times City, Ha Noi",
        "size": "ENTERPRISE",
        "logo": "https://logos.hunter.io/vinai.io",
        "description": "VinAI Research develops artificial intelligence systems in computer vision, language, automotive, and applied AI.",
    },
]

JOB_TEMPLATES = [
    ("FPT Software", "Senior Java Developer", "SENIOR", 5, ["Java", "Spring", "Spring Boot", "PostgreSQL", "Docker", "Kubernetes"], "Ho Chi Minh", 42, 78, "Backend Development", "IT Services and enterprise microservices"),
    ("FPT Software", "Middle .NET Developer", "MIDDLE", 3, ["C#", ".NET", "ASP.NET", "SQL", "Azure"], "Ha Noi", 28, 48, "Backend Development", "Enterprise web applications"),
    ("FPT Software", "Cloud DevOps Engineer", "SENIOR", 5, ["AWS", "Docker", "Kubernetes", "CI/CD", "Linux"], "Da Nang", 50, 88, "DevOps", "Cloud migration and platform operations"),
    ("VNGGames", "Senior Java Developer", "SENIOR", 5, ["Java", "Spring Boot", "Redis", "Kafka", "SQL"], "Ho Chi Minh", 50, 90, "Backend Development", "High traffic game and payment services"),
    ("VNGGames", "Frontend Engineer ReactJS", "MIDDLE", 3, ["React", "JavaScript", "TypeScript", "HTML", "CSS"], "Ho Chi Minh", 28, 48, "Frontend Development", "Game portal and operation dashboard"),
    ("VNGGames", "Game Backend Engineer Golang", "MIDDLE", 4, ["Go", "Redis", "MongoDB", "Microservices", "Linux"], "Ho Chi Minh", 35, 62, "Backend Development", "Realtime game backend services"),
    ("One Mount Group", "Senior Backend Engineer Java Spring Boot", "SENIOR", 5, ["Java", "Spring Boot", "Database", "Algorithms", "Kafka"], "Ha Noi", 55, 95, "Backend Development", "Retail and fintech ecosystem services"),
    ("One Mount Group", "Data Engineer", "MIDDLE", 4, ["Python", "SQL", "Kafka", "AWS", "Machine Learning"], "Ha Noi", 38, 70, "Data Engineering", "Data platform and product analytics"),
    ("One Mount Group", "Product Frontend Engineer React", "MIDDLE", 3, ["React", "TypeScript", "Redux", "REST API", "Git"], "Ho Chi Minh", 30, 55, "Frontend Development", "Consumer product web apps"),
    ("Katalon Vietnam", "Automation QA Engineer", "MIDDLE", 3, ["Testing", "Selenium", "Playwright", "Java", "CI/CD"], "Ho Chi Minh", 25, 45, "QA Automation", "Test automation platform"),
    ("Katalon Vietnam", "Senior Backend Engineer Node.js", "SENIOR", 5, ["Node.js", "TypeScript", "PostgreSQL", "Microservices", "AWS"], "Ho Chi Minh", 48, 82, "Backend Development", "SaaS platform backend"),
    ("Katalon Vietnam", "Frontend Developer React TypeScript", "MIDDLE", 3, ["React", "TypeScript", "JavaScript", "Figma", "REST API"], "Ho Chi Minh", 27, 48, "Frontend Development", "Testing platform UI"),
    ("FPT Telecom", "Java Backend Developer", "MIDDLE", 3, ["Java", "Spring Boot", "MySQL", "Redis", "Docker"], "Ho Chi Minh", 26, 45, "Backend Development", "Telecom self-service systems"),
    ("FPT Telecom", "System Engineer", "MIDDLE", 4, ["Linux", "Docker", "Kubernetes", "CI/CD", "SQL"], "Ha Noi", 30, 55, "Infrastructure", "Network and service platform operations"),
    ("FPT Telecom", "React Native Developer", "MIDDLE", 3, ["React Native", "JavaScript", "TypeScript", "REST API"], "Ho Chi Minh", 28, 48, "Mobile Development", "Customer mobile applications"),
    ("Capgemini Vietnam", "Java Developer Lead Senior", "SENIOR", 5, ["Java", "Spring Boot", "Microservices", "SQL", "Agile"], "Ho Chi Minh", 50, 88, "Backend Development", "Global consulting delivery"),
    ("Capgemini Vietnam", "Business Analyst IT", "MIDDLE", 3, ["Agile", "Scrum", "SQL", "REST API"], "Ho Chi Minh", 28, 50, "Business Analysis", "Enterprise delivery projects"),
    ("Capgemini Vietnam", "Senior DevOps Engineer", "SENIOR", 6, ["AWS", "Azure", "Kubernetes", "Docker", "CI/CD"], "Ho Chi Minh", 60, 105, "DevOps", "Cloud platform automation"),
    ("Rakuten Fintech Vietnam", "Mid Senior Java Developer English Required", "SENIOR", 5, ["Java", "Spring Boot", "English", "SQL", "Microservices"], "Ho Chi Minh", 50, 82, "Backend Development", "Fintech platform engineering"),
    ("Rakuten Fintech Vietnam", "Fullstack Engineer React Java", "MIDDLE", 4, ["React", "Java", "JavaScript", "Spring Boot", "TypeScript"], "Ho Chi Minh", 38, 68, "Fullstack Development", "Internal fintech systems"),
    ("Rakuten Fintech Vietnam", "QA Automation Engineer", "MIDDLE", 3, ["Testing", "Selenium", "Java", "CI/CD"], "Ho Chi Minh", 25, 45, "QA Automation", "Financial product testing"),
    ("ACB", "Fullstack Developer ERP Fusion Java Python AI", "MIDDLE", 4, ["Java", "Python", "React", "SQL", "Machine Learning"], "Ho Chi Minh", 38, 70, "Fullstack Development", "Banking ERP and AI systems"),
    ("ACB", "Backend Developer Core Banking", "SENIOR", 5, ["Java", "Spring Boot", "Oracle", "Kafka", "Redis"], "Ho Chi Minh", 52, 92, "Backend Development", "Core banking integration"),
    ("ACB", "Data Scientist", "SENIOR", 5, ["Python", "SQL", "Machine Learning", "Deep Learning", "TensorFlow"], "Ho Chi Minh", 55, 100, "Data Science", "Risk and customer analytics"),
    ("Shopee Vietnam", "Senior Frontend Engineer React", "SENIOR", 5, ["React", "TypeScript", "JavaScript", "Redux", "Jest"], "Ho Chi Minh", 45, 78, "Frontend Development", "E-commerce seller and buyer platforms"),
    ("Shopee Vietnam", "Backend Engineer Golang", "MIDDLE", 4, ["Go", "MySQL", "Redis", "Kafka", "Microservices"], "Ho Chi Minh", 40, 72, "Backend Development", "Marketplace services"),
    ("Shopee Vietnam", "Data Engineer", "SENIOR", 5, ["Python", "SQL", "Kafka", "AWS", "Spark"], "Ho Chi Minh", 55, 95, "Data Engineering", "E-commerce data pipelines"),
    ("Tiki", "Frontend Developer ReactJS", "MIDDLE", 3, ["React", "JavaScript", "TypeScript", "CSS", "REST API"], "Ho Chi Minh", 25, 45, "Frontend Development", "Marketplace web products"),
    ("Tiki", "Senior Backend Engineer Node.js", "SENIOR", 5, ["Node.js", "TypeScript", "MongoDB", "Redis", "Microservices"], "Ho Chi Minh", 45, 80, "Backend Development", "Order and fulfillment systems"),
    ("Tiki", "Mobile Engineer Flutter", "MIDDLE", 3, ["Flutter", "Dart", "Firebase", "REST API"], "Ho Chi Minh", 28, 50, "Mobile Development", "Consumer mobile app"),
    ("MoMo", "Senior Backend Engineer Java", "SENIOR", 6, ["Java", "Spring Boot", "Kafka", "Redis", "Microservices"], "Ho Chi Minh", 60, 105, "Backend Development", "Digital payment services"),
    ("MoMo", "DevOps Engineer", "SENIOR", 5, ["Kubernetes", "Docker", "AWS", "CI/CD", "Linux"], "Ho Chi Minh", 65, 115, "DevOps", "Payment platform reliability"),
    ("MoMo", "Machine Learning Engineer", "SENIOR", 5, ["Python", "Machine Learning", "Deep Learning", "PyTorch", "SQL"], "Ho Chi Minh", 65, 120, "AI Engineering", "Fraud and personalization models"),
    ("VinAI Research", "AI Engineer Computer Vision", "SENIOR", 5, ["Python", "Deep Learning", "PyTorch", "TensorFlow", "Machine Learning"], "Ha Noi", 70, 130, "AI Engineering", "Computer vision research and deployment"),
    ("VinAI Research", "Data Engineer MLOps", "MIDDLE", 4, ["Python", "Docker", "Kubernetes", "AWS", "Machine Learning"], "Ha Noi", 45, 80, "Data Engineering", "ML pipelines and model serving"),
    ("VinAI Research", "Backend Engineer Python FastAPI", "MIDDLE", 3, ["Python", "FastAPI", "PostgreSQL", "Docker", "REST API"], "Ha Noi", 32, 58, "Backend Development", "AI platform backend"),
]

TEAM_SUFFIXES = [
    "Core Platform", "Product Growth", "Payment Platform", "Customer Experience",
    "Data Platform", "Cloud Platform", "Merchant Services", "Internal Tools",
    "Mobile Platform", "AI Services", "Infrastructure", "Enterprise Delivery",
    "Marketplace", "Risk & Compliance", "Search & Recommendation",
]

EXTRA_SKILLS_BY_CATEGORY = {
    "Backend Development": ["REST API", "RabbitMQ", "GraphQL", "Git", "Agile"],
    "Frontend Development": ["Next.js", "GraphQL", "Jest", "Git", "Agile"],
    "Fullstack Development": ["REST API", "GraphQL", "Docker", "Git", "Agile"],
    "DevOps": ["Terraform", "GCP", "Azure", "RabbitMQ", "Git"],
    "Data Engineering": ["Spark", "Airflow", "MongoDB", "GCP", "Git"],
    "Data Science": ["scikit-learn", "AWS", "Docker", "Git"],
    "AI Engineering": ["scikit-learn", "FastAPI", "Docker", "Kubernetes", "Git"],
    "Mobile Development": ["Firebase", "Git", "Agile"],
    "QA Automation": ["REST API", "Git", "Agile"],
    "Business Analysis": ["Figma", "Git", "Agile"],
    "Infrastructure": ["AWS", "Azure", "Git"],
}

LEVEL_VARIANTS = {
    "MIDDLE": [("MIDDLE", 1.00, 0), ("MIDDLE", 1.04, 1), ("SENIOR", 1.30, 2), ("JUNIOR", 0.72, -1)],
    "SENIOR": [("SENIOR", 1.00, 0), ("SENIOR", 1.08, 1), ("LEADER", 1.28, 2), ("MIDDLE", 0.74, -2)],
}


def build_market_job_records():
    records = []
    for idx in range(TARGET_JOB_COUNT):
        base = JOB_TEMPLATES[idx % len(JOB_TEMPLATES)]
        company_name, title, level, years, skills, location, sal_min, sal_max, category, context = base
        cycle = idx // len(JOB_TEMPLATES)
        level_options = LEVEL_VARIANTS.get(level, [(level, 1.0, 0)])
        level, level_multiplier, year_delta = level_options[(idx + cycle) % len(level_options)]
        years = max(0, years + year_delta)

        salary_wave = 1.0 + (((idx * 7 + cycle * 3) % 13) - 6) / 100.0
        salary_min = round(max(6.0, sal_min * level_multiplier * salary_wave), 1)
        salary_max = round(max(salary_min + 4.0, sal_max * level_multiplier * (salary_wave + 0.02)), 1)

        skill_pool = EXTRA_SKILLS_BY_CATEGORY.get(category, ["Git", "Agile"])
        augmented_skills = list(dict.fromkeys(skills + [skill_pool[(idx + cycle) % len(skill_pool)]]))
        if len(augmented_skills) > 7:
            augmented_skills = augmented_skills[:7]

        team = TEAM_SUFFIXES[(idx + cycle) % len(TEAM_SUFFIXES)]
        title_variant = title if cycle == 0 else f"{title} - {team}"
        if level == "JUNIOR" and "Junior" not in title_variant:
            title_variant = title_variant.replace("Middle", "Junior").replace("Senior", "Junior")
            if "Junior" not in title_variant:
                title_variant = f"Junior {title_variant}"
        elif level == "LEADER" and not any(k in title_variant.lower() for k in ["lead", "leader"]):
            title_variant = f"Lead {title_variant}"
        elif level == "SENIOR" and "Senior" not in title_variant and "Lead" not in title_variant:
            title_variant = f"Senior {title_variant}"

        records.append((
            company_name, title_variant, level, years, augmented_skills, location,
            salary_min, salary_max, category, context
        ))
    return records


def db(name):
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=name, user=DB_USER, password=DB_PASSWORD)


def slug(value):
    clean = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return clean or "company"


def stable_uuid(namespace, key):
    return str(uuid.uuid5(namespace, key))


def get_hr_role_and_hash(auth_cur):
    auth_cur.execute('SELECT "Id" FROM "Roles" WHERE "Name" = %s LIMIT 1', ("HR",))
    row = auth_cur.fetchone()
    if not row:
        raise RuntimeError("Role HR not found in AuthService.Roles")
    role_id = row[0]

    auth_cur.execute('SELECT "PasswordHash" FROM "AppUsers" WHERE "RoleId" = %s AND "PasswordHash" IS NOT NULL LIMIT 1', (role_id,))
    row = auth_cur.fetchone()
    return role_id, (row[0] if row else PASSWORD_FALLBACK_HASH)


def upsert_company(cur, item):
    now = datetime.now(timezone.utc)
    cur.execute('SELECT "Id" FROM "Companies" WHERE LOWER("Name") = LOWER(%s) AND "IsDeleted" = false LIMIT 1', (item["name"],))
    row = cur.fetchone()
    company_id = row[0] if row else stable_uuid(uuid.NAMESPACE_URL, f"jobhub-company:{item['name']}")
    activity_json = json.dumps(ACTIVITY_IMAGES)

    if row:
        cur.execute(
            '''
            UPDATE "Companies"
            SET "Description"=%s, "Address"=%s, "Logo"=%s, "CoverImage"=%s, "Industry"=%s,
                "CompanySize"=%s, "Website"=%s, "ContactEmail"=%s, "IsVerified"=true,
                "ActivityImages"=%s::jsonb, "LastModifiedDate"=%s, "LastModifiedBy"=%s
            WHERE "Id"=%s
            ''',
            (item["description"], item["address"], item["logo"], COVER, item["industry"], item["size"],
             item["website"], item["email"], activity_json, now, SEED_SOURCE, company_id),
        )
    else:
        cur.execute(
            '''
            INSERT INTO "Companies" (
                "Id", "Name", "Description", "Address", "Logo", "CoverImage", "Industry", "CompanySize",
                "Website", "ContactEmail", "TaxCode", "IsVerified", "ActivityImages",
                "CreatedDate", "LastModifiedDate", "CreatedBy", "LastModifiedBy", "IsDeleted"
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,true,%s::jsonb,%s,%s,%s,%s,false)
            ''',
            (company_id, item["name"], item["description"], item["address"], item["logo"], COVER, item["industry"],
             item["size"], item["website"], item["email"], None, activity_json, now, now, SEED_SOURCE, SEED_SOURCE),
        )
    return company_id


def ensure_hr(auth_cur, profile_cur, company_id, company_name, role_id, password_hash):
    now = datetime.now(timezone.utc)
    profile_cur.execute(
        'SELECT "Id", "AppUserId" FROM "Customers" WHERE "CompanyId" = %s AND "Type" = %s AND "IsDeleted" = false LIMIT 1',
        (company_id, "EMPLOYER"),
    )
    row = profile_cur.fetchone()
    if row:
        return row[0]

    hr_email = f"hr.{slug(company_name)}@jobhub.vn"
    hr_name = f"HR {company_name}"
    auth_cur.execute('SELECT "Id" FROM "AppUsers" WHERE LOWER("Email") = LOWER(%s) LIMIT 1', (hr_email,))
    row = auth_cur.fetchone()
    app_user_id = row[0] if row else stable_uuid(uuid.NAMESPACE_URL, f"jobhub-hr-user:{company_name}")

    if row:
        auth_cur.execute(
            'UPDATE "AppUsers" SET "Username"=%s, "Status"=%s, "RoleId"=%s, "LastModifiedDate"=%s, "LastModifiedBy"=%s WHERE "Id"=%s',
            (hr_name, "Active", role_id, now, SEED_SOURCE, app_user_id),
        )
    else:
        auth_cur.execute(
            '''
            INSERT INTO "AppUsers" (
                "Id", "Email", "Username", "PasswordHash", "Status", "RefreshToken", "RoleId",
                "CreatedDate", "LastModifiedDate", "CreatedBy", "LastModifiedBy", "IsDeleted"
            ) VALUES (%s,%s,%s,%s,%s,NULL,%s,%s,%s,%s,%s,false)
            ''',
            (app_user_id, hr_email, hr_name, password_hash, "Active", role_id, now, now, SEED_SOURCE, SEED_SOURCE),
        )

    customer_id = stable_uuid(uuid.NAMESPACE_URL, f"jobhub-hr-customer:{company_name}")
    profile_cur.execute(
        '''
        INSERT INTO "Customers" (
            "Id", "AppUserId", "Type", "FullName", "Avatar", "Phone", "CompanyId", "Position",
            "CreatedDate", "LastModifiedDate", "CreatedBy", "LastModifiedBy", "IsDeleted"
        ) VALUES (%s,%s,%s,%s,NULL,NULL,%s,%s,%s,%s,%s,%s,false)
        ON CONFLICT ("Id") DO UPDATE SET
            "CompanyId"=EXCLUDED."CompanyId", "Type"=EXCLUDED."Type", "FullName"=EXCLUDED."FullName",
            "Position"=EXCLUDED."Position", "LastModifiedDate"=EXCLUDED."LastModifiedDate",
            "LastModifiedBy"=EXCLUDED."LastModifiedBy", "IsDeleted"=false
        ''',
        (customer_id, app_user_id, "EMPLOYER", hr_name, company_id, "Talent Acquisition Manager", now, now, SEED_SOURCE, SEED_SOURCE),
    )
    return customer_id


def sync_skills(job_cur):
    job_cur.execute('SELECT "Id", "Name" FROM "Skills" WHERE "IsDeleted" = false')
    return {name.lower(): sid for sid, name in job_cur.fetchall()}


def insert_jobs(job_cur, company_map, hr_map, skill_map):
    now = datetime.now(timezone.utc)
    source_jobs = []
    job_skill_rows = []

    job_cur.execute('DELETE FROM "JobSkills" WHERE "JobId" IN (SELECT "Id" FROM "Jobs" WHERE "CreatedBy" = %s)', (SEED_SOURCE,))
    job_cur.execute('DELETE FROM "Jobs" WHERE "CreatedBy" = %s', (SEED_SOURCE,))

    company_lookup = {c["name"]: c for c in COMPANIES}
    for company_name, title, level, years, skills, location, sal_min, sal_max, category, context in build_market_job_records():
        company = company_lookup[company_name]
        company_id = company_map[company_name]
        customer_id = hr_map[company_name]
        job_id = stable_uuid(uuid.NAMESPACE_URL, f"jobhub-job:{company_name}:{title}")
        description = (
            f"{company_name} is hiring {title} for {context}. "
            f"The role focuses on production software delivery, code quality, cross-functional collaboration, and measurable business impact."
        )
        requirements = (
            f"Required experience: about {years}+ years for this level. "
            f"Core skills: {', '.join(skills)}. Candidates should communicate clearly, own delivery, and understand production systems."
        )
        benefits = "Competitive monthly salary, 13th month salary, annual performance review, health insurance, learning budget, and hybrid-friendly collaboration."
        job_type = "HYBRID" if location in {"Ho Chi Minh", "Ha Noi"} else "FULL_TIME"
        exp_text = f"{years}+ years of relevant experience"

        source_jobs.append((
            job_id, customer_id, company_id, title, company_name, company["logo"], location,
            float(round(sal_min * VND_UNIT)), float(round(sal_max * VND_UNIT)), "VND", False, 1, level, job_type, exp_text,
            description, requirements, benefits, now, now + timedelta(days=45), 0, "PUBLISHED",
            category, now, now, SEED_SOURCE, SEED_SOURCE, False
        ))

        for skill in skills:
            sid = skill_map.get(skill.lower())
            if sid:
                job_skill_rows.append((job_id, sid))

    execute_values(
        job_cur,
        '''
        INSERT INTO "Jobs" (
            "Id", "CustomerId", "CompanyId", "Name", "CompanyName", "CompanyLogo", "Location",
            "SalaryMin", "SalaryMax", "SalaryCurrency", "IsSalaryNegotiable", "Quantity",
            "Level", "JobType", "ExperienceRequired", "Description", "Requirements", "Benefits",
            "StartDate", "EndDate", "ViewCount", "Status", "Category",
            "CreatedDate", "LastModifiedDate", "CreatedBy", "LastModifiedBy", "IsDeleted"
        ) VALUES %s
        ''',
        source_jobs,
    )
    if job_skill_rows:
        execute_values(
            job_cur,
            'INSERT INTO "JobSkills" ("JobId", "SkillId") VALUES %s ON CONFLICT DO NOTHING',
            sorted(set(job_skill_rows)),
        )
    return len(source_jobs), len(set(job_skill_rows))


def seed_salary_dataset():
    client = MongoClient(MONGO_URI)
    dbm = client[MONGO_DB]
    dbm["salary_datasets"].delete_many({"source": SEED_SOURCE})
    dbm["salary_prediction_caches"].delete_many({})
    docs = []
    now = datetime.utcnow()
    for company_name, title, level, years, skills, location, sal_min, sal_max, category, _ in build_market_job_records():
        docs.append({
            "job_title": title,
            "years_of_experience": years,
            "skill_set": skills,
            "location": location,
            "level": level,
            "salary_min": float(sal_min),
            "salary_max": float(sal_max),
            "is_negotiable": False,
            "source": SEED_SOURCE,
            "company_name": company_name,
            "category": category,
            "collected_at": now,
        })
    if docs:
        dbm["salary_datasets"].insert_many(docs)
    client.close()
    return len(docs)


def main():
    comp_conn = db("CompanyService")
    auth_conn = db("AuthService")
    profile_conn = db("ProfileService")
    job_conn = db("JobService")
    try:
        comp_cur = comp_conn.cursor()
        auth_cur = auth_conn.cursor()
        profile_cur = profile_conn.cursor()
        job_cur = job_conn.cursor()

        role_id, password_hash = get_hr_role_and_hash(auth_cur)
        company_map = {}
        hr_map = {}

        for company in COMPANIES:
            cid = upsert_company(comp_cur, company)
            company_map[company["name"]] = cid
            hr_map[company["name"]] = ensure_hr(auth_cur, profile_cur, cid, company["name"], role_id, password_hash)

        skill_map = sync_skills(job_cur)
        jobs_count, job_skills_count = insert_jobs(job_cur, company_map, hr_map, skill_map)
        salary_count = seed_salary_dataset()

        comp_conn.commit()
        auth_conn.commit()
        profile_conn.commit()
        job_conn.commit()

        print(f"Companies upserted: {len(company_map)}")
        print(f"Employer customers ready: {len(hr_map)}")
        print(f"Jobs seeded: {jobs_count}")
        print(f"JobSkills linked: {job_skills_count}")
        print(f"Salary dataset records inserted for training: {salary_count}")
    except Exception:
        comp_conn.rollback()
        auth_conn.rollback()
        profile_conn.rollback()
        job_conn.rollback()
        raise
    finally:
        comp_conn.close()
        auth_conn.close()
        profile_conn.close()
        job_conn.close()


if __name__ == "__main__":
    main()
