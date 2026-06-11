"""
Seed realistic salary samples for DataAnalyticsService.

The script only replaces records created by this seeder. Real salary records
from JobService-Sync, crawlers, or user input are kept intact.

Run from Backend/JobHub/DataAnalyticsService:
    python scripts/seed_data.py
"""

import asyncio
import random
from datetime import datetime

import motor.motor_asyncio

MONGO_URI = "mongodb://root:root@localhost:27017/?authSource=admin"
SEED_SOURCE = "market-seed-vn-2026"

LOCATIONS = {
    "TP.HCM": 1.06,
    "Ha Noi": 1.0,
    "Da Nang": 0.9,
    "Remote": 1.08,
    "Can Tho": 0.82,
}

LEVEL_YEARS = {
    "INTERN": (0, 0),
    "FRESHER": (0, 1),
    "JUNIOR": (1, 3),
    "MIDDLE": (3, 5),
    "SENIOR": (5, 8),
    "LEADER": (7, 11),
    "MANAGER": (8, 14),
}

# Salary bands are monthly gross salary in million VND, tuned for Vietnam IT market.
ROLE_PROFILES = {
    "Frontend Developer": {
        "bands": {
            "INTERN": (3.0, 7.0),
            "FRESHER": (8.0, 14.0),
            "JUNIOR": (13.0, 24.0),
            "MIDDLE": (24.0, 42.0),
            "SENIOR": (38.0, 68.0),
            "LEADER": (50.0, 85.0),
            "MANAGER": (60.0, 105.0),
        },
        "skills": ["JavaScript", "TypeScript", "React", "Vue", "Angular", "Next.js", "HTML", "CSS", "Figma"],
        "premium_skills": {"TypeScript": 0.03, "React": 0.03, "Next.js": 0.05, "Angular": 0.02},
    },
    "Backend Developer": {
        "bands": {
            "INTERN": (3.0, 7.0),
            "FRESHER": (8.0, 15.0),
            "JUNIOR": (14.0, 26.0),
            "MIDDLE": (27.0, 48.0),
            "SENIOR": (42.0, 76.0),
            "LEADER": (58.0, 95.0),
            "MANAGER": (70.0, 120.0),
        },
        "skills": ["Java", "Python", "C#", ".NET", "Node.js", "Spring", "SQL", "PostgreSQL", "MongoDB", "Redis"],
        "premium_skills": {"Java": 0.02, "Python": 0.02, ".NET": 0.02, "Spring": 0.03, "Redis": 0.03},
    },
    "Fullstack Developer": {
        "bands": {
            "INTERN": (3.5, 8.0),
            "FRESHER": (9.0, 16.0),
            "JUNIOR": (16.0, 28.0),
            "MIDDLE": (30.0, 52.0),
            "SENIOR": (46.0, 82.0),
            "LEADER": (60.0, 100.0),
            "MANAGER": (72.0, 125.0),
        },
        "skills": ["JavaScript", "TypeScript", "React", "Node.js", "Java", ".NET", "SQL", "Docker", "REST API"],
        "premium_skills": {"TypeScript": 0.03, "React": 0.03, "Node.js": 0.03, "Docker": 0.04},
    },
    "Mobile Developer": {
        "bands": {
            "INTERN": (3.0, 7.0),
            "FRESHER": (8.0, 15.0),
            "JUNIOR": (14.0, 27.0),
            "MIDDLE": (27.0, 47.0),
            "SENIOR": (42.0, 74.0),
            "LEADER": (55.0, 90.0),
            "MANAGER": (65.0, 110.0),
        },
        "skills": ["React Native", "Flutter", "JavaScript", "TypeScript", "Swift", "Kotlin", "Firebase", "REST API"],
        "premium_skills": {"React Native": 0.03, "Flutter": 0.03, "Swift": 0.04, "Kotlin": 0.04},
    },
    "DevOps Engineer": {
        "bands": {
            "INTERN": (5.0, 10.0),
            "FRESHER": (10.0, 18.0),
            "JUNIOR": (18.0, 34.0),
            "MIDDLE": (34.0, 60.0),
            "SENIOR": (50.0, 90.0),
            "LEADER": (70.0, 120.0),
            "MANAGER": (85.0, 150.0),
        },
        "skills": ["Docker", "Kubernetes", "AWS", "Azure", "GCP", "CI/CD", "Linux", "Terraform", "Git"],
        "premium_skills": {"Kubernetes": 0.06, "AWS": 0.05, "Azure": 0.04, "GCP": 0.04, "Terraform": 0.05},
    },
    "Data AI Engineer": {
        "bands": {
            "INTERN": (5.0, 10.0),
            "FRESHER": (10.0, 20.0),
            "JUNIOR": (18.0, 34.0),
            "MIDDLE": (34.0, 62.0),
            "SENIOR": (54.0, 95.0),
            "LEADER": (75.0, 130.0),
            "MANAGER": (90.0, 160.0),
        },
        "skills": ["Python", "SQL", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "scikit-learn", "AWS"],
        "premium_skills": {"Machine Learning": 0.05, "Deep Learning": 0.06, "PyTorch": 0.04, "TensorFlow": 0.04, "AWS": 0.03},
    },
    "QA Automation Engineer": {
        "bands": {
            "INTERN": (3.0, 6.5),
            "FRESHER": (7.0, 13.0),
            "JUNIOR": (12.0, 22.0),
            "MIDDLE": (22.0, 38.0),
            "SENIOR": (35.0, 62.0),
            "LEADER": (48.0, 80.0),
            "MANAGER": (58.0, 100.0),
        },
        "skills": ["JavaScript", "Python", "Java", "Selenium", "Playwright", "SQL", "CI/CD", "Git"],
        "premium_skills": {"Playwright": 0.03, "Selenium": 0.03, "CI/CD": 0.03},
    },
}

COMPANY_MULTIPLIERS = [
    ("outsourcing", 0.92),
    ("local-product", 1.0),
    ("fintech", 1.12),
    ("global-product", 1.18),
    ("startup", 0.96),
]


def weighted_level() -> str:
    return random.choices(
        population=["INTERN", "FRESHER", "JUNIOR", "MIDDLE", "SENIOR", "LEADER", "MANAGER"],
        weights=[5, 9, 18, 34, 25, 6, 3],
        k=1,
    )[0]


def years_for_level(level: str) -> int:
    start, end = LEVEL_YEARS[level]
    return random.randint(start, end)


def pick_skills(profile: dict, level: str) -> list[str]:
    base_count = {
        "INTERN": 2,
        "FRESHER": 2,
        "JUNIOR": 3,
        "MIDDLE": 4,
        "SENIOR": 5,
        "LEADER": 6,
        "MANAGER": 5,
    }[level]
    count = min(len(profile["skills"]), random.randint(max(2, base_count - 1), base_count + 1))
    return random.sample(profile["skills"], k=count)


def salary_for(profile: dict, level: str, years: int, skills: list[str], location: str, company_type: str) -> tuple[float, float]:
    band_min, band_max = profile["bands"][level]
    company_multiplier = dict(COMPANY_MULTIPLIERS)[company_type]
    location_multiplier = LOCATIONS[location]

    min_year, max_year = LEVEL_YEARS[level]
    year_span = max(1, max_year - min_year)
    year_progress = (years - min_year) / year_span
    experience_multiplier = 0.94 + (year_progress * 0.12)

    skill_multiplier = 1.0
    for skill in skills:
        skill_multiplier += profile["premium_skills"].get(skill, 0.0)
    skill_multiplier = min(skill_multiplier, 1.18)

    noise = random.uniform(0.94, 1.06)
    midpoint = ((band_min + band_max) / 2.0) * company_multiplier * location_multiplier * experience_multiplier * skill_multiplier * noise
    spread = (band_max - band_min) * random.uniform(0.45, 0.72)

    salary_min = max(3.0, midpoint - spread / 2.0)
    salary_max = max(salary_min + 3.0, midpoint + spread / 2.0)

    # Keep generated samples inside a realistic envelope for each role/level.
    salary_min = max(band_min * 0.82, salary_min)
    salary_max = min(band_max * 1.25, salary_max)
    if salary_max <= salary_min:
        salary_max = salary_min + random.uniform(3.0, 8.0)

    return round(salary_min, 1), round(salary_max, 1)


def job_title_for(role: str, level: str, skills: list[str]) -> str:
    title_level = {
        "INTERN": "Intern",
        "FRESHER": "Fresher",
        "JUNIOR": "Junior",
        "MIDDLE": "Middle",
        "SENIOR": "Senior",
        "LEADER": "Lead",
        "MANAGER": "Engineering Manager",
    }[level]
    if level == "MANAGER":
        return f"{title_level} - {role}"

    main_skill = next((s for s in skills if s in {"React", "Vue", "Angular", "Java", "Python", ".NET", "Node.js", "React Native", "Flutter", "AWS"}), None)
    if main_skill:
        return f"{title_level} {main_skill} {role}"
    return f"{title_level} {role}"


async def seed_data():
    print("Dang ket noi toi MongoDB...")
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)

    db_analytics = client["DataAnalyticsDB"]
    col_salary = db_analytics["salary_datasets"]
    cache_col = db_analytics["salary_prediction_caches"]

    delete_result = await col_salary.delete_many({"source": SEED_SOURCE})
    print(f"Da xoa {delete_result.deleted_count} mau seed cu. Du lieu that duoc giu nguyen.")

    random.seed(2026)
    mock_salaries = []
    sample_size = 800
    print(f"Dang tao {sample_size} ban ghi luong seed sat thi truong Viet Nam...")

    role_names = list(ROLE_PROFILES.keys())
    role_weights = [22, 24, 16, 10, 10, 10, 8]

    for _ in range(sample_size):
        role = random.choices(role_names, weights=role_weights, k=1)[0]
        profile = ROLE_PROFILES[role]
        level = weighted_level()
        years = years_for_level(level)
        location = random.choices(list(LOCATIONS.keys()), weights=[42, 34, 10, 10, 4], k=1)[0]
        company_type, _ = random.choices(COMPANY_MULTIPLIERS, weights=[35, 25, 14, 12, 14], k=1)[0]
        skills = pick_skills(profile, level)
        salary_min, salary_max = salary_for(profile, level, years, skills, location, company_type)

        mock_salaries.append({
            "job_title": job_title_for(role, level, skills),
            "years_of_experience": years,
            "skill_set": skills,
            "location": location,
            "level": level,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "is_negotiable": False,
            "source": SEED_SOURCE,
            "company_type": company_type,
            "collected_at": datetime.utcnow(),
        })

    await col_salary.insert_many(mock_salaries)
    await cache_col.delete_many({})
    print(f"Da them {len(mock_salaries)} mau luong seed moi vao DataAnalyticsDB.salary_datasets.")
    print("Da xoa salary_prediction_caches de tranh dung lai du doan cu.")

    print("Hoan tat seed dataset luong. Khong thay doi job that hoac du lieu CV.")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_data())
