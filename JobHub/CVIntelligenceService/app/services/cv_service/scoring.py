# app/services/cv_service/scoring.py
"""
CV Scoring service: SBERT-based scoring, penalty computation và lưu kết quả.
"""
import logging
import re

from app.core.database import get_resume_analysis_col
from app.ml.sbert_scorer import score_cv, batch_score_cvs
from app.ml.llm_generator import generate_feedback
from app.models.documents import ResumeAnalysis
from app.schemas.cv_scoring import (
    CvScoringRequest,
    SkillScoringRequest,
    BatchScoringResponse,
    ScoringResult,
)

logger = logging.getLogger(__name__)

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
    return [pat for pat in _TECH_SKILL_PATTERNS if re.search(pat, text_lower)]


def _compute_skill_penalty(jd_skills: list[str], cv_text: str) -> float:
    """
    Tính hệ số phạt dựa trên tỉ lệ kỹ năng JD xuất hiện trong CV.
    - match_ratio >= 0.5  → không phạt (×1.0)
    - match_ratio >= 0.25 → phạt nhẹ (×0.7)
    - match_ratio >  0    → phạt vừa (×0.5)
    - match_ratio =  0    → phạt nặng (×0.2)
    """
    if not jd_skills:
        return 1.0
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


def _compute_seniority_penalty(jd_text: str, cv_text: str) -> float:
    """
    Áp dụng hình phạt nếu có sự lệch lớn về cấp bậc (Seniority Mismatch).
    Đặc biệt là khi Job yêu cầu Senior/Leader/Manager mà CV chỉ ở mức Intern/Fresher.
    """
    jd_lower = jd_text.lower()
    cv_lower = cv_text.lower()

    high_level_patterns = [
        r"\bsenior\b", r"\blead\b", r"\btrưởng nhóm\b", r"\btrưởng phòng\b",
        r"\bquản lý\b", r"\bmanager\b", r"\btech lead\b", r"\bchủ chốt\b",
        r"\barchitect\b", r"\bchuyên gia\b", r"\b3\s*năm kinh nghiệm\b",
        r"\b5\s*năm kinh nghiệm\b", r"\b6\s*năm kinh nghiệm\b"
    ]
    is_job_high_level = any(re.search(pat, jd_lower) for pat in high_level_patterns)

    fresher_patterns = [
        r"\bintern\b", r"\bfresher\b", r"\bthực tập sinh\b", r"\bthực tập\b",
        r"\bsinh viên năm\b", r"\bchưa có kinh nghiệm\b", r"\bmới ra trường\b",
        r"\bhọc việc\b", r"\b0\s*-\s*1\s*năm kinh nghiệm\b", r"\bchưa có kinh nghiệm thực tế\b"
    ]
    is_candidate_fresher = any(re.search(pat, cv_lower) for pat in fresher_patterns)

    if is_job_high_level and is_candidate_fresher:
        logger.info("[SeniorityPenalty] Lệch cấp bậc: Senior JD vs Fresher CV. Phạt x0.35")
        return 0.35

    return 1.0


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


async def score_single_cv(req: CvScoringRequest) -> ScoringResult:
    """
    Bước 1: SBERT chấm điểm 1 CV với JD.
    Bước 1.5: Áp dụng Hard Skill Penalty & Seniority Penalty.
    Bước 2 (tuỳ chọn): Nếu có application_id → sinh feedback bằng LLM và lưu vào MongoDB.
    """
    raw_score = score_cv(req.job_description, req.cv_text)

    jd_skills = _extract_tech_skills(req.job_description)
    skill_penalty = _compute_skill_penalty(jd_skills, req.cv_text)
    seniority_penalty = _compute_seniority_penalty(req.job_description, req.cv_text)

    # Boost scores: sqrt(x)*10 mapping (0→0, 50→70.7, 100→100)
    final_raw_score = raw_score * skill_penalty * seniority_penalty
    score = round((max(0.0, final_raw_score) ** 0.5) * 10, 2)

    if skill_penalty < 1.0 or seniority_penalty < 1.0:
        logger.info(
            f"[Score] SBERT={raw_score:.1f} → skill_penalty={skill_penalty}, "
            f"seniority_penalty={seniority_penalty} → final={score:.1f}"
        )

    feedback_data = {"extracted_skills": [], "strengths": [], "weaknesses": [], "ai_feedback": None}

    if req.generate_feedback and score >= 50.0:
        feedback_data = await generate_feedback(req.job_description, req.cv_text)

    result = ScoringResult(application_id=req.application_id, matching_score=score, **feedback_data)

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
    raw_scores = batch_score_cvs(req.job_description, cv_texts)

    jd_skills = _extract_tech_skills(req.job_description)
    final_scores = []
    for cv_text, raw_score in zip(cv_texts, raw_scores):
        skill_penalty = _compute_skill_penalty(jd_skills, cv_text)
        seniority_penalty = _compute_seniority_penalty(req.job_description, cv_text)
        final_raw_score = raw_score * skill_penalty * seniority_penalty
        final_scores.append(round((max(0.0, final_raw_score) ** 0.5) * 10, 2))

    scored = sorted(zip(req.cv_list, final_scores), key=lambda x: x[1], reverse=True)

    results = []
    for idx, (cv_item, score) in enumerate(scored):
        feedback_data = {"extracted_skills": [], "strengths": [], "weaknesses": [], "ai_feedback": None}

        # Không sinh feedback tự động bằng LLM ở đây để tránh làm chậm và tốn quota.
        # Feedback chi tiết sẽ được sinh on-demand (khi NTD click xem chi tiết ứng viên).
        pass

        res_item = ScoringResult(
            application_id=cv_item.get("application_id"),
            matching_score=score,
            **feedback_data,
        )
        results.append(res_item)

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
