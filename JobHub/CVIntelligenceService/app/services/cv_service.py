import logging
import urllib.request
import json
import re
import asyncio
from datetime import datetime
import numpy as np
from sklearn.decomposition import TruncatedSVD
import hashlib
import time

# Cache cho API recommendations
_RECOMMENDATIONS_CACHE = {}
_CACHE_TTL = 300  # 5 phút

# Cache điểm số SVD được tính toán ngầm
_PRECOMPUTED_SVD_SCORES = {}

from app.core.database import get_resume_analysis_col, get_job_view_history_col
from app.ml.sbert_scorer import score_cv, batch_score_cvs
from app.ml.llm_generator import generate_feedback
from app.models.documents import ResumeAnalysis, JobViewHistory
from app.schemas.cv_scoring import (
    CvScoringRequest,
    SkillScoringRequest,
    BatchScoringResponse,
    ScoringResult,
    TrackInteractionRequest,
)

logger = logging.getLogger(__name__)

# Trọng số tương tác cho Recommendation Engine
_INTERACTION_SCORES = {
    "VIEW":  1.0,
    "CLICK": 2.0,
    "SAVE":  3.0,
    "APPLY": 5.0,
}


# Danh sách công nghệ cụ thể để phát hiện kỹ năng cứng từ JD
_TECH_SKILL_PATTERNS = [
    # Backend languages/frameworks
    r"\bjava\b", r"\bpython\b", r"\bc#\b", r"\b\.net\b", r"\bgo\b", r"\brust\b",
    r"\bkotlin\b", r"\bscala\b", r"\bphp\b", r"\bruby\b",
    # Frontend
    r"\breact\b", r"\bvue\b", r"\bangular\b", r"\bsvelte\b", r"\bnext\.?js\b",
    r"\btypescript\b", r"\bjavascript\b", r"\bhtml\b", r"\bcss\b",
    # Mobile
    r"\bswift\b", r"\bswiftui\b", r"\buikit\b", r"\bflutter\b", r"\breact native\b",
    r"\bandroid\b", r"\bios\b", r"\bxcode\b",
    # Databases
    r"\bsql\b", r"\bpostgresql\b", r"\bmysql\b", r"\bmongodb\b", r"\boracle\b",
    r"\bredis\b", r"\belasticsearch\b", r"\bcassandra\b",
    # Cloud/DevOps
    r"\baws\b", r"\bazure\b", r"\bgcp\b", r"\bdocker\b", r"\bkubernetes\b",
    r"\bterraform\b", r"\bjenkins\b", r"\bgithub actions\b",
    # Architecture
    r"\bmicroservices\b", r"\bgraphql\b", r"\bgrpc\b", r"\bkafka\b", r"\brabbitmq\b",
    # Data/ML
    r"\bmachine learning\b", r"\bdeep learning\b", r"\btensorflow\b",
    r"\bpytorch\b", r"\bpandas\b", r"\bspark\b",
    # Storage
    r"\bs3\b", r"\bminio\b",
    # Spring
    r"\bspring\b", r"\bspring boot\b", r"\bhibernate\b",
]

def _extract_tech_skills(text: str) -> list[str]:
    """Trích xuất danh sách kỹ năng công nghệ cụ thể từ văn bản."""
    text_lower = text.lower()
    found = []
    for pattern in _TECH_SKILL_PATTERNS:
        if re.search(pattern, text_lower):
            found.append(pattern)
    return found

def _compute_skill_penalty(jd_skills: list[str], cv_text: str) -> float:
    """
    Tính hệ số phạt dựa trên tỉ lệ kỹ năng JD xuất hiện trong CV.
    - match_ratio >= 0.5  → không phạt (×1.0)
    - match_ratio >= 0.25 → phạt nhẹ (×0.7)
    - match_ratio > 0     → phạt vừa (×0.5)
    - match_ratio = 0     → phạt nặng (×0.2) — hoàn toàn khác domain
    """
    if not jd_skills:
        return 1.0  # Không có kỹ năng nào xác định được → không phạt

    cv_lower = cv_text.lower()
    matched = [s for s in jd_skills if re.search(s, cv_lower)]
    ratio = len(matched) / len(jd_skills)

    if ratio >= 0.5:
        return 1.0
    elif ratio >= 0.25:
        return 0.7
    elif ratio > 0:
        return 0.5
    else:
        return 0.2


async def score_single_cv(req: CvScoringRequest) -> ScoringResult:
    """
    Bước 1: SBERT chấm điểm 1 CV với JD.
    Bước 1.5: Áp dụng Hard Skill Penalty — nếu kỹ năng công nghệ trong JD
              không xuất hiện trong CV thì giảm mạnh điểm (tránh match ngữ nghĩa chung).
    Bước 2 (tuỳ chọn): Nếu có application_id → sinh feedback bằng LLM và lưu vào MongoDB.
    """
    raw_score = score_cv(req.job_description, req.cv_text)

    # Hard Skill Penalty
    jd_skills = _extract_tech_skills(req.job_description)
    penalty = _compute_skill_penalty(jd_skills, req.cv_text)
    score = round(raw_score * penalty, 2)

    if penalty < 1.0:
        logger.info(
            f"[HireAgent-Score] SBERT={raw_score:.1f} → "
            f"penalty={penalty} (skills matched {len([s for s in jd_skills if re.search(s, req.cv_text.lower())])}/{len(jd_skills)}) "
            f"→ final={score:.1f}"
        )

    feedback_data = {"extracted_skills": [], "strengths": [], "weaknesses": [], "ai_feedback": None}

    # Chỉ gọi LLM khi score > 50% để tiết kiệm chi phí
    if score >= 50.0:
        feedback_data = await generate_feedback(req.job_description, req.cv_text)

    result = ScoringResult(
        application_id=req.application_id,
        matching_score=score,
        **feedback_data,
    )

    # Lưu vào MongoDB nếu có đủ thông tin
    if req.application_id and req.job_id and req.customer_id:
        await _save_analysis(req, result)

    return result


async def batch_score(req: SkillScoringRequest, top_n: int = 10) -> BatchScoringResponse:
    """
    Pipeline 2 bước chuẩn công nghiệp:
    Bước 1: SBERT chấm hàng loạt tất cả CVs — cực nhanh (GPU).
    Bước 2: Chỉ top_n CV điểm cao nhất mới gọi LLM sinh nhận xét chi tiết.
    """
    cv_texts = [item["cv_text"] for item in req.cv_list]
    scores = batch_score_cvs(req.job_description, cv_texts)

    # Gắn điểm vào từng CV và sắp xếp giảm dần
    scored = sorted(
        zip(req.cv_list, scores),
        key=lambda x: x[1],
        reverse=True,
    )

    results = []
    for idx, (cv_item, score) in enumerate(scored):
        feedback_data = {"extracted_skills": [], "strengths": [], "weaknesses": [], "ai_feedback": None}

        # Chỉ gọi LLM cho top-N CV tốt nhất
        if idx < top_n and score >= 40.0:
            feedback_data = await generate_feedback(req.job_description, cv_item["cv_text"])

        res_item = ScoringResult(
            application_id=cv_item.get("application_id"),
            matching_score=score,
            **feedback_data,
        )
        results.append(res_item)

        # Lưu vào MongoDB nếu có đủ thông tin
        app_id = cv_item.get("application_id")
        job_id = cv_item.get("job_id")
        cust_id = cv_item.get("customer_id")
        if app_id and job_id and cust_id:
            fake_req = CvScoringRequest(
                job_description=req.job_description,
                cv_text=cv_item["cv_text"],
                application_id=app_id,
                job_id=job_id,
                customer_id=cust_id
            )
            await _save_analysis(fake_req, res_item)

    return BatchScoringResponse(results=results, top_count=min(top_n, len(results)))


async def track_interaction(req: TrackInteractionRequest) -> dict:
    """Ghi log hành vi người dùng với Job (VIEW/CLICK/SAVE/APPLY)."""
    score = _INTERACTION_SCORES.get(req.interaction_type.upper(), 1.0)
    doc = JobViewHistory(
        customer_id=req.customer_id,
        job_id=req.job_id,
        interaction_type=req.interaction_type.upper(),
        interaction_score=score,
        timestamp=datetime.utcnow(),
    )
    col = get_job_view_history_col()
    await col.insert_one(doc.model_dump(exclude={"id"}))
    return {"message": "Ghi log thành công"}


async def get_analyses_by_job(job_id: str) -> list:
    """Lấy tất cả kết quả phân tích CV của 1 Job — HR dùng để xem bảng xếp hạng."""
    col = get_resume_analysis_col()
    docs = await col.find({"job_id": job_id}).sort("matching_score", -1).to_list(length=None)
    for doc in docs:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
    return docs


# ── Internal Helpers ───────────────────────────────────────────────────────────
async def _save_analysis(req: CvScoringRequest, result: ScoringResult):
    doc = ResumeAnalysis(
        application_id=req.application_id,
        job_id=req.job_id,
        customer_id=req.customer_id,
        matching_score=result.matching_score,
        extracted_skills=result.extracted_skills,
        strengths=result.strengths,
        weaknesses=result.weaknesses,
        ai_feedback=result.ai_feedback,
    )
    col = get_resume_analysis_col()
    await col.replace_one(
        {"application_id": req.application_id},
        doc.model_dump(exclude={"id"}),
        upsert=True,
    )


async def train_and_cache_svd_for_all_users() -> dict:
    """
    Huấn luyện SVD cho TOÀN BỘ người dùng cùng lúc từ dữ liệu MongoDB,
    sau đó lưu vào biến cache toàn cục _PRECOMPUTED_SVD_SCORES.
    """
    global _PRECOMPUTED_SVD_SCORES
    col = get_job_view_history_col()
    cursor = col.find({}, {"customer_id": 1, "job_id": 1, "interaction_score": 1})
    docs = await cursor.to_list(length=None)
    
    if not docs:
        _PRECOMPUTED_SVD_SCORES = {}
        return {}

    user_item_scores = {}
    unique_users = set()
    unique_jobs = set()
    
    for doc in docs:
        uid = doc.get("customer_id")
        jid = doc.get("job_id")
        score = doc.get("interaction_score", 1.0)
        if uid and jid:
            user_item_scores[(uid, jid)] = user_item_scores.get((uid, jid), 0.0) + score
            unique_users.add(uid)
            unique_jobs.add(jid)

    num_users = len(unique_users)
    num_jobs = len(unique_jobs)
    
    if num_users < 3 or num_jobs < 3 or len(user_item_scores) < 5:
        logger.info("[SVD] Chưa đủ dữ liệu tương tác để huấn luyện SVD. Reset cache về rỗng.")
        _PRECOMPUTED_SVD_SCORES = {}
        return {}

    user_to_idx = {uid: idx for idx, uid in enumerate(unique_users)}
    job_to_idx = {jid: idx for idx, jid in enumerate(unique_jobs)}
    idx_to_job = {idx: jid for jid, idx in job_to_idx.items()}

    R = np.zeros((num_users, num_jobs))
    for (uid, jid), score in user_item_scores.items():
        R[user_to_idx[uid], job_to_idx[jid]] = score

    n_components = max(1, min(10, num_users - 1, num_jobs - 1))
    
    try:
        svd = TruncatedSVD(n_components=n_components, random_state=42)
        user_embeddings = svd.fit_transform(R)
        item_embeddings = svd.components_.T
        
        R_pred = np.dot(user_embeddings, item_embeddings.T)
        
        new_scores = {}
        for uid in unique_users:
            u_idx = user_to_idx[uid]
            pred_ratings = R_pred[u_idx]
            
            min_r = float(np.min(pred_ratings))
            max_r = float(np.max(pred_ratings))
            
            user_scores = {}
            for idx, rating in enumerate(pred_ratings):
                jid = idx_to_job[idx]
                if max_r > min_r:
                    norm_score = ((rating - min_r) / (max_r - min_r)) * 100.0
                else:
                    norm_score = 50.0
                user_scores[jid] = round(norm_score, 2)
            new_scores[uid] = user_scores
            
        _PRECOMPUTED_SVD_SCORES = new_scores
        logger.info(f"[SVD] Huấn luyện SVD offline thành công cho {num_users} users, {num_jobs} jobs, latent={n_components}.")
        return _PRECOMPUTED_SVD_SCORES
        
    except Exception as ex:
        logger.error(f"[SVD] Lỗi khi huấn luyện SVD offline: {ex}")
        return {}


async def start_periodic_svd_training(interval_seconds: int = 4 * 3600):
    """Bắt đầu vòng lặp huấn luyện SVD định kỳ chạy ngầm."""
    logger.info("[SVD Loop] Đã khởi động luồng huấn luyện SVD chạy ngầm.")
    while True:
        try:
            await train_and_cache_svd_for_all_users()
        except Exception as e:
            logger.error(f"[SVD Loop] Lỗi khi huấn luyện SVD định kỳ: {e}")
        await asyncio.sleep(interval_seconds)


def _clean_cv_text(text: str) -> str:
    if not text:
        return ""
    
    # 1. Loại bỏ các phần khảo sát/cam kết ở cuối CV (khớp nhiều dòng)
    multiline_patterns = [
        r"Bạn vui lòng trả lời các câu hỏi sau:[\s\S]*",
        r"Sau khi nghiên cứu nội dung thông báo tuyển dụng[\s\S]*",
        r"Tôi xin cam đoan:[\s\S]*",
        r"Người đăng ký dự tuyển[\s\S]*",
    ]
    
    cleaned = text
    for pattern in multiline_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        
    # 2. Loại bỏ thông tin cá nhân/hành chính (khớp đơn dòng)
    singleline_patterns = [
        r"Kính gửi:.*",
        r"Hộ khẩu thường trú.*",
        r"Địa chỉ đang ở.*",
        r"Địa chỉ báo tin.*",
        r"Số chứng minh nhân dân.*",
        r"Số định danh cá nhân.*",
        r"Ngày cấp:.*",
        r"Hồ sơ đính kèm:.*",
        r"Application ID:.*",
        r"Candidate ID:.*",
        r"Resume title:.*",
        r"Resume type:.*",
        r"Cover letter:.*"
    ]
    
    for pattern in singleline_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _is_skill_in_text(skill: str, text: str) -> bool:
    skill_lower = skill.lower().strip()
    text_lower = text.lower()
    
    if not skill_lower or not text_lower:
        return False
        
    # Nếu skill bắt đầu bằng dấu chấm (như .net, .js), ta không chặn phía trước bằng (?<!\w)
    if skill_lower.startswith("."):
        pattern = re.escape(skill_lower) + r"(?!\w)"
    else:
        pattern = r"(?<!\w)" + re.escape(skill_lower) + r"(?!\w)"
        
    return bool(re.search(pattern, text_lower))



async def recommend_jobs_for_candidate(cv_text: str, customer_id: str = None) -> list:
    """
    Gợi ý việc làm lai (Hybrid Recommendation):
    1. Lấy danh sách tối đa 100 công việc đang tuyển dụng từ JobService.
    2. Làm sạch văn bản CV để loại bỏ nhiễu hành chính/khảo sát.
    3. Chấm điểm SBERT (độ trùng khớp kỹ năng & mô tả) -> sbert_score.
    4. Đối sánh kỹ năng cứng (Skill overlap) giữa Job và CV để phạt điểm lệch ngành.
    5. Nếu có customer_id, chạy mô hình Collaborative Filtering (Matrix Factorization SVD) -> svd_score.
    6. Trộn điểm số: matching_score = 0.6 * sbert_score + 0.4 * svd_score.
    7. Trả về danh sách công việc phù hợp nhất xếp hạng giảm dần.
    """
    if not cv_text:
        return []

    # ── Check Cache ──
    if customer_id:
        cache_key = f"cust:{customer_id}"
    else:
        cv_hash = hashlib.md5(cv_text.encode('utf-8', errors='ignore')).hexdigest()
        cache_key = f"cv:{cv_hash}"

    now = time.time()
    if cache_key in _RECOMMENDATIONS_CACHE:
        cache_time, cached_result = _RECOMMENDATIONS_CACHE[cache_key]
        if now - cache_time < _CACHE_TTL:
            logger.info(f"[Recommendation] Cache hit for {cache_key}")
            return cached_result

    try:
        url = "http://jobhub_jobservice:8080/api/v1/jobs?pageSize=100"
        
        loop = asyncio.get_event_loop()
        def fetch_jobs():
            with urllib.request.urlopen(url, timeout=5) as response:
                return json.loads(response.read().decode())

        res = await loop.run_in_executor(None, fetch_jobs)
        jobs = res.get("data", {}).get("result", [])

        if not jobs:
            return []

        cleaned_cv = _clean_cv_text(cv_text)

        job_texts = []
        for job in jobs:
            title = job.get("name") or ""
            desc = job.get("description") or ""
            req = job.get("requirements") or ""
            job_text = f"Title: {title}\nDescription: {desc}\nRequirements: {req}"
            job_texts.append(job_text)

        scores = batch_score_cvs(cleaned_cv, job_texts)

        svd_scores = {}
        if customer_id and customer_id in _PRECOMPUTED_SVD_SCORES:
            svd_scores = _PRECOMPUTED_SVD_SCORES[customer_id]

        scored_jobs = []
        for job, sbert_score in zip(jobs, scores):
            jid = job.get("id")
            
            hybrid_score = sbert_score
            if jid in svd_scores:
                svd_score = svd_scores[jid]
                hybrid_score = 0.6 * sbert_score + 0.4 * svd_score
            
            # Áp dụng bộ phạt/thưởng đối sánh kỹ năng cứng (Skill Overlap Heuristic)
            job_skills = [s.get("name") for s in job.get("skills", []) if s.get("name")]
            if job_skills:
                matched_skills = [s for s in job_skills if _is_skill_in_text(s, cleaned_cv)]
                match_ratio = len(matched_skills) / len(job_skills)
                
                # Nếu tỷ lệ khớp quá thấp (hoặc 0 kỹ năng khớp), giảm 50% điểm số
                if match_ratio < 0.25:
                    hybrid_score = hybrid_score * 0.5
                # Nếu tỷ lệ khớp tốt (khớp >= 50%), thưởng 10% điểm số (tối đa 100)
                elif match_ratio >= 0.5:
                    hybrid_score = min(100.0, hybrid_score * 1.1)
                
            job_copy = dict(job)
            job_copy["matching_score"] = round(hybrid_score, 2)
            scored_jobs.append(job_copy)

        scored_jobs.sort(key=lambda x: x["matching_score"], reverse=True)
        final_recs = scored_jobs[:6]
        _RECOMMENDATIONS_CACHE[cache_key] = (now, final_recs)
        return final_recs

    except Exception as e:
        logger.error(f"[Recommendation] Lỗi khi gợi ý việc làm: {e}")
        return []

