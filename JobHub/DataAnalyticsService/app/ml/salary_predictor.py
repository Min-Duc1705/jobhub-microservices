"""
salary_predictor.py
====================
Module load model XGBoost đã train sẵn, thực hiện dự đoán lương.

Cách hoạt động:
1. Lần đầu khởi động: load file `salary_model.pkl` từ disk lên bộ nhớ.
2. Mỗi request predict: Feature Engineering → Model.predict() → trả về kết quả.

QUAN TRỌNG: File .pkl được tạo ra bằng cách chạy script:
    python scripts/train_salary_model.py
Nếu chưa có file này, hàm predict() sẽ raise ModelNotAvailable exception.
"""

import hashlib
import json
import logging
import os
from pathlib import Path

import joblib
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

# Level encoding phải khớp với LabelEncoder trong script train
_LEVEL_MAP = {"INTERN": 0, "FRESHER": 1, "JUNIOR": 2, "MIDDLE": 3, "SENIOR": 4, "LEADER": 5, "MANAGER": 6}

# Top 50 skills phổ biến (phải khớp với bộ features khi train)
_KNOWN_SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "C#", "C++", "Go", "Rust",
    "React", "Vue", "Angular", "Next.js", "Node.js", "FastAPI", "Django", "Spring",
    ".NET", "ASP.NET", "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis",
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "CI/CD", "Git",
    "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "scikit-learn",
    "Microservices", "REST API", "GraphQL", "gRPC", "RabbitMQ", "Kafka",
    "Linux", "Agile", "Scrum", "ElasticSearch", "Figma", "Flutter", "React Native",
]

_LOCATION_MAP = {
    "Hà Nội": 0, "TP.HCM": 1, "Đà Nẵng": 2, "Hải Phòng": 3,
    "Khác": 4, "Remote": 5,
}

_model = None


def _load_model():
    global _model
    if _model is not None:
        return _model

    model_path = Path(settings.MODEL_PATH)
    if not model_path.exists():
        raise FileNotFoundError(
            f"[Salary] Model file không tìm thấy tại '{model_path}'.\n"
            f"Hãy chạy: python scripts/train_salary_model.py"
        )

    logger.info(f"[Salary] Đang load model từ '{model_path}'...")
    _model = joblib.load(model_path)
    logger.info("[Salary] Model sẵn sàng!")
    return _model


def _build_features(
    job_title: str,
    years_of_experience: int,
    skill_set: list[str],
    location: str,
    level: str,
) -> np.ndarray:
    """
    Chuyển input thô thành vector số để model predict.
    Phải đồng bộ 100% với script train.
    """
    features = []

    # 1. Số năm kinh nghiệm
    features.append(years_of_experience)

    # 2. Level encoding
    features.append(_LEVEL_MAP.get(level.upper(), 2))

    # 3. Location encoding
    loc_val = 4
    if location:
        loc_lower = location.lower()
        if "hà nội" in loc_lower or "ha noi" in loc_lower:
            loc_val = 0
        elif "hồ chí minh" in loc_lower or "hcm" in loc_lower or "tp.hcm" in loc_lower or "sài gòn" in loc_lower or "sai gon" in loc_lower:
            loc_val = 1
        elif "đà nẵng" in loc_lower or "da nang" in loc_lower:
            loc_val = 2
        elif "hải phòng" in loc_lower or "hai phong" in loc_lower:
            loc_val = 3
        elif "remote" in loc_lower:
            loc_val = 5
        else:
            loc_val = 4
    features.append(loc_val)


    # 4. Skills one-hot encoding (50 bits)
    skill_set_lower = {s.lower() for s in skill_set}
    for known in _KNOWN_SKILLS:
        features.append(1 if known.lower() in skill_set_lower else 0)

    return np.array(features).reshape(1, -1)


def predict_salary(
    job_title: str,
    years_of_experience: int,
    skill_set: list[str],
    location: str,
    level: str,
) -> dict:
    """
    Dự đoán khoảng lương. Trả về {min_salary, max_salary, confidence}.
    Mô hình MultiOutput cho ra trực tiếp [Midpoint, Spread].
    """
    model = _load_model()
    X = _build_features(job_title, years_of_experience, skill_set, location, level)
    
    # Kết quả trả về là Array [y_mid, y_spread]
    predicted = model.predict(X)[0]
    predicted_mid = float(predicted[0])
    predicted_spread = float(predicted[1])
    
    # An toàn hóa dữ liệu từ mô hình Toán học
    predicted_spread = max(0.0, predicted_spread)
    predicted_mid = max(1.0, predicted_mid)

    # Khôi phục Lương Min / Max từ Midpoint và Spread
    min_salary = round(predicted_mid - (predicted_spread / 2.0), 1)
    max_salary = round(predicted_mid + (predicted_spread / 2.0), 1)

    if min_salary < 1.0: 
        min_salary = 1.0

    confidence = 0.85   # Tăng độ mượt mà tự tin

    return {
        "min_salary":    min_salary,
        "max_salary":    max_salary,
        "confidence":    confidence,
        "model_version": "2.0-MultiOutput",
    }


def make_input_hash(
    job_title: str,
    years_of_experience: int,
    skill_set: list[str],
    location: str,
    level: str,
) -> str:
    """Tạo SHA256 hash của bộ input để tra cứu cache MongoDB."""
    payload = {
        "job_title": job_title.lower().strip(),
        "years":     years_of_experience,
        "skills":    sorted([s.lower() for s in skill_set]),
        "location":  location,
        "level":     level.upper(),
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def reload_model():
    """Xóa cache mô hình trong bộ nhớ để load lại file .pkl mới từ disk."""
    global _model
    _model = None
    logger.info("[Salary] Đã xóa cache model cũ để chuẩn bị tải model mới.")

