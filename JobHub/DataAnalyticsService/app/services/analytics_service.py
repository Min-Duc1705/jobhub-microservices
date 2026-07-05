import logging
import asyncio
from datetime import datetime
import pandas as pd
import numpy as np
import joblib
from xgboost import XGBRegressor
from sklearn.multioutput import MultiOutputRegressor

from app.config import settings
from app.core.database import (
    get_salary_dataset_col,
    get_salary_cache_col,
    get_job_trend_col,
    get_model_metadata_col,
)
from app.ml.salary_predictor import predict_salary, make_input_hash, reload_model

# Danh sách kỹ năng và map phục vụ tự động train
KNOWN_SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "C#", "C++", "Go", "Rust",
    "React", "Vue", "Angular", "Next.js", "Node.js", "FastAPI", "Django", "Spring",
    ".NET", "ASP.NET", "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis",
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "CI/CD", "Git",
    "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "scikit-learn",
    "Microservices", "REST API", "GraphQL", "gRPC", "RabbitMQ", "Kafka",
    "Linux", "Agile", "Scrum", "ElasticSearch", "Figma", "Flutter", "React Native",
]
LEVEL_MAP = {"INTERN": 0, "FRESHER": 1, "JUNIOR": 2, "MIDDLE": 3, "SENIOR": 4, "LEADER": 5, "MANAGER": 6}

ROLE_KEYWORDS = [
    "software", "engineer", "developer", "tester", "manager", "leader", 
    "analyst", "designer", "embedded", "data", "ai", "blockchain", 
    "devops", "fullstack", "backend", "frontend"
]

logger = logging.getLogger(__name__)

async def _run_background_retrain(current_count: int):
    """Huấn luyện lại XGBoost model dưới nền và ghi đè file salary_model.pkl."""
    logger.info("[Auto-Retrain] Bắt đầu tự động huấn luyện lại model lương...")
    try:
        col = get_salary_dataset_col()
        # Train exclusively on the clean TopCV dataset to prevent noise and outliers
        docs = await col.find({"source": "topcv-seed-2026"}).to_list(length=None)
        if not docs:
            logger.warning("[Auto-Retrain] Không có dữ liệu để train.")
            return

        df = pd.DataFrame(docs)
        rows = []
        labels = []
        df = df[df.get("is_negotiable", False) != True]

        for _, row in df.iterrows():
            min_salary = float(row.get("salary_min", 0))
            max_salary = float(row.get("salary_max", 0))
            
            if min_salary == 0 and max_salary == 0 and row.get("actual_salary"):
                min_salary = max_salary = float(row.get("actual_salary"))

            if min_salary == 0 and max_salary == 0:
                continue
                
            if min_salary > max_salary:
                min_salary, max_salary = max_salary, min_salary

            features = []
            features.append(int(row.get("years_of_experience", 0)))
            features.append(LEVEL_MAP.get(str(row.get("level", "JUNIOR")).upper(), 2))
            
            # Cắt chuỗi địa lý giống như salary_predictor
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

            # Role keywords features
            title_lower = str(row.get("job_title", "")).lower()
            for kw in ROLE_KEYWORDS:
                features.append(1 if kw in title_lower else 0)

            # Skill features
            skill_set_lower = {s.lower() for s in row.get("skill_set", [])}
            for skill in KNOWN_SKILLS:
                features.append(1 if skill.lower() in skill_set_lower else 0)

            rows.append(features)
            y_mid = (min_salary + max_salary) / 2.0
            y_spread = max_salary - min_salary
            labels.append([y_mid, y_spread])

        if len(rows) < 5:
            logger.warning("[Auto-Retrain] Quá ít mẫu hợp lệ để train (yêu cầu ít nhất 5 mẫu).")
            return

        X = np.array(rows)
        y = np.array(labels)

        # Định nghĩa bộ XGBoost Regressor
        model = MultiOutputRegressor(
            XGBRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1,
                tree_method="hist",
            )
        )
        
        # Fit model bằng thread executor để tránh blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, model.fit, X, y)
        
        # Lưu file
        joblib.dump(model, settings.MODEL_PATH)
        
        # Clear model cache trong bộ nhớ
        reload_model()
        
        # Cập nhật metadata trong MongoDB
        meta_col = get_model_metadata_col()
        await meta_col.replace_one(
            {"key": "salary_model_metadata"},
            {
                "key": "salary_model_metadata",
                "last_trained_count": current_count,
                "last_trained_at": datetime.now(),
            },
            upsert=True
        )
        logger.info(f"[Auto-Retrain] Đã tự động huấn luyện xong model thành công tại {datetime.now()} với {current_count} mẫu.")
    except Exception as ex:
        logger.error(f"[Auto-Retrain] Lỗi trong quá trình train model: {ex}")

async def _check_and_trigger_retrain():
    """Kiểm tra ngưỡng chênh lệch mẫu mới để tự động chạy train."""
    try:
        col = get_salary_dataset_col()
        current_count = await col.count_documents({})
        
        meta_col = get_model_metadata_col()
        meta = await meta_col.find_one({"key": "salary_model_metadata"})
        
        last_trained_count = 0
        if meta:
            last_trained_count = meta.get("last_trained_count", 0)
        else:
            # Lần đầu khởi tạo, lưu mốc count hiện tại làm mốc huấn luyện gốc
            await meta_col.insert_one({
                "key": "salary_model_metadata",
                "last_trained_count": current_count,
                "last_trained_at": datetime.now()
            })
            return

        # Trigger train nếu có thêm từ 50 mẫu trở lên
        if current_count - last_trained_count >= 50:
            await _run_background_retrain(current_count)
    except Exception as ex:
        logger.error(f"[Auto-Retrain] Lỗi kiểm tra ngưỡng train: {ex}")

from app.models.documents import (
    SalaryDataset,
    SalaryPredictionCache,
    JobTrendSnapshot,
)
from app.schemas.analytics import (
    SalaryPredictRequest,
    SalaryPredictResponse,
    AddSalaryDataRequest,
    TrendRequest,
    TrendResponse,
    TrendDataPoint,
)

logger = logging.getLogger(__name__)


# ── Salary Prediction ─────────────────────────────────────────────────────────
async def predict(req: SalaryPredictRequest) -> SalaryPredictResponse:
    """
    Dự đoán lương với cache:
    1. Tính hash bộ input.
    2. Tra cứu MongoDB — nếu có → trả về cache ngay.
    3. Không có → Gọi XGBoost model predict → Lưu cache → Trả về.
    """
    input_hash = make_input_hash(
        req.job_title, req.years_of_experience, req.skill_set, req.location, req.level
    )

    # Kiểm tra cache
    cache_col = get_salary_cache_col()
    cached = await cache_col.find_one({"input_hash": input_hash})
    if cached:
        logger.info(f"[Salary] Cache hit: {input_hash[:8]}...")
        return SalaryPredictResponse(
            min_salary=cached["min_salary"],
            max_salary=cached["max_salary"],
            confidence=cached["confidence"],
            model_version=cached["model_version"],
            from_cache=True,
        )

    # Cache miss → gọi model
    result = predict_salary(
        req.job_title, req.years_of_experience, req.skill_set, req.location, req.level
    )

    # Lưu vào cache
    cache_doc = SalaryPredictionCache(
        input_hash=input_hash,
        **result,
    )
    await cache_col.insert_one(cache_doc.model_dump(exclude={"id"}))

    return SalaryPredictResponse(**result, from_cache=False)


async def add_salary_data(req: AddSalaryDataRequest) -> dict:
    """Thêm 1 bản ghi lương thực tế vào dataset (để dùng cho lần retrain tiếp theo)."""
    doc = SalaryDataset(
        job_title=req.job_title,
        years_of_experience=req.years_of_experience,
        skill_set=req.skill_set,
        location=req.location,
        level=req.level,
        salary_min=req.salary_min,
        salary_max=req.salary_max,
        is_negotiable=req.is_negotiable,
        source=req.source,
    )
    col = get_salary_dataset_col()
    await col.insert_one(doc.model_dump(exclude={"id"}))
    
    # Tạo background task kiểm tra & tự động train lại mô hình
    asyncio.create_task(_check_and_trigger_retrain())
    
    return {"message": "Đã thêm dữ liệu lương thành công. Dataset hiện có thêm 1 mẫu."}


async def get_dataset_stats() -> dict:
    """Thống kê nhanh dataset hiện tại."""
    col = get_salary_dataset_col()
    total = await col.count_documents({})
    return {"total_samples": total, "message": "Chạy scripts/train_salary_model.py để retrain sau khi có đủ dữ liệu mới."}


# ── Job Trend ─────────────────────────────────────────────────────────────────
async def get_trend(req: TrendRequest) -> TrendResponse:
    """
    Lấy dữ liệu lịch sử xu hướng của 1 kỹ năng từ MongoDB.
    Kết hợp với dự báo đơn giản dựa trên moving average (Prophet training offline).
    """
    col = get_job_trend_col()
    docs = await col.find({"skill_name": req.skill_name}).sort([("year", 1), ("month", 1)]).to_list(length=None)

    history = [
        TrendDataPoint(
            month=d["month"],
            year=d["year"],
            job_count=d["job_count"],
            avg_salary=d["avg_salary"],
        )
        for d in docs
    ]

    # Dự báo đơn giản: Moving Average 3 tháng cuối (sẽ thay bằng Prophet sau khi có đủ data)
    forecast = _simple_moving_avg_forecast(history, months=req.months)

    return TrendResponse(skill_name=req.skill_name, history=history, forecast=forecast)


async def record_trend_snapshot(
    skill_id: str, skill_name: str, month: int, year: int,
    job_count: int, avg_salary: float,
) -> dict:
    """Ghi snapshot tháng này cho 1 kỹ năng (thường gọi bằng Scheduled Task / Event)."""
    col = get_job_trend_col()
    doc = JobTrendSnapshot(
        skill_id=skill_id,
        skill_name=skill_name,
        month=month, year=year,
        job_count=job_count,
        avg_salary=avg_salary,
    )
    await col.replace_one(
        {"skill_id": skill_id, "month": month, "year": year},
        doc.model_dump(exclude={"id"}),
        upsert=True,
    )
    return {"message": "Đã ghi snapshot xu hướng."}


def _simple_moving_avg_forecast(history: list[TrendDataPoint], months: int) -> list[TrendDataPoint]:
    """Dự báo có tính toán xu hướng (slope), damping và dao động ngẫu nhiên ổn định."""
    if len(history) < 3:
        return []
        
    p1 = history[-3]
    p3 = history[-1]
    
    # Tính xu hướng tăng/giảm mỗi tháng từ 3 tháng gần nhất
    slope_jobs = (p3.job_count - p1.job_count) / 2.0
    slope_sal = (p3.avg_salary - p1.avg_salary) / 2.0
    
    # Giới hạn gia tốc tăng/giảm đột biến để tránh số âm hoặc quá lớn
    max_job_delta = p3.job_count * 0.08
    max_sal_delta = p3.avg_salary * 0.04
    slope_jobs = max(-max_job_delta, min(max_job_delta, slope_jobs))
    slope_sal = max(-max_sal_delta, min(max_sal_delta, slope_sal))
    
    result = []
    m, y = p3.month, p3.year
    curr_jobs = float(p3.job_count)
    curr_sal = float(p3.avg_salary)
    
    import random
    for step in range(1, months + 1):
        m += 1
        if m > 12:
            m = 1
            y += 1
            
        # Sử dụng seed cố định theo tháng, năm và độ dài lịch sử để đường biểu đồ ổn định khi query lại
        random.seed(m * 1000 + y + len(history))
        
        # Biến động thị trường ngẫu nhiên nhỏ (±3% jobs, ±1% salary)
        noise_jobs = random.uniform(0.97, 1.03)
        noise_sal = random.uniform(0.99, 1.01)
        
        # Tính lũy kế xu hướng với hệ số giảm chấn (damping factor)
        damping = 0.88 ** (step - 1)
        curr_jobs = max(1.0, curr_jobs + slope_jobs * damping)
        curr_sal = max(1.0, curr_sal + slope_sal * damping)
        
        final_jobs = int(curr_jobs * noise_jobs)
        final_sal = round(curr_sal * noise_sal, 2)
        
        result.append(TrendDataPoint(
            month=m, year=y,
            job_count=max(1, final_jobs),
            avg_salary=final_sal,
        ))
        
    random.seed() # Reset seed
    return result
