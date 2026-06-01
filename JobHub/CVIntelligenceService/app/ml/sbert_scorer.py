import logging
import re
import html
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

def clean_html(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    # Remove HTML tags
    text = re.sub(r'<[^>]*>', ' ', text)
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# ── SBERT Model Singleton ──────────────────────────────────────────────────────
# Dùng @lru_cache để chỉ load model 1 lần lên VRAM khi service khởi động.
# paraphrase-multilingual-mpnet-base-v2: hỗ trợ tiếng Việt + 50 ngôn ngữ khác,
# chính xác cao hơn MiniLM, RTX 3050 Ti đủ sức chạy mượt với GPU acceleration.
@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    logger.info(f"[SBERT] Đang load model '{settings.SBERT_MODEL}'... (lần đầu có thể download)")
    model = SentenceTransformer(settings.SBERT_MODEL)
    logger.info("[SBERT] Model đã load xong và sẵn sàng!")
    return model


def score_cv(job_description: str, cv_text: str) -> float:
    """
    Chấm điểm 1 CV so với JD.
    Trả về float 0.0 → 100.0 (phần trăm độ khớp).

    Cơ chế:
    1. Dịch cả JD và CV thành vector số (Embedding).
    2. Tính góc Cosine giữa 2 vector (0 = không liên quan, 1 = giống hệt nhau).
    3. Nhân 100 để ra %.
    """
    model = _load_model()
    clean_jd = clean_html(job_description)
    clean_cv = clean_html(cv_text)
    embeddings = model.encode(
        [clean_jd, clean_cv],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    score = float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])
    return round(score * 100, 2)


def batch_score_cvs(job_description: str, cv_texts: list[str]) -> list[float]:
    """
    Chấm hàng loạt: 1 JD vs N CVs — chạy song song trên GPU.
    Hiệu quả nhất khi N lớn (vài trăm đến vài nghìn CVs).
    """
    model = _load_model()
    clean_jd = clean_html(job_description)
    clean_cvs = [clean_html(cv) for cv in cv_texts]
    all_texts = [clean_jd] + clean_cvs
    embeddings = model.encode(
        all_texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        batch_size=64,        # Phù hợp với VRAM 4GB của 3050 Ti
        show_progress_bar=True,
    )
    jd_vec = embeddings[0:1]
    cv_vecs = embeddings[1:]
    scores = cosine_similarity(jd_vec, cv_vecs)[0]
    return [round(float(s) * 100, 2) for s in scores]
