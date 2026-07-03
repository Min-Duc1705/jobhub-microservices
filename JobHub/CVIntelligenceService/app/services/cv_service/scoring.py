# app/services/cv_service/scoring.py
"""
CV Scoring service: SBERT-based scoring, penalty computation và lưu kết quả.
"""
import logging
import re
import urllib.request
import json

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
    # Embedded / Systems Programming
    r"\bc\b", r"\bc\+\+\b", r"\bcpp\b", r"\blinux\b", r"\bembedded\b", r"\bnhúng\b",
    r"\bspi\b", r"\bi2c\b", r"\buart\b", r"\bcan bus\b",
    r"\barm\b", r"\bcortex\b", r"\bstm32\b", r"\besp32\b",
    r"\brtos\b", r"\bfree rtos\b", r"\bfreertos\b",
    r"\bfirmware\b", r"\bmicrocontroller\b", r"\bvi điều khiển\b",
]


def _extract_tech_skills(text: str) -> list[str]:
    """Trích xuất danh sách kỹ năng công nghệ cụ thể từ văn bản."""
    text_lower = text.lower()
    extracted = []
    for pat in _TECH_SKILL_PATTERNS:
        match = re.search(pat, text_lower)
        if match:
            extracted.append(match.group(0).strip())
    return extracted


async def _fetch_job_skills_from_api(job_id: str) -> list[str]:
    """
    Gọi API của JobService để lấy danh sách kỹ năng thực tế của Job.
    Sử dụng Redis cache để tối ưu hóa, hỗ trợ cả môi trường Docker và Local.
    """
    if not job_id:
        return []

    redis_key = f"JobHubAuth_job_skills:{job_id}"
    try:
        from app.routers.assistant_router_helpers import redis_client
        cached_data = await redis_client.get(redis_key)
        if cached_data:
            skills = json.loads(cached_data)
            if isinstance(skills, list):
                logger.info(f"[SkillsCache] Redis hit: Loaded {len(skills)} skills for job {job_id} from cache.")
                return skills
    except Exception as e:
        logger.error(f"[SkillsCache] Failed to fetch/parse job skills from Redis: {e}")

    urls = [
        f"http://jobhub_jobservice:8080/api/v1/jobs/{job_id}/preview",
        f"http://localhost:5002/api/v1/jobs/{job_id}/preview"
    ]
    skills = []
    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    job_data = data.get("data", {})
                    if job_data:
                        skills = [s.get("name") for s in job_data.get("skills", []) if s.get("name")]
                        if skills:
                            logger.info(f"[SkillsAPI] Fetched {len(skills)} skills for job {job_id} from {url}: {skills}")
                            break
        except Exception as e:
            logger.debug(f"[SkillsAPI] Failed to fetch from {url}: {e}")

    if skills:
        try:
            from app.routers.assistant_router_helpers import redis_client
            await redis_client.set(redis_key, json.dumps(skills), ex=7200)  # cache 2 giờ
            logger.info(f"[SkillsCache] Cached {len(skills)} skills for job {job_id} in Redis.")
        except Exception as e:
            logger.error(f"[SkillsCache] Failed to save job skills to Redis: {e}")

    return skills


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
    
    matched = []
    for skill in jd_skills:
        skill_lower = skill.lower().strip()
        if not skill_lower:
            continue
        if skill_lower.startswith("."):
            pattern = re.escape(skill_lower) + r"(?!\w)"
        else:
            pattern = r"(?<!\w)" + re.escape(skill_lower) + r"(?!\w)"
            
        if re.search(pattern, cv_lower):
            matched.append(skill)
            
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
    Áp dụng hình phạt nếu có sự lệch cấp bậc giữa yêu cầu công việc (JD) và CV.
    - Cấp 4: Senior+ (Senior, Lead, Manager, Architect, >=5 năm kinh nghiệm)
    - Cấp 3: Middle (Middle, Mid, 3-4 năm kinh nghiệm)
    - Cấp 2: Junior (Junior, 1-2 năm kinh nghiệm)
    - Cấp 1: Intern/Fresher (Intern, Fresher, Thực tập, Chưa có kinh nghiệm, 0-1 năm)
    
    Nếu JD yêu cầu cấp cao hơn năng lực của ứng viên, áp dụng hình phạt:
    - Lệch 1 cấp: phạt x0.8
    - Lệch 2 cấp: phạt x0.5
    - Lệch 3 cấp: phạt x0.35
    """
    jd_lower = jd_text.lower()
    cv_lower = cv_text.lower()
    # Chỉ quét 600 ký tự đầu của CV để tránh match nhầm chức danh của người giới thiệu ở cuối trang
    cv_header = cv_lower[:600]

    # 1. Xác định cấp bậc yêu cầu của Job (JD)
    jd_senior_patterns = [
        r"\bsenior\b", r"\blead\b", r"\btrưởng nhóm\b", r"\btrưởng phòng\b",
        r"\bquản lý (?:nhóm|dự án|kỹ thuật|phòng|ban)\b", r"\bmanager\b", r"\btech lead\b", r"\bchủ chốt\b",
        r"\barchitect\b", r"\bchuyên gia\b", r"\b5\s*năm kinh nghiệm\b",
        r"\b6\s*năm kinh nghiệm\b", r"\b7\s*năm kinh nghiệm\b", r"\b8\s*năm kinh nghiệm\b",
        r"\b10\s*năm kinh nghiệm\b"
    ]
    jd_middle_patterns = [
        r"\bmiddle\b", r"\bmid\b", r"\b3\s*năm kinh nghiệm\b", r"\b4\s*năm kinh nghiệm\b"
    ]
    jd_junior_patterns = [
        r"\bjunior\b", r"\b1\s*năm kinh nghiệm\b", r"\b2\s*năm kinh nghiệm\b"
    ]
    jd_fresher_patterns = [
        r"\bintern\b", r"\bfresher\b", r"\bthực tập sinh\b", r"\bthực tập\b",
        r"\b0\s*-\s*1\s*năm kinh nghiệm\b"
    ]

    jd_level = 2  # Mặc định là Junior
    if any(re.search(pat, jd_lower) for pat in jd_senior_patterns):
        jd_level = 4
    elif any(re.search(pat, jd_lower) for pat in jd_middle_patterns):
        jd_level = 3
    elif any(re.search(pat, jd_lower) for pat in jd_junior_patterns):
        jd_level = 2
    elif any(re.search(pat, jd_lower) for pat in jd_fresher_patterns):
        jd_level = 1

    # 2. Xác định cấp bậc của ứng viên (CV) - hỗ trợ việc nối từ do lỗi trích xuất text
    cv_senior_patterns = [
        r"\w*senior\b", r"\w*lead\b", r"\w*leader\b", r"\btrưởng nhóm\b", r"\btrưởng phòng\b",
        r"\bquản lý (?:nhóm|dự án|kỹ thuật|phòng|ban)\b", r"\w*manager\b", r"\w*architect\b", r"\bchuyên gia\b"
    ]
    cv_middle_patterns = [
        r"\w*middle\b", r"\w*mid\b"
    ]
    cv_junior_patterns = [
        r"\w*junior\b"
    ]
    cv_fresher_patterns = [
        r"\w*intern(?:ship)?\b", r"\w*fresher\b", r"\bthực tập sinh\b", r"\bthực tập\b",
        r"\bsinh viên năm\b", r"\bchưa có kinh nghiệm\b", r"\bmới ra trường\b",
        r"\bhọc việc\b", r"\b0\s*-\s*1\s*năm kinh nghiệm\b", r"\bchưa có kinh nghiệm thực tế\b"
    ]

    cv_level = 2  # Mặc định là Junior nếu không tìm thấy từ khóa đặc trưng
    if any(re.search(pat, cv_header) for pat in cv_senior_patterns):
        cv_level = 4
    elif any(re.search(pat, cv_header) for pat in cv_middle_patterns):
        cv_level = 3
    elif any(re.search(pat, cv_header) for pat in cv_junior_patterns):
        cv_level = 2
    elif any(re.search(pat, cv_header) for pat in cv_fresher_patterns):
        cv_level = 1

    # 3. Tính toán hình phạt nếu lệch cấp bậc
    if jd_level > cv_level:
        # Trường hợp ứng viên THIẾU kinh nghiệm so với JD (Under-qualified)
        diff = jd_level - cv_level
        if diff == 1:
            penalty = 0.8
        elif diff == 2:
            penalty = 0.5
        else:
            penalty = 0.35
        logger.info(
            f"[SeniorityPenalty] Thiếu cấp bậc (Under-qualified): JD Level {jd_level} vs CV Level {cv_level}. "
            f"Phạt x{penalty}"
        )
        return penalty

    elif cv_level > jd_level:
        # Trường hợp ứng viên THỪA kinh nghiệm so với JD (Over-qualified)
        diff = cv_level - jd_level
        if diff == 1:
            # Lệch 1 cấp (JD Fresher vs CV Junior) -> Vẫn tốt, phạt nhẹ x0.9
            penalty = 0.9
        elif diff == 2:
            # Lệch 2 cấp (JD Fresher vs CV Middle) -> Chênh lệch lớn về lương & kỳ vọng công việc
            penalty = 0.7
        else:
            # Lệch 3 cấp (JD Fresher vs CV Senior) -> Mismatch nghiêm trọng
            penalty = 0.5
        logger.info(
            f"[SeniorityPenalty] Thừa cấp bậc (Over-qualified): JD Level {jd_level} vs CV Level {cv_level}. "
            f"Phạt x{penalty}"
        )
        return penalty

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
    jd_skills = []
    if req.job_id:
        jd_skills = await _fetch_job_skills_from_api(req.job_id)
        
    if not jd_skills:
        jd_skills = _extract_tech_skills(req.job_description)

    raw_score = score_cv(req.job_description, req.cv_text)
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

    feedback_data = {"extracted_skills": jd_skills, "strengths": [], "weaknesses": [], "ai_feedback": None}

    if req.generate_feedback:
        # Vẫn sử dụng JD gốc để LLM phân tích chi tiết thế mạnh/điểm yếu
        llm_feedback = await generate_feedback(req.job_description, req.cv_text)
        feedback_data.update({
            "strengths": llm_feedback.get("strengths", []),
            "weaknesses": llm_feedback.get("weaknesses", []),
            "ai_feedback": llm_feedback.get("ai_feedback", None)
        })

    result = ScoringResult(
        application_id=req.application_id,
        customer_id=req.customer_id,
        matching_score=score,
        **feedback_data
    )

    if req.application_id and req.job_id and req.customer_id:
        await _save_analysis(req, result)

    return result


async def batch_score(req: SkillScoringRequest, top_n: int = 10) -> BatchScoringResponse:
    """
    Pipeline 2 bước chuẩn công nghiệp:
    Bước 1: SBERT chấm hàng loạt tất cả CVs — cực nhanh (GPU).
    Bước 2: Chỉ top_n CV điểm cao nhất mới gọi LLM sinh nhận xét chi tiết.
    """
    job_id = None
    if req.cv_list:
        job_id = req.cv_list[0].get("job_id")
        
    jd_skills = []
    if job_id:
        jd_skills = await _fetch_job_skills_from_api(job_id)
        
    if not jd_skills:
        jd_skills = _extract_tech_skills(req.job_description)

    cv_texts = [item["cv_text"] for item in req.cv_list]
    raw_scores = batch_score_cvs(req.job_description, cv_texts)

    final_scores = []
    for cv_text, raw_score in zip(cv_texts, raw_scores):
        skill_penalty = _compute_skill_penalty(jd_skills, cv_text)
        seniority_penalty = _compute_seniority_penalty(req.job_description, cv_text)
        final_raw_score = raw_score * skill_penalty * seniority_penalty
        final_scores.append(round((max(0.0, final_raw_score) ** 0.5) * 10, 2))

    scored = sorted(zip(req.cv_list, final_scores), key=lambda x: x[1], reverse=True)

    results = []
    for idx, (cv_item, score) in enumerate(scored):
        feedback_data = {"extracted_skills": jd_skills, "strengths": [], "weaknesses": [], "ai_feedback": None}

        # Không sinh feedback tự động bằng LLM ở đây để tránh làm chậm và tốn quota.
        # Feedback chi tiết sẽ được sinh on-demand (khi NTD click xem chi tiết ứng viên).
        pass

        res_item = ScoringResult(
            application_id=cv_item.get("application_id"),
            customer_id=cv_item.get("customer_id"),
            matching_score=score,
            **feedback_data,
        )
        results.append(res_item)

        app_id = cv_item.get("application_id")
        curr_job_id = cv_item.get("job_id") or job_id
        cust_id = cv_item.get("customer_id")
        if app_id and curr_job_id and cust_id:
            fake_req = CvScoringRequest(
                job_description=req.job_description,
                cv_text=cv_item["cv_text"],
                application_id=app_id,
                job_id=curr_job_id,
                customer_id=cust_id
            )
            await _save_analysis(fake_req, res_item)

    return BatchScoringResponse(results=results, top_count=min(top_n, len(results)))
