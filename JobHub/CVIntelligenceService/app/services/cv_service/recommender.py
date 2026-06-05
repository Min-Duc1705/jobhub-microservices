# app/services/cv_service/recommender.py
"""
Hybrid Recommendation Engine: kết hợp SBERT matching với Collaborative Filtering (SVD).
"""
import asyncio
import hashlib
import logging
import re
import time
import urllib.request
import json

from app.ml.sbert_scorer import batch_score_cvs
from .svd_engine import get_svd_scores

logger = logging.getLogger(__name__)

# Cache kết quả recommendations (5 phút TTL)
_RECOMMENDATIONS_CACHE: dict[str, tuple[float, list]] = {}
_CACHE_TTL = 300  # seconds


def _clean_cv_text(text: str) -> str:
    """Xóa các phần không liên quan (cam kết, hành chính) để cải thiện chất lượng SBERT."""
    if not text:
        return ""

    multiline_patterns = [
        r"Bạn vui lòng trả lời các câu hỏi sau:[\s\S]*",
        r"Sau khi nghiên cứu nội dung thông báo tuyển dụng[\s\S]*",
        r"Tôi xin cam đoan:[\s\S]*",
        r"Người đăng ký dự tuyển[\s\S]*",
    ]
    cleaned = text
    for pattern in multiline_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    singleline_patterns = [
        r"Kính gửi:.*", r"Hộ khẩu thường trú.*", r"Địa chỉ đang ở.*",
        r"Địa chỉ báo tin.*", r"Số chứng minh nhân dân.*", r"Số định danh cá nhân.*",
        r"Ngày cấp:.*", r"Hồ sơ đính kèm:.*", r"Application ID:.*",
        r"Candidate ID:.*", r"Resume title:.*", r"Resume type:.*", r"Cover letter:.*"
    ]
    for pattern in singleline_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    return re.sub(r"\s+", " ", cleaned).strip()


def _is_skill_in_text(skill: str, text: str) -> bool:
    """Kiểm tra một kỹ năng có xuất hiện trong văn bản không (word-boundary safe)."""
    skill_lower = skill.lower().strip()
    text_lower = text.lower()

    if not skill_lower or not text_lower:
        return False

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
    3. Chấm điểm SBERT (độ trùng khớp kỹ năng & mô tả) → sbert_score.
    4. Đối sánh kỹ năng cứng (Skill overlap) giữa Job và CV để phạt điểm lệch ngành.
    5. Nếu có customer_id, chạy mô hình Collaborative Filtering (SVD) → svd_score.
    6. Trộn điểm số: matching_score = 0.6 * sbert_score + 0.4 * svd_score.
    7. Trả về danh sách công việc phù hợp nhất xếp hạng giảm dần.
    """
    if not cv_text:
        return []

    # ── Check Cache ──
    cache_key = (
        f"cust:{customer_id}"
        if customer_id
        else f"cv:{hashlib.md5(cv_text.encode('utf-8', errors='ignore')).hexdigest()}"
    )

    now = time.time()
    if cache_key in _RECOMMENDATIONS_CACHE:
        cache_time, cached_result = _RECOMMENDATIONS_CACHE[cache_key]
        if now - cache_time < _CACHE_TTL:
            logger.info(f"[Recommender] Cache hit for {cache_key}")
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

        job_texts = [
            f"Title: {j.get('name', '')}\nDescription: {j.get('description', '')}\nRequirements: {j.get('requirements', '')}"
            for j in jobs
        ]

        scores = batch_score_cvs(cleaned_cv, job_texts)

        # SVD scores nếu có customer_id
        svd_scores_map = {}
        precomputed = get_svd_scores()
        if customer_id and customer_id in precomputed:
            svd_scores_map = precomputed[customer_id]

        scored_jobs = []
        for job, sbert_score in zip(jobs, scores):
            jid = job.get("id")

            hybrid_score = sbert_score
            if jid in svd_scores_map:
                hybrid_score = 0.6 * sbert_score + 0.4 * svd_scores_map[jid]

            # Boost: sqrt(x)*10
            hybrid_score = (max(0.0, hybrid_score) ** 0.5) * 10

            # Skill Overlap Heuristic
            job_skills = [s.get("name") for s in job.get("skills", []) if s.get("name")]
            if job_skills:
                matched_skills = [s for s in job_skills if _is_skill_in_text(s, cleaned_cv)]
                match_ratio = len(matched_skills) / len(job_skills)

                if match_ratio < 0.25:
                    hybrid_score *= 0.5
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
        logger.error(f"[Recommender] Lỗi khi gợi ý việc làm: {e}")
        return []
