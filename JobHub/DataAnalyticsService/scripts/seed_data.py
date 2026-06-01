"""
seed_data.py
==============
Script tự động bơm (Seed) dữ liệu mẫu vào 2 Database của AI Services.
Thực hiện 2 mục tiêu:
1. Giúp MongoDB khởi tạo sẵn 2 Database và các Bảng để có thể nhìn thấy trên Compass.
2. Ép thêm 200+ mẩu dữ liệu mẫu về Lương (Salary Dataset) để XGBoost có cái lôi ra huấn luyện.

Cách chạy (Mở Terminal ở Backend/JobHub/DataAnalyticsService):
>> python scripts/seed_data.py
"""

import asyncio
import random
from datetime import datetime

import motor.motor_asyncio

# URI truy cập Mongo (giống hệt docker-compose.yml auth)
MONGO_URI = "mongodb://root:root@localhost:27017/?authSource=admin"

# Các mảng dữ liệu Random để tạo sự đa dạng
SKILLS_POOL = ["Python", "Java", "JavaScript", "React", "Node.js", "Docker", "AWS", "SQL", "MongoDB", "C#", ".NET"]
LOCATIONS = ["Hà Nội", "TP.HCM", "Đà Nẵng", "Remote"]
LEVELS = ["INTERN", "FRESHER", "JUNIOR", "MIDDLE", "SENIOR", "LEADER", "MANAGER"]
JOB_TITLES = ["Backend Developer", "Frontend Developer", "Fullstack Developer", "DevOps Engineer", "Data Scientist"]

async def seed_data():
    print("Dang ket noi toi MongoDB...")
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)

    # =========================================================================
    # 1. SEED: DataAnalyticsDB (Dữ liệu Lương để train)
    # =========================================================================
    db_analytics = client["DataAnalyticsDB"]
    col_salary = db_analytics["salary_datasets"]
    
    # Xoá data cũ nếu có để tránh bị duplicate cồng kềnh khi chạy seed lặp lại nhiều lần
    await col_salary.delete_many({})

    mock_salaries = []
    print("Dang tao ngau nhien 500 ban ghi du lieu Luong cho DataAnalyticsDB...")
    
    for _ in range(500):
        level = random.choice(LEVELS)
        years_exp = 0
        base_salary = 5.0 # Mức cơ sở 5 củ
        
        # Tạo logic giả lập tiền lương thuận tự nhiên (Kinh nghiệm cao -> Lương khét)
        if level in ["INTERN", "FRESHER"]:
            years_exp = random.randint(0, 1)
            base_salary = random.uniform(3.0, 10.0)
        elif level == "JUNIOR":
            years_exp = random.randint(1, 3)
            base_salary = random.uniform(10.0, 18.0)
        elif level == "MIDDLE":
            years_exp = random.randint(3, 5)
            base_salary = random.uniform(18.0, 35.0)
        else: # SENIOR, LEADER, MANAGER
            years_exp = random.randint(5, 12)
            base_salary = random.uniform(35.0, 80.0)
            
        doc = {
            "job_title": random.choice(JOB_TITLES),
            "years_of_experience": years_exp,
            "skill_set": random.sample(SKILLS_POOL, k=random.randint(2, 5)), # Chọc ngẫu nhiên 2-5 skills
            "location": random.choice(LOCATIONS),
            "level": level,
            "salary_min": round(base_salary, 1),
            "salary_max": round(base_salary + random.uniform(2.0, 10.0), 1),
            "is_negotiable": False,
            "source": "seed-script",
            "collected_at": datetime.utcnow()
        }
        mock_salaries.append(doc)
        
    await col_salary.insert_many(mock_salaries)
    print("Da hoan tat bom 200 mau luong gia lap dinh (SalaryDataset).")


    # =========================================================================
    # 2. SEED: CVIntelligenceDB (Bơm mắm muối cho nó hiện DB lên Compass)
    # =========================================================================
    db_cv = client["CVIntelligenceDB"]
    col_resume = db_cv["resume_analyses"]
    
    # Xoá collection mồi cũ
    await col_resume.delete_many({})
    
    mock_cvs = [
        {
            "application_id": "seed-app-1",
            "job_id": "seed-job-xyz",
            "customer_id": "seed-user-99",
            "matching_score": 85.5,
            "extracted_skills": ["React", "JavaScript", "HTML"],
            "strengths": ["Front-end cứng", "Kinh nghiệm dồi dào web app"],
            "weaknesses": ["Chưa thực chiến Docker"],
            "ai_feedback": "Ứng viên phù hợp vị trí Web FrontEnd",
            "analyzed_at": datetime.utcnow()
        },
        {
            "application_id": "seed-app-2",
            "job_id": "seed-job-xyz",
            "customer_id": "seed-user-100",
            "matching_score": 42.1,
            "extracted_skills": ["Photoshop", "Figma"],
            "strengths": ["Mắt thẩm mỹ tốt thẩm định giao diện UI"],
            "weaknesses": ["Không biết code logic React"],
            "ai_feedback": "Mô tả công việc cần Dev, ứng viên lại là Designer. Nên loại nhẹ nhàng",
            "analyzed_at": datetime.utcnow()
        }
    ]
    
    await col_resume.insert_many(mock_cvs)
    print("Da hoan tat bom 2 ket qua cham CV mau vao CVIntelligenceDB.")
    
    print("\nTHANH CONG RUC RO! Hay mo MongoDB Compass bam Refresh de tan huong 2 cai Bang nay nhe!")

if __name__ == "__main__":
    asyncio.run(seed_data())
