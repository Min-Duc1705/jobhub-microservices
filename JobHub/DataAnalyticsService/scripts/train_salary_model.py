"""
train_salary_model.py
======================
Script độc lập để huấn luyện mô hình XGBoost dự đoán lương.

CÁCH SỬ DỤNG:
    Điều hướng đến thư mục DataAnalyticsService và chạy:
    >> python scripts/train_salary_model.py

Kết quả:
    File `app/ml/artifacts/salary_model.pkl` sẽ được tạo ra (hoặc ghi đè nếu đã có).
    FastAPI service sau đó load file này lên mỗi khi khởi động.

TÁI TRAINING:
    - Thu thập thêm dữ liệu vào collection `salary_datasets` trong MongoDB.
    - Chạy lại script này (hoặc đặt Cronjob).
    - Restart service để load model mới.
"""

import asyncio
import os
import sys
from pathlib import Path

# Thêm thư mục gốc vào path để import app modules
sys.path.append(str(Path(__file__).parent.parent))

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import motor.motor_asyncio

# ── Config ────────────────────────────────────────────────────────────────────
MONGO_URL   = "mongodb://root:root@localhost:27017/?authSource=admin"
MONGO_DB    = "DataAnalyticsDB"
OUTPUT_PATH = "app/ml/artifacts/salary_model.pkl"

# Phải đồng bộ với salary_predictor.py
KNOWN_SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "C#", "C++", "Go", "Rust",
    "React", "Vue", "Angular", "Next.js", "Node.js", "FastAPI", "Django", "Spring",
    ".NET", "ASP.NET", "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis",
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "CI/CD", "Git",
    "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "scikit-learn",
    "Microservices", "REST API", "GraphQL", "gRPC", "RabbitMQ", "Kafka",
    "Linux", "Agile", "Scrum", "ElasticSearch", "Figma", "Flutter", "React Native",
]
LEVEL_MAP    = {"INTERN": 0, "FRESHER": 1, "JUNIOR": 2, "MIDDLE": 3, "SENIOR": 4, "LEADER": 5, "MANAGER": 6}
LOCATION_MAP = {"Hà Nội": 0, "TP.HCM": 1, "Đà Nẵng": 2, "Hải Phòng": 3, "Khác": 4, "Remote": 5}


async def load_data_from_mongo() -> pd.DataFrame:
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
    col = client[MONGO_DB]["salary_datasets"]
    docs = await col.find({}).to_list(length=None)

    if not docs:
        print("[Train] ❌ Không có dữ liệu trong MongoDB 'salary_datasets'.")
        print("[Train] Hãy thêm dữ liệu trước qua API POST /api/v1/salary/dataset")
        sys.exit(1)

    print(f"[Train] ✅ Đã tải {len(docs)} bản ghi từ MongoDB.")
    return pd.DataFrame(docs)


def build_features(df: pd.DataFrame):
    rows = []
    labels = []

    # Loại bỏ các job Thoả Thuận khỏi tập train vĩnh viễn (vì không có Y)
    df = df[df.get("is_negotiable", False) != True]

    for _, row in df.iterrows():
        min_salary = float(row.get("salary_min", 0))
        max_salary = float(row.get("salary_max", 0))
        
        # Nếu DB cũ chưa migrate, fallback dùng cột actual_salary
        if min_salary == 0 and max_salary == 0 and row.get("actual_salary"):
            min_salary = max_salary = float(row.get("actual_salary"))

        if min_salary == 0 and max_salary == 0:
            continue
            
        if min_salary > max_salary:
            min_salary, max_salary = max_salary, min_salary

        features = []
        features.append(int(row.get("years_of_experience", 0)))
        features.append(LEVEL_MAP.get(str(row.get("level", "JUNIOR")).upper(), 2))
        loc_str = str(row.get("location", "Khác")).lower()
        loc_val = 4
        if "hà nội" in loc_str or "ha noi" in loc_str:
            loc_val = 0
        elif "hồ chí minh" in loc_str or "hcm" in loc_str or "tp.hcm" in loc_str or "sài gòn" in loc_str or "sai gon" in loc_str:
            loc_val = 1
        elif "đà nẵng" in loc_str or "da nang" in loc_str:
            loc_val = 2
        elif "hải phòng" in loc_str or "hai phong" in loc_str:
            loc_val = 3
        elif "remote" in loc_str:
            loc_val = 5
        else:
            loc_val = 4
        features.append(loc_val)


        skill_set_lower = {s.lower() for s in row.get("skill_set", [])}
        for skill in KNOWN_SKILLS:
            features.append(1 if skill.lower() in skill_set_lower else 0)

        rows.append(features)
        
        # Chuyển hoá Min, Max => Midpoint & Spread
        y_mid = (min_salary + max_salary) / 2.0
        y_spread = max_salary - min_salary
        labels.append([y_mid, y_spread])

    X = np.array(rows)
    Y = np.array(labels)
    return X, Y


async def train():
    df = await load_data_from_mongo()
    X, y = build_features(df)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"[Train] Training set: {len(X_train)} mẫu | Test set: {len(X_test)} mẫu")

    model = MultiOutputRegressor(
        XGBRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,        # Dùng toàn bộ CPU nhân
            tree_method="hist",  # Nhanh hơn cho dataset lớn
        )
    )

    print("[Train] ⏳ Đang huấn luyện Multi-Output XGBoost Regressor...")
    # Vì XGBRegressor native không support verbose cho MultiOutputRegressor dễ dàng nên tắt verbose
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae_mid    = mean_absolute_error(y_test[:, 0], y_pred[:, 0])
    mae_spread = mean_absolute_error(y_test[:, 1], y_pred[:, 1])
    r2_mid     = r2_score(y_test[:, 0], y_pred[:, 0])
    
    print(f"\n[Train] ✅ Kết quả Evaluation:")
    print(f"  MAE Midpoint: {mae_mid:.2f} triệu VND")
    print(f"  MAE Spread  : {mae_spread:.2f} triệu VND")
    print(f"  R² Midpoint : {r2_mid:.4f} (Gần 1 là tốt nhất)")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    joblib.dump(model, OUTPUT_PATH)
    print(f"\n[Train] 💾 Model đã lưu tại: {OUTPUT_PATH}")
    print("[Train] Restart DataAnalyticsService để load model mới.")


if __name__ == "__main__":
    asyncio.run(train())
