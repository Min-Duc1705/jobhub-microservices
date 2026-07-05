import asyncio
import os
import sys
import random
from datetime import datetime
from pathlib import Path

# Thêm thư mục gốc vào sys.path để import app modules
sys.path.append(str(Path(__file__).parent.parent))

import motor.motor_asyncio

MONGO_URL = os.getenv("MONGO_URL", "mongodb://root:root@localhost:27017/?authSource=admin")
MONGO_DB  = os.getenv("MONGO_DB", "DataAnalyticsDB")

SKILL_BASELINES = {
    "React": {"job_count": 130, "avg_salary": 24.5},
    "Node.js": {"job_count": 95, "avg_salary": 23.0},
    "Python": {"job_count": 85, "avg_salary": 27.5},
    "Java": {"job_count": 115, "avg_salary": 25.8},
    "Docker": {"job_count": 75, "avg_salary": 28.5},
    "Kubernetes": {"job_count": 48, "avg_salary": 34.0},
    "TypeScript": {"job_count": 105, "avg_salary": 25.2},
    "JavaScript": {"job_count": 140, "avg_salary": 21.0},
    "Go": {"job_count": 42, "avg_salary": 31.5},
    "Rust": {"job_count": 18, "avg_salary": 37.0},
    "Flutter": {"job_count": 50, "avg_salary": 21.5},
    "React Native": {"job_count": 45, "avg_salary": 22.0},
    ".NET": {"job_count": 72, "avg_salary": 23.8},
    "C#": {"job_count": 68, "avg_salary": 24.0},
    "AWS": {"job_count": 65, "avg_salary": 30.5},
    "Azure": {"job_count": 40, "avg_salary": 29.0},
    "Vue": {"job_count": 55, "avg_salary": 21.8},
    "Angular": {"job_count": 48, "avg_salary": 23.5},
    "SQL": {"job_count": 120, "avg_salary": 20.5},
    "PostgreSQL": {"job_count": 80, "avg_salary": 24.5},
    "MongoDB": {"job_count": 75, "avg_salary": 23.0},
    "Redis": {"job_count": 60, "avg_salary": 26.0},
    "Machine Learning": {"job_count": 38, "avg_salary": 35.5},
    "Deep Learning": {"job_count": 25, "avg_salary": 39.0},
}

async def seed_trends():
    print(f"[Seed Trends] Đang kết nối tới MongoDB: {MONGO_URL}...")
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
    db = client[MONGO_DB]
    col = db["job_trend_snapshots"]
    
    # Xóa dữ liệu cũ của các skill này để tránh trùng lặp
    print("[Seed Trends] Đang dọn dẹp các bản ghi xu hướng cũ...")
    await col.delete_many({"skill_name": {"$in": list(SKILL_BASELINES.keys())}})
    
    records = []
    
    # Tạo dữ liệu lịch sử cho 6 tháng: 1/2026 -> 6/2026
    months_data = [
        (1, 2026), (2, 2026), (3, 2026), (4, 2026), (5, 2026), (6, 2026)
    ]
    
    print("[Seed Trends] Đang sinh dữ liệu xu hướng thực tế...")
    for skill_name, baseline in SKILL_BASELINES.items():
        base_jobs = baseline["job_count"]
        base_sal = baseline["avg_salary"]
        
        skill_id = f"skill-{skill_name.lower().replace(' ', '-').replace('.', '-')}"
        
        # Duyệt tuần tự qua các tháng
        for i, (m, y) in enumerate(months_data):
            # Tính mức tăng trưởng xu hướng (tăng nhẹ 2-4% mỗi tháng)
            growth_factor = 1.0 + (i * 0.035)
            # Thêm độ biến động ngẫu nhiên nhỏ của thị trường
            job_noise = random.uniform(0.85, 1.15)
            sal_noise = random.uniform(0.95, 1.05)
            
            jobs = int(base_jobs * growth_factor * job_noise)
            # Lương lưu ở db dưới dạng Triệu VND thực tế (VD: 24.5 triệu)
            avg_sal = round(base_sal * growth_factor * sal_noise, 2)
            
            doc = {
                "skill_id": skill_id,
                "skill_name": skill_name,
                "month": m,
                "year": y,
                "job_count": max(1, jobs),
                "avg_salary": avg_sal,
                "demand_index": round(jobs / 100.0, 2),
                "snapshot_at": datetime.utcnow()
            }
            records.append(doc)
            
    if records:
        await col.insert_many(records)
        print(f"[Seed Trends] Đã thêm thành công {len(records)} bản ghi xu hướng vào DataAnalyticsDB!")
    else:
        print("[Seed Trends] Không có bản ghi nào được sinh ra.")
        
    client.close()

if __name__ == "__main__":
    # Đảm bảo in UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    asyncio.run(seed_trends())
