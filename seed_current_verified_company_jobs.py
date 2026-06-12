import ast
import argparse
import html
import random
import re
import sys
import time
import unicodedata
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import psycopg2
import requests
from bs4 import BeautifulSoup
from pymongo import ASCENDING, MongoClient, UpdateOne

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "root",
}

SOURCE = "verified-web-jobs-2026-06"
CHECKED_AT = datetime(2026, 6, 12, tzinfo=timezone.utc)
MIN_JOBS_PER_COMPANY = 1
MAX_JOBS_PER_COMPANY = 25
LINKEDIN_SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
LINKEDIN_DETAIL_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
MONGO_URI = "mongodb://root:root@localhost:27017/?authSource=admin"
MONGO_DB = "CVIntelligenceDB"
MONGO_JOB_COLLECTION = "job_training_corpus"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 Safari/605.1.15",
]

COMPANY_ALIASES = {
    "Lazada Vietnam": ["Lazada"],
    "Tencent Vietnam": ["Tencent"],
    "Garena Vietnam": ["Garena"],
    "FAST Software Company": ["FAST"],
    "Panasonic R&D Center Vietnam": ["Panasonic"],
    "Home Credit Vietnam": ["Home Credit Vietnam", "Home Credit"],
    "NEC Vietnam": ["NEC Vietnam", "NEC"],
    "Hitachi Vantara Vietnam": ["Hitachi Vantara"],
    "Pyco Group": ["PYCOGroup", "PYCO Group"],
    "Woori Bank IT Center": ["Woori Bank Vietnam"],
    "Shinhan Bank IT Center": ["Shinhan Bank Vietnam", "Shinhan DS"],
    "HSBC IT Center": ["HSBC"],
    "Mercari Vietnam": ["Mercari"],
    "Money Forward Vietnam": ["Money Forward Vietnam"],
    "Henny Penny Vietnam": ["Henny Penny"],
    "Be Group": ["BE GROUP", "beGroup"],
    "Koei Tecmo Vietnam": ["KOEI TECMO SOFTWARE VIETNAM"],
    "Sparx* - a Virtuos Studio": ["Sparx", "Virtuos"],
    "NCS Vietnam": ["NCS Group", "NCS"],
    "DXC Technology Vietnam": ["DXC Technology"],
    "Luxoft Vietnam": ["Luxoft"],
    "EPAM Systems Vietnam": ["EPAM Systems"],
    "Capgemini Vietnam": ["Capgemini"],
    "Cognizant Vietnam": ["Cognizant"],
    "Infosys Vietnam": ["Infosys"],
    "Wipro Vietnam": ["Wipro"],
    "HCLTech Vietnam": ["HCLTech"],
    "Tata Consultancy Services Vietnam": ["Tata Consultancy Services", "TCS"],
    "Ericsson Vietnam": ["Ericsson"],
    "Nokia Vietnam": ["Nokia"],
    "Huawei Vietnam": ["Huawei"],
    "Cisco Vietnam": ["Cisco"],
    "Fortinet Vietnam": ["Fortinet"],
    "Palo Alto Networks Vietnam": ["Palo Alto Networks"],
    "Check Point Software Vietnam": ["Check Point Software"],
    "Kaspersky Vietnam": ["Kaspersky"],
    "VNG Games": ["VNGGames", "VNG"],
    "VNCS (Vietnam Cyber Security)": ["VNCS"],
    "VinAI Research": ["VinAI"],
    "VinBigData": ["VinBigdata"],
    "FPT Information System": ["FPT IS"],
    "Viettel AI Center": ["Viettel AI"],
    "VNPT AI Center": ["VNPT AI"],
    "MindX Technology School": ["MindX Technology School", "MindX"],
    "Teky Academy": ["TEKY Academy", "TEKY"],
    "Funix": ["FUNiX"],
    "Topica Edtech Group": ["Topica"],
    "Buymed (Thuocsi.vn)": ["Buymed", "thuocsi.vn"],
    "Navigos Group (VietnamWorks)": ["Navigos Group", "VietnamWorks"],
    "J&T Express Vietnam": ["J&T Express Vietnam", "J&T Express"],
    "Ninja Van Vietnam": ["Ninja Van"],
    "Qualcomm Vietnam": ["Qualcomm"],
}

IGNORED_COMPANY_WORDS = {
    "vietnam",
    "viet",
    "nam",
    "company",
    "corporation",
    "corp",
    "group",
    "co",
    "ltd",
    "limited",
    "center",
    "centre",
    "technology",
    "technologies",
    "software",
    "systems",
    "it",
    "research",
    "academy",
    "school",
}

SKILL_ALIASES = {
    "nodejs": "node.js",
    "node js": "node.js",
    "golang": "go",
    "reactjs": "react",
    "vuejs": "vue",
    "nextjs": "next.js",
    "dotnet": ".net",
    "c sharp": "c#",
    "postgres": "postgresql",
    "k8s": "kubernetes",
    "amazon web services": "aws",
    "google cloud": "gcp",
    "quality assurance": "testing",
    "qa qc": "testing",
}


def db(name):
    return psycopg2.connect(dbname=name, **DB_CONFIG)


def normalize(value):
    value = unicodedata.normalize("NFKD", (value or "").lower())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def company_core(value):
    return [
        word
        for word in normalize(value).split()
        if word not in IGNORED_COMPANY_WORDS
    ]


def company_matches(expected, actual):
    variants = [expected, *COMPANY_ALIASES.get(expected, [])]
    normalized_actual = normalize(actual)

    for variant in variants:
        normalized_variant = normalize(variant)
        if normalized_variant == normalized_actual:
            return True
        if len(normalized_variant) >= 4 and (
            normalized_variant in normalized_actual
            or normalized_actual in normalized_variant
        ):
            return True

        expected_words = set(company_core(variant))
        actual_words = set(company_core(actual))
        if expected_words and len(expected_words & actual_words) / len(expected_words) >= 0.75:
            return True

    return False


def load_verified_companies():
    source_path = Path(__file__).with_name("update_to_real_companies.py")
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(
            isinstance(target, ast.Name) and target.id == "REAL_COMPANIES"
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise RuntimeError("Không tìm thấy REAL_COMPANIES trong update_to_real_companies.py")


def linked_in_job_id(url):
    match = re.search(r"-(\d+)(?:\?|$)", url or "")
    return match.group(1) if match else None


def clean_source_url(url):
    if not url:
        return ""
    parsed = urlparse(html.unescape(url))
    return parsed._replace(query="", fragment="").geturl()


def fetch_search_page(query, start):
    response = requests.get(
        LINKEDIN_SEARCH_URL,
        params={"keywords": query, "location": "Vietnam", "start": start},
        headers={"User-Agent": random.choice(USER_AGENTS)},
        timeout=12,
    )
    response.raise_for_status()
    return response.text


def collect_company_jobs(company_name):
    query_variants = COMPANY_ALIASES.get(company_name, []) + [company_name]
    results = {}

    for query in dict.fromkeys(query_variants):
        for start in (0, 25):
            best_html = ""
            for attempt in range(2):
                try:
                    best_html = fetch_search_page(query, start)
                    if len(best_html) > 100:
                        break
                except requests.RequestException:
                    if attempt == 1:
                        best_html = ""
                time.sleep(0.15 + random.random() * 0.2)

            soup = BeautifulSoup(best_html, "html.parser")
            for item in soup.select("li"):
                title_node = item.select_one(".base-search-card__title")
                company_node = item.select_one(".base-search-card__subtitle")
                location_node = item.select_one(".job-search-card__location")
                link_node = item.select_one("a.base-card__full-link")
                date_node = item.select_one("time")

                if not (title_node and company_node and link_node):
                    continue

                actual_company = company_node.get_text(" ", strip=True)
                if not company_matches(company_name, actual_company):
                    continue

                source_url = clean_source_url(link_node.get("href"))
                job_id = linked_in_job_id(source_url)
                if not job_id:
                    continue

                results[job_id] = {
                    "source_job_id": job_id,
                    "title": title_node.get_text(" ", strip=True),
                    "source_company": actual_company,
                    "location": (
                        location_node.get_text(" ", strip=True)
                        if location_node
                        else "Vietnam"
                    ),
                    "source_url": source_url,
                    "posted_at": date_node.get("datetime") if date_node else None,
                }

            if len(results) >= MAX_JOBS_PER_COMPANY:
                break
            time.sleep(0.15 + random.random() * 0.2)

        if len(results) >= MAX_JOBS_PER_COMPANY:
            break

    unique_by_title = {}
    for item in results.values():
        key = normalize(item["title"])
        unique_by_title.setdefault(key, item)

    return list(unique_by_title.values())[:MAX_JOBS_PER_COMPANY]


def fetch_job_description(job_id):
    for attempt in range(2):
        try:
            response = requests.get(
                LINKEDIN_DETAIL_URL.format(job_id=job_id),
                headers={"User-Agent": random.choice(USER_AGENTS)},
                timeout=12,
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            description = soup.select_one(".show-more-less-html__markup")
            return description.get_text("\n", strip=True) if description else ""
        except requests.RequestException:
            if attempt == 1:
                return ""
            time.sleep(0.25 + random.random() * 0.5)
    return ""


def infer_level(title):
    value = normalize(title)
    if re.search(r"\b(intern|internship|trainee)\b", value):
        return "INTERN"
    if re.search(r"\b(fresher|graduate)\b", value):
        return "FRESHER"
    if re.search(r"\b(junior|jr)\b", value):
        return "JUNIOR"
    if re.search(r"\b(manager|head|director)\b", value):
        return "MANAGER"
    if re.search(r"\b(lead|principal|architect)\b", value):
        return "LEADER"
    if re.search(r"\b(senior|sr|expert)\b", value):
        return "SENIOR"
    return "MIDDLE"


def infer_job_type(title, location, description):
    value = normalize(f"{title} {location} {description[:500]}")
    if "remote" in value:
        return "REMOTE"
    if "hybrid" in value:
        return "HYBRID"
    if "part time" in value:
        return "PART_TIME"
    if "intern" in value or "trainee" in value:
        return "INTERNSHIP"
    return "FULL_TIME"


def infer_category(title):
    value = normalize(title)
    categories = [
        (("ai", "machine learning", "data scientist", "computer vision", "nlp"), "Data Science & AI"),
        (("data engineer", "bigdata", "big data", "analytics engineer", "bi engineer"), "Data Engineering"),
        (("devops", "cloud", "site reliability", "sre", "infrastructure"), "DevOps & Cloud"),
        (("security", "cyber", "soc", "pentest"), "Cybersecurity"),
        (("frontend", "front end", "react", "angular", "vue"), "Frontend Development"),
        (("backend", "back end", "java", "nodejs", "golang", "python developer", ".net"), "Backend Development"),
        (("mobile", "android", "ios", "flutter", "react native"), "Mobile Development"),
        (("qa", "tester", "testing", "quality assurance"), "QA & Testing"),
        (("game", "unity", "artist"), "Game Development"),
        (("business analyst", "product analyst"), "Business Analysis"),
        (("product manager", "product owner"), "Product Management"),
        (("network", "telecom", "embedded", "firmware"), "Network & Sysadmin"),
    ]
    for keywords, category in categories:
        if any(
            re.search(
                rf"(?<![a-z0-9]){re.escape(normalize(keyword))}(?![a-z0-9])",
                value,
            )
            for keyword in keywords
        ):
            return category
    return "Software Development"


def infer_experience(description, level):
    normalized = re.sub(r"\s+", " ", description)
    patterns = [
        r"(\d+\+?\s*(?:years?|năm)[^.;\n]{0,50}(?:experience|kinh nghiệm))",
        r"((?:at least|minimum|tối thiểu)\s+\d+\+?\s*(?:years?|năm)[^.;\n]{0,40})",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized, re.IGNORECASE)
        if match:
            return match.group(1)[:180]
    defaults = {
        "INTERN": "Không yêu cầu kinh nghiệm; ưu tiên sinh viên năm cuối.",
        "FRESHER": "0-1 năm kinh nghiệm.",
        "JUNIOR": "1-2 năm kinh nghiệm.",
        "MIDDLE": "2-4 năm kinh nghiệm.",
        "SENIOR": "4+ năm kinh nghiệm.",
        "LEADER": "5+ năm kinh nghiệm và có năng lực dẫn dắt.",
        "MANAGER": "5+ năm kinh nghiệm, bao gồm kinh nghiệm quản lý.",
    }
    return defaults[level]


def normalize_location(location):
    value = normalize(location)
    if "ho chi minh" in value or "saigon" in value:
        return "TP. Hồ Chí Minh"
    if "ha noi" in value or "hanoi" in value:
        return "Hà Nội"
    if "da nang" in value:
        return "Đà Nẵng"
    return location[:255] if location else "Việt Nam"


def detect_skills(text, skill_map):
    normalized_text = normalize(text)
    matches = []
    for skill_name, skill_id in skill_map.items():
        variants = {normalize(skill_name)}
        for alias, canonical in SKILL_ALIASES.items():
            if normalize(canonical) == normalize(skill_name):
                variants.add(normalize(alias))
        if any(
            len(variant) >= 2
            and re.search(rf"(?<![a-z0-9]){re.escape(variant)}(?![a-z0-9])", normalized_text)
            for variant in variants
        ):
            matches.append((skill_id, skill_name))
    return matches[:12]


def load_database_context(company_cur, auth_cur, profile_cur, job_cur):
    company_cur.execute(
        '''
        SELECT "Id", "Name", "Logo", "Website", "CreatedDate"
        FROM "Companies"
        WHERE "IsDeleted" = false
        ORDER BY "CreatedDate"
        '''
    )
    companies = company_cur.fetchall()

    auth_cur.execute(
        '''
        SELECT u."Id", LOWER(u."Email"), r."Name", u."Status"
        FROM "AppUsers" u
        JOIN "Roles" r ON r."Id" = u."RoleId"
        WHERE u."IsDeleted" = false
        '''
    )
    users = {str(row[0]): row for row in auth_cur.fetchall()}

    profile_cur.execute(
        '''
        SELECT "AppUserId", "CompanyId"
        FROM "Customers"
        WHERE "Type" = 'EMPLOYER' AND "IsDeleted" = false AND "CompanyId" IS NOT NULL
        '''
    )
    company_users = {}
    for app_user_id, company_id in profile_cur.fetchall():
        company_users.setdefault(str(company_id), []).append(str(app_user_id))

    job_cur.execute(
        '''
        SELECT "CompanyId", COUNT(*)
        FROM "Jobs"
        WHERE "IsDeleted" = false
        GROUP BY "CompanyId"
        '''
    )
    job_counts = {str(row[0]): row[1] for row in job_cur.fetchall()}

    job_cur.execute(
        '''
        SELECT "CompanyId", COUNT(*)
        FROM "Jobs"
        WHERE "IsDeleted" = false AND "CreatedBy" = %s
        GROUP BY "CompanyId"
        ''',
        (SOURCE,),
    )
    source_job_counts = {str(row[0]): row[1] for row in job_cur.fetchall()}

    job_cur.execute('SELECT "Id", "Name" FROM "Skills" WHERE "IsDeleted" = false')
    skill_map = {row[1]: row[0] for row in job_cur.fetchall()}
    return companies, users, company_users, job_counts, source_job_counts, skill_map


def resolve_company_and_hr(
    expected_name,
    companies,
    users,
    company_users,
    job_counts,
):
    candidates = [
        company
        for company in companies
        if normalize(company[1]) == normalize(expected_name)
    ]
    if not candidates:
        return None, None

    ranked = []
    for company in candidates:
        company_id = str(company[0])
        valid_hr_ids = [
            user_id
            for user_id in company_users.get(company_id, [])
            if user_id in users
            and users[user_id][2] == "HR"
            and users[user_id][3] == "Active"
        ]
        valid_hr_ids.sort(
            key=lambda user_id: (
                0 if users[user_id][1].startswith("hr.") else 1,
                users[user_id][1],
            )
        )
        ranked.append(
            (
                0 if valid_hr_ids else 1,
                -job_counts.get(company_id, 0),
                company,
                valid_hr_ids[0] if valid_hr_ids else None,
            )
        )

    ranked.sort(key=lambda item: (item[0], item[1]))
    _, _, company, hr_user_id = ranked[0]
    return company, hr_user_id


def build_job_record(company, hr_user_id, source_job, description):
    company_id, company_name, company_logo, _, _ = company
    title = source_job["title"][:255]
    level = infer_level(title)
    location = normalize_location(source_job["location"])
    skills_text = f"{title}\n{description}"
    source_url = source_job["source_url"]
    posted_at = source_job["posted_at"]
    checked_date = CHECKED_AT.strftime("%d/%m/%Y")

    normalized_description = (
        f"{company_name} đang tuyển vị trí {title} tại {location}. "
        f"Tin được đối chiếu từ nguồn tuyển dụng công khai vào ngày {checked_date}. "
        f"Mô tả đầy đủ và trạng thái ứng tuyển: {source_url}"
    )
    requirements = (
        f"Yêu cầu được chuẩn hóa từ tin tuyển dụng gốc. "
        f"Kinh nghiệm tham khảo: {infer_experience(description, level)} "
        f"Vui lòng kiểm tra yêu cầu chi tiết tại: {source_url}"
    )
    benefits = (
        "Lương và phúc lợi theo chính sách hiện hành của công ty; "
        "nguồn công khai không được dùng để suy đoán mức lương."
    )

    start_date = CHECKED_AT
    if posted_at:
        try:
            start_date = datetime.fromisoformat(posted_at).replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    stable_id = uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"jobhub:{SOURCE}:{source_job['source_job_id']}",
    )
    return {
        "id": str(stable_id),
        "customer_id": hr_user_id,
        "company_id": company_id,
        "company_name": company_name,
        "company_logo": company_logo,
        "name": title,
        "location": location,
        "level": level,
        "job_type": infer_job_type(title, location, description),
        "experience_required": infer_experience(description, level),
        "description": normalized_description,
        "requirements": requirements,
        "benefits": benefits,
        "start_date": start_date,
        "end_date": CHECKED_AT + timedelta(days=45),
        "category": infer_category(title),
        "skills_text": skills_text,
    }


def upsert_job(job_cur, record):
    job_cur.execute(
        '''
        INSERT INTO "Jobs" (
            "Id", "CustomerId", "CompanyId", "Name", "CompanyName", "CompanyLogo",
            "Location", "SalaryMin", "SalaryMax", "SalaryCurrency",
            "IsSalaryNegotiable", "Quantity", "Level", "JobType",
            "ExperienceRequired", "Description", "Requirements", "Benefits",
            "StartDate", "EndDate", "ViewCount", "Status", "Category",
            "CreatedDate", "LastModifiedDate", "CreatedBy", "LastModifiedBy", "IsDeleted"
        ) VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, NULL, NULL, 'VND',
            true, 1, %s, %s,
            %s, %s, %s, %s,
            %s, %s, 0, 'PUBLISHED', %s,
            %s, %s, %s, %s, false
        )
        ON CONFLICT ("Id") DO UPDATE SET
            "CustomerId" = EXCLUDED."CustomerId",
            "CompanyId" = EXCLUDED."CompanyId",
            "Name" = EXCLUDED."Name",
            "CompanyName" = EXCLUDED."CompanyName",
            "CompanyLogo" = EXCLUDED."CompanyLogo",
            "Location" = EXCLUDED."Location",
            "Level" = EXCLUDED."Level",
            "JobType" = EXCLUDED."JobType",
            "ExperienceRequired" = EXCLUDED."ExperienceRequired",
            "Description" = EXCLUDED."Description",
            "Requirements" = EXCLUDED."Requirements",
            "Benefits" = EXCLUDED."Benefits",
            "StartDate" = EXCLUDED."StartDate",
            "EndDate" = EXCLUDED."EndDate",
            "Status" = 'PUBLISHED',
            "Category" = EXCLUDED."Category",
            "LastModifiedDate" = EXCLUDED."LastModifiedDate",
            "LastModifiedBy" = EXCLUDED."LastModifiedBy",
            "IsDeleted" = false
        ''',
        (
            record["id"],
            record["customer_id"],
            record["company_id"],
            record["name"],
            record["company_name"],
            record["company_logo"],
            record["location"],
            record["level"],
            record["job_type"],
            record["experience_required"],
            record["description"],
            record["requirements"],
            record["benefits"],
            record["start_date"],
            record["end_date"],
            record["category"],
            CHECKED_AT,
            CHECKED_AT,
            SOURCE,
            SOURCE,
        ),
    )


def sync_seeded_jobs_to_mongo(job_cur):
    job_cur.execute(
        '''
        SELECT
            j."Id", j."CustomerId", j."CompanyId", j."CompanyName",
            j."Name", j."Location", j."Level", j."JobType", j."Category",
            j."ExperienceRequired", j."Description", j."Requirements",
            j."Benefits", j."StartDate", j."EndDate", j."Status",
            COALESCE(
                ARRAY_AGG(DISTINCT s."Name") FILTER (WHERE s."Name" IS NOT NULL),
                ARRAY[]::text[]
            ) AS skills
        FROM "Jobs" j
        LEFT JOIN "JobSkills" js ON js."JobId" = j."Id"
        LEFT JOIN "Skills" s ON s."Id" = js."SkillId" AND s."IsDeleted" = false
        WHERE j."CreatedBy" = %s AND j."IsDeleted" = false
        GROUP BY j."Id"
        ORDER BY j."CompanyName", j."Name"
        ''',
        (SOURCE,),
    )
    rows = job_cur.fetchall()

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    try:
        client.admin.command("ping")
        collection = client[MONGO_DB][MONGO_JOB_COLLECTION]
        collection.create_index([("job_id", ASCENDING)], unique=True)
        collection.create_index([("company_id", ASCENDING)])
        collection.create_index([("skills", ASCENDING)])
        collection.create_index([("source", ASCENDING)])

        operations = []
        synced_at = datetime.now(timezone.utc)
        for row in rows:
            (
                job_id,
                customer_id,
                company_id,
                company_name,
                title,
                location,
                level,
                job_type,
                category,
                experience_required,
                description,
                requirements,
                benefits,
                start_date,
                end_date,
                status,
                skills,
            ) = row
            source_match = re.search(r"https://[^\s]+", description or "")
            source_url = source_match.group(0) if source_match else None
            training_text = "\n".join(
                part
                for part in (
                    f"Job title: {title}",
                    f"Company: {company_name}",
                    f"Location: {location}",
                    f"Level: {level}",
                    f"Category: {category}",
                    f"Skills: {', '.join(skills)}" if skills else "",
                    f"Experience: {experience_required}",
                    f"Description: {description}",
                    f"Requirements: {requirements}",
                    f"Benefits: {benefits}",
                )
                if part
            )
            document = {
                "job_id": str(job_id),
                "hr_user_id": str(customer_id),
                "company_id": str(company_id),
                "company_name": company_name,
                "title": title,
                "location": location,
                "level": level,
                "job_type": job_type,
                "category": category,
                "experience_required": experience_required,
                "description": description,
                "requirements": requirements,
                "benefits": benefits,
                "skills": list(skills),
                "status": status,
                "source": SOURCE,
                "source_url": source_url,
                "source_posted_at": start_date,
                "expires_at": end_date,
                "training_purpose": [
                    "job_cv_matching",
                    "job_recommendation",
                    "skill_extraction",
                ],
                "training_text": training_text,
                "is_labeled": False,
                "synced_at": synced_at,
            }
            operations.append(
                UpdateOne(
                    {"job_id": str(job_id)},
                    {
                        "$set": document,
                        "$setOnInsert": {"collected_at": CHECKED_AT},
                    },
                    upsert=True,
                )
            )

        if operations:
            result = collection.bulk_write(operations, ordered=False)
            return {
                "total": len(rows),
                "upserted": result.upserted_count,
                "modified": result.modified_count,
            }
        return {"total": 0, "upserted": 0, "modified": 0}
    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Bỏ qua công ty đã có ít nhất 1 job từ nguồn seed này.",
    )
    parser.add_argument(
        "--sync-mongo-only",
        action="store_true",
        help="Chỉ đồng bộ các job đã seed từ PostgreSQL sang MongoDB.",
    )
    args = parser.parse_args()
    verified_companies = load_verified_companies()
    company_conn = db("CompanyService")
    auth_conn = db("AuthService")
    profile_conn = db("ProfileService")
    job_conn = db("JobService")

    seeded_companies = []
    skipped = []
    total_jobs = 0

    try:
        company_cur = company_conn.cursor()
        auth_cur = auth_conn.cursor()
        profile_cur = profile_conn.cursor()
        job_cur = job_conn.cursor()

        (
            companies,
            users,
            company_users,
            job_counts,
            source_job_counts,
            skill_map,
        ) = load_database_context(company_cur, auth_cur, profile_cur, job_cur)

        if args.sync_mongo_only:
            mongo_result = sync_seeded_jobs_to_mongo(job_cur)
            print(
                "MongoDB sync: "
                f"{mongo_result['total']} documents, "
                f"upserted={mongo_result['upserted']}, "
                f"modified={mongo_result['modified']}"
            )
            return

        for index, item in enumerate(verified_companies, start=1):
            expected_name = item["name"]
            company, hr_user_id = resolve_company_and_hr(
                expected_name,
                companies,
                users,
                company_users,
                job_counts,
            )
            if not company or not hr_user_id:
                skipped.append((expected_name, "Không tìm thấy Company/HR hợp lệ"))
                print(f"[{index:03}/100] SKIP {expected_name}: thiếu Company/HR")
                continue

            company_id = str(company[0])
            if args.resume and source_job_counts.get(company_id, 0) >= MIN_JOBS_PER_COMPANY:
                print(
                    f"[{index:03}/100] DONE {company[1]}: "
                    f"{source_job_counts[company_id]} jobs đã seed"
                )
                continue

            source_jobs = collect_company_jobs(expected_name)
            if len(source_jobs) < MIN_JOBS_PER_COMPANY:
                skipped.append(
                    (
                        expected_name,
                        f"Chỉ xác minh được {len(source_jobs)} tin đang mở",
                    )
                )
                print(
                    f"[{index:03}/100] SKIP {expected_name}: "
                    f"{len(source_jobs)} tin xác minh"
                )
                continue

            seeded_for_company = 0
            for source_job in source_jobs[:MAX_JOBS_PER_COMPANY]:
                description = fetch_job_description(source_job["source_job_id"])
                record = build_job_record(
                    company,
                    hr_user_id,
                    source_job,
                    description,
                )
                upsert_job(job_cur, record)
                job_cur.execute('DELETE FROM "JobSkills" WHERE "JobId" = %s', (record["id"],))

                for skill_id, _ in detect_skills(record["skills_text"], skill_map):
                    job_cur.execute(
                        '''
                        INSERT INTO "JobSkills" ("JobId", "SkillId")
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                        ''',
                        (record["id"], skill_id),
                    )

                seeded_for_company += 1
                time.sleep(0.2 + random.random() * 0.25)

            total_jobs += seeded_for_company
            seeded_companies.append(
                (
                    company[1],
                    users[hr_user_id][1],
                    seeded_for_company,
                )
            )
            job_conn.commit()
            print(
                f"[{index:03}/100] OK {company[1]}: "
                f"{seeded_for_company} jobs -> {users[hr_user_id][1]}"
            )

        job_conn.commit()
        mongo_result = sync_seeded_jobs_to_mongo(job_cur)

        print("\n=== KẾT QUẢ ===")
        print(f"Công ty được seed: {len(seeded_companies)}")
        print(f"Job được seed/upsert: {total_jobs}")
        print(f"Công ty bỏ qua: {len(skipped)}")
        print(
            f"MongoDB {MONGO_DB}.{MONGO_JOB_COLLECTION}: "
            f"{mongo_result['total']} documents, "
            f"upserted={mongo_result['upserted']}, "
            f"modified={mongo_result['modified']}"
        )
        for company_name, email, count in seeded_companies:
            print(f"  OK {company_name}: {count} jobs, HR={email}")
        for company_name, reason in skipped:
            print(f"  SKIP {company_name}: {reason}")
    except Exception:
        job_conn.rollback()
        raise
    finally:
        company_conn.close()
        auth_conn.close()
        profile_conn.close()
        job_conn.close()


if __name__ == "__main__":
    main()
