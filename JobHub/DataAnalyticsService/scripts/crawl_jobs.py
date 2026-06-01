"""
crawl_jobs.py
==============
Script cào dữ liệu tuyển dụng từ ITviec và TopCV,
chuẩn hóa rồi đẩy thẳng vào MongoDB collection `salary_datasets`.

Cài thư viện trước:
    pip install requests beautifulsoup4 playwright
    playwright install chromium

Cách chạy:
    python scripts/crawl_jobs.py --source itviec --pages 5
    python scripts/crawl_jobs.py --source topcv  --pages 3
    python scripts/crawl_jobs.py --source all    --pages 5
"""

import argparse
import asyncio
import json
import re
import time
import random
from datetime import datetime, timezone

import motor.motor_asyncio
import requests
from bs4 import BeautifulSoup

# ── Config ────────────────────────────────────────────────────────────────────
MONGO_URI = "mongodb://root:root@localhost:27017/?authSource=admin"
COLLECTION = "salary_datasets"
DB_NAME    = "DataAnalyticsDB"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Delay ngẫu nhiên giữa mỗi request để tránh bị Cloudflare chặn IP
MIN_DELAY = 2.0   # giây
MAX_DELAY = 5.0   # giây

# ── Bảng quy đổi tỷ giá ─────────────────────────────────────────────────────
USD_TO_VND_MILLION = 25.0   # 1 USD = 25,000 VND = 0.025 triệu


# ═════════════════════════════════════════════════════════════════════════════
# Utility: Chuẩn hóa mức lương (bất kể định dạng) → Dải lương [min, max]
# ═════════════════════════════════════════════════════════════════════════════
def parse_salary_range(raw_salary: str) -> tuple[float, float, bool]:
    """
    Trả về bộ 3 tham số: (min_salary, max_salary, is_negotiable)
    """
    if not raw_salary:
        return 0.0, 0.0, False

    text = raw_salary.lower().strip()

    skip_keywords = ["cạnh tranh", "thỏa thuận", "competitive", "negotiate",
                     "you'll love", "attractive", "thoả thuận", "không giới hạn"]
    if any(kw in text for kw in skip_keywords):
        return 0.0, 0.0, True

    is_usd = "usd" in text or "$" in text

    numbers = re.findall(r"[\d,]+(?:\.\d+)?", text.replace(",", ""))
    if not numbers:
        return 0.0, 0.0, False

    values = [float(n) for n in numbers]

    min_val, max_val = 0.0, 0.0
    if len(values) == 1:
        if "lên đến" in text or "up to" in text or "đến" in text:
            max_val = values[0]
            min_val = max_val * 0.7  # ước tính
        elif "từ" in text or "from" in text:
            min_val = values[0]
            max_val = min_val * 1.5
        else:
            min_val = max_val = values[0]
    elif len(values) >= 2:
        val1, val2 = values[0], values[1]
        min_val = min(val1, val2)
        max_val = max(val1, val2)

    def convert(val):
        if is_usd: return val * USD_TO_VND_MILLION / 1000
        if val > 1000: return val / 1_000_000
        return val

    min_sal = round(convert(min_val), 1)
    max_sal = round(convert(max_val), 1)

    if max_sal > 500: max_sal = 500.0
    if min_sal > max_sal: min_sal = max_sal

    return min_sal, max_sal, False


def parse_level(title: str, description: str = "") -> str:
    """Đoán cấp bậc từ tiêu đề hoặc mô tả việc làm."""
    text = (title + " " + description).lower()
    if any(k in text for k in ["intern", "thực tập"]):
        return "INTERN"
    if any(k in text for k in ["fresher", "junior", "0-1 year", "dưới 1 năm"]):
        return "FRESHER"
    if any(k in text for k in ["middle", "2-3 year", "2 năm", "3 năm"]):
        return "MIDDLE"
    if any(k in text for k in ["senior", "5+ year", "5 năm", "lead developer"]):
        return "SENIOR"
    if any(k in text for k in ["leader", "team lead", "tech lead"]):
        return "LEADER"
    if any(k in text for k in ["manager", "director", "head of", "cto"]):
        return "MANAGER"
    return "JUNIOR"   # mặc định


def extract_skills(tags: list[str], strict: bool = False) -> list[str]:
    """Làm sạch và chuẩn hóa danh sách skill từ thẻ tag. Nếu strict=True, chỉ lấy skill CÓ trong từ điển."""
    KNOWN_SKILLS = {
        "python", "java", "javascript", "typescript", "c#", ".net", "react", "reactjs",
        "vue", "vuejs", "angular", "nodejs", "node.js", "django", "fastapi", "spring",
        "docker", "kubernetes", "aws", "azure", "gcp", "sql", "mongodb", "mysql",
        "postgresql", "redis", "elasticsearch", "flutter", "swift", "kotlin", "php", "laravel",
        "machine learning", "deep learning", "ai", "data science", "golang", "ruby", "c++",
        "devops", "linux", "git", "microservices", "kubernetes", "html", "css"
    }
    cleaned = []
    for tag in tags:
        t = tag.strip().lower()
        if t in KNOWN_SKILLS:
            cleaned.append(tag.strip())       # giữ casing gốc
        elif not strict and len(t) > 1 and len(t) < 40:     # fallback: giữ tag web tự do
            cleaned.append(tag.strip())
    return list(set(cleaned))[:15]            # tối đa 15 skill / job


# ═════════════════════════════════════════════════════════════════════════════
# Phương pháp 1: Cào HTML tĩnh với Requests + BeautifulSoup
# Dùng cho ITviec (trang render HTML một phần ở server)
# ═════════════════════════════════════════════════════════════════════════════
def crawl_itviec_requests(max_pages: int = 5) -> list[dict]:
    """
    Cào trang tìm kiếm ITviec bằng requests (không cần trình duyệt).
    ITviec render danh sách job ở server-side → đọc thẳng HTML được.
    Nếu bị chặn Cloudflare, chuyển sang hàm crawl_itviec_playwright().
    """
    base_url = "https://itviec.com/it-jobs"
    results = []

    for page in range(1, max_pages + 1):
        url = f"{base_url}?page={page}"
        print(f"  [ITviec] Đang cào trang {page}/{max_pages}: {url}")

        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"  [ITviec] Lỗi trang {page}: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")

        # Mỗi card job nằm trong div.job_content hoặc article[data-job-id]
        job_cards = soup.select("div.job_content, article[data-job-id]")
        if not job_cards:
            print(f"  [ITviec] Không tìm thấy card nào ở trang {page} — có thể đã hết hoặc bị block.")
            break

        for card in job_cards:
            try:
                title_el   = card.select_one("h3.title a, h2 a")
                salary_el  = card.select_one("span.salary, div.salary")
                location_el= card.select_one("span.location, div.location")
                tag_els    = card.select("a.tag, span.tag-name")

                title    = title_el.get_text(strip=True)   if title_el    else "Unknown"
                raw_sal  = salary_el.get_text(strip=True)  if salary_el   else ""
                location = location_el.get_text(strip=True)if location_el else "Remote"
                tags     = [t.get_text(strip=True) for t in tag_els]

                min_sal, max_sal, is_nego = parse_salary_range(raw_sal)
                if min_sal == 0 and max_sal == 0 and not is_nego:
                    continue   # bỏ qua job không có lương rõ ràng

                results.append({
                    "job_title": title,
                    "years_of_experience": 0,       # ITviec không hiển thị field này rõ
                    "skill_set": extract_skills(tags),
                    "location": location,
                    "level": parse_level(title),
                    "salary_min": min_sal,
                    "salary_max": max_sal,
                    "is_negotiable": is_nego,
                    "source": "itviec-crawl",
                    "collected_at": datetime.now(timezone.utc),
                })

            except Exception as e:
                print(f"    Lỗi parse card: {e}")
                continue

        # Delay ngẫu nhiên giữa các trang
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    print(f"  [ITviec] Thu thập được {len(results)} bản ghi hợp lệ.")
    return results


# ═════════════════════════════════════════════════════════════════════════════
# Phương pháp 2: Render JavaScript bằng Playwright
# Dùng cho TopCV (trang dùng React/Next.js, render client-side)
# ═════════════════════════════════════════════════════════════════════════════
async def crawl_topcv_playwright(max_pages: int = 3) -> list[dict]:
    """
    Cào TopCV bằng Playwright — mở Chrome thật, đợi JS render xong rồi đọc HTML.
    Yêu cầu: playwright install chromium
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("  [TopCV] Playwright chưa được cài. Chạy: pip install playwright && playwright install chromium")
        return []

    results = []

    async with async_playwright() as p:
        # headless=False: mở Chrome thật (xem được) để dễ debug
        # headless=True : chạy nền ẩn tối đa tốc độ cào
        browser = await p.chromium.launch(headless=True)
        page    = await browser.new_page()

        # Giả lập user thật — tránh bot detection
        await page.set_extra_http_headers({
            "User-Agent": HEADERS["User-Agent"],
            "Accept-Language": "vi-VN,vi;q=0.9",
        })

        for pg in range(1, max_pages + 1):
            url = f"https://www.topcv.vn/viec-lam-it?page={pg}"
            print(f"  [TopCV] Đang cào trang {pg}/{max_pages}: {url}")

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                # Đợi selector chứa card việc làm load xong (với TopCV giao diện mới)
                await page.wait_for_selector(".job-item-search-result, .job-item, .job-card", timeout=15000)
            except Exception as e:
                print(f"  [TopCV] Trang {pg} timeout/lỗi: {e}")
                break

            # Lấy HTML của trang đã render đầy đủ
            html  = await page.content()
            soup  = BeautifulSoup(html, "html.parser")
            cards = soup.select("div.job-item-search-result, div.job-item")

            if not cards:
                print(f"  [TopCV] Không tìm thấy card ở trang {pg}.")
                break

            for card in cards:
                try:
                    title_el    = card.select_one("h3.title a, a.job-title")
                    salary_el   = card.select_one("span.salary, label.title-salary")
                    location_el = card.select_one("label.address, span.location")
                    tag_els     = card.select("label.label-content, span.tag")

                    title    = title_el.get_text(strip=True)    if title_el    else "Unknown"
                    raw_sal  = salary_el.get_text(strip=True)   if salary_el   else ""
                    location = location_el.get_text(strip=True) if location_el else "Remote"
                    tags     = [t.get_text(strip=True) for t in tag_els]
                    location = location.replace("(mới)", "").strip()
                    min_sal, max_sal, is_nego = parse_salary_range(raw_sal)
                    if min_sal == 0 and max_sal == 0 and not is_nego:
                        continue   # Nếu lỗi định dạng hoàn toàn thì mới bỏ, còn thỏa thuận (0.0/0.0/True) giữ.

                    # Lấy text của toàn bộ thẻ Card để Check "Năm kinh nghiệm"
                    card_text = card.get_text(separator=' ').lower()
                    
                    if "không yêu cầu" in card_text or "kinh nghiệm: không" in card_text:
                        years_exp = 0
                    else:
                        exp_match = re.search(r'(\d+)\s*năm', card_text)
                        if exp_match:
                            years_exp = int(exp_match.group(1))
                        else:
                            # Khúc fallback kinh điển nếu không tìm thấy text rõ ràng
                            level = parse_level(title)
                            years_exp = 0
                            if level == "INTERN": years_exp = 0
                            elif level == "FRESHER": years_exp = 1
                            elif level == "JUNIOR": years_exp = 2
                            elif level == "MIDDLE": years_exp = 3
                            elif level == "SENIOR": years_exp = 5
                            elif level in ["LEADER", "MANAGER"]: years_exp = 8
                            
                    level = parse_level(title)

                    # TopCV thay đổi giao diện, dùng Fallback bóc skill từ Tiêu đề
                    skill_set = extract_skills(tags, strict=False)
                    if not skill_set:
                         # Tự nội suy Skill từ Title NHƯNG bật chế độ KHẮT KHE (strict=True) 
                         # để chặn các chữ "Lập", "trình", "viên" lọt vào
                         words = title.lower().replace("-", " ").replace("/", " ").replace(",", " ").split()
                         skill_set = extract_skills(words, strict=True)
                         
                    # Ép cứng phải có ít nhất 1 kĩ năng mới nạp, tránh rác
                    if not skill_set:
                        continue

                    results.append({
                        "job_title": title,
                        "years_of_experience": years_exp,
                        "skill_set": skill_set,
                        "location": location,
                        "level": level,
                        "salary_min": min_sal,
                        "salary_max": max_sal,
                        "is_negotiable": is_nego,
                        "source": "topcv-crawl",
                        "collected_at": datetime.now(timezone.utc),
                    })

                except Exception as e:
                    print(f"    Lỗi parse card: {e}")
                    continue

            # Delay ngẫu nhiên giữa mỗi trang
            await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

        await browser.close()

    print(f"  [TopCV] Thu thập được {len(results)} bản ghi hợp lệ.")
    return results


# ═════════════════════════════════════════════════════════════════════════════
# Phương pháp 3 (BONUS): Nghe lén API ngầm của ITviec
# ITviec có GraphQL API trả JSON sạch hơn nhiều — ưu tiên dùng nếu còn hoạt động
# ═════════════════════════════════════════════════════════════════════════════
def crawl_itviec_api(max_pages: int = 5) -> list[dict]:
    """
    Gọi thẳng API nội bộ của ITviec (tìm được bằng cách F12 > Network > XHR).
    Kết quả là JSON nguyên bản, sạch hơn parse HTML rất nhiều.
    """
    url = "https://itviec.com/graphql"
    results = []

    query = """
    query SearchJobs($query: String, $page: Int) {
      jobs(query: $query, page: $page) {
        nodes {
          title
          salary_min
          salary_max
          salary_currency
          working_type
          skills { skill_attributes { name } }
          city { name }
          seniority_level
        }
      }
    }
    """

    for page in range(1, max_pages + 1):
        print(f"  [ITviec API] Trang {page}/{max_pages}")
        try:
            resp = requests.post(
                url,
                json={"query": query, "variables": {"query": "developer", "page": page}},
                headers={**HEADERS, "Content-Type": "application/json"},
                timeout=15,
            )
            data = resp.json()
            jobs = data.get("data", {}).get("jobs", {}).get("nodes", [])

            for job in jobs:
                try:
                    sal_min  = job.get("salary_min") or 0
                    sal_max  = job.get("salary_max") or 0
                    currency = (job.get("salary_currency") or "VND").upper()

                    if not sal_min and not sal_max:
                        continue

                    raw_salary_str = f"{sal_min} - {sal_max} {currency}"
                    min_sal, max_sal, is_nego = parse_salary_range(raw_salary_str)
                    if min_sal == 0 and max_sal == 0 and not is_nego:
                        continue

                    skills = [
                        s["skill_attributes"]["name"]
                        for s in job.get("skills", [])
                        if s.get("skill_attributes", {}).get("name")
                    ]

                    results.append({
                        "job_title": job.get("title", "Unknown"),
                        "years_of_experience": 0,
                        "skill_set": extract_skills(skills),
                        "location": job.get("city", {}).get("name", "Remote"),
                        "level": parse_level(job.get("seniority_level", "") + " " + job.get("title", "")),
                        "salary_min": min_sal,
                        "salary_max": max_sal,
                        "is_negotiable": is_nego,
                        "source": "itviec-api",
                        "collected_at": datetime.now(timezone.utc),
                    })
                except Exception as e:
                    print(f"    Lỗi parse job GraphQL: {e}")
                    continue

        except Exception as e:
            print(f"  [ITviec API] Trang {page} lỗi: {e}")
            break

        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    print(f"  [ITviec API] Thu thập được {len(results)} bản ghi hợp lệ.")
    return results


# ═════════════════════════════════════════════════════════════════════════════
# Đẩy data vào MongoDB
# ═════════════════════════════════════════════════════════════════════════════
async def insert_to_mongodb(records: list[dict]):
    if not records:
        print("Khong co du lieu de insert.")
        return

    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    col    = client[DB_NAME][COLLECTION]

    result = await col.insert_many(records)
    print(f"\nDa insert {len(result.inserted_ids)} ban ghi vao MongoDB [{DB_NAME}.{COLLECTION}].")
    client.close()


# ═════════════════════════════════════════════════════════════════════════════
# Main: chọn nguồn cào qua CLI argument
# ═════════════════════════════════════════════════════════════════════════════
async def main():
    parser = argparse.ArgumentParser(description="Crawl job data from ITviec / TopCV")
    parser.add_argument("--source", choices=["itviec", "itviec-api", "topcv", "all"],
                        default="itviec-api", help="Nguon du lieu can cao")
    parser.add_argument("--pages", type=int, default=3,
                        help="So trang can cao (moi trang ~10-20 job)")
    args = parser.parse_args()

    all_records: list[dict] = []

    print(f"\n=== JobHub Salary Data Crawler ===")
    print(f"Source : {args.source}")
    print(f"Pages  : {args.pages}")
    print("==================================\n")

    if args.source in ("itviec-api", "all"):
        records = crawl_itviec_api(args.pages)
        all_records.extend(records)

    if args.source in ("itviec", "all"):
        records = crawl_itviec_requests(args.pages)
        all_records.extend(records)

    if args.source in ("topcv", "all"):
        records = await crawl_topcv_playwright(args.pages)
        all_records.extend(records)

    print(f"\nTong cong: {len(all_records)} ban ghi hop le tu tat ca nguon.")
    await insert_to_mongodb(all_records)

    print("\nHoat dong xong! Mo MongoDB Compass va bam Refresh de xem du lieu moi.")
    print("Sau khi du lieu du nhieu (500+), chay:")
    print("  python scripts/train_salary_model.py")
    print("de train lai mo hinh XGBoost voi du lieu that tu thi truong!")


if __name__ == "__main__":
    asyncio.run(main())
