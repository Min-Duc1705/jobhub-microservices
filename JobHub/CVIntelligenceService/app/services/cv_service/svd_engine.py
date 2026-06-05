# app/services/cv_service/svd_engine.py
"""
Collaborative Filtering engine dùng Matrix Factorization (Truncated SVD).
Huấn luyện theo lô từ dữ liệu MongoDB và cache kết quả toàn cục.
"""
import asyncio
import logging

import numpy as np
from sklearn.decomposition import TruncatedSVD

from app.core.database import get_job_view_history_col

logger = logging.getLogger(__name__)

# Cache điểm số SVD được tính toán ngầm
_PRECOMPUTED_SVD_SCORES: dict[str, dict[str, float]] = {}


def get_svd_scores() -> dict[str, dict[str, float]]:
    """Trả về cache SVD scores hiện tại (read-only reference)."""
    return _PRECOMPUTED_SVD_SCORES


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

    user_item_scores: dict[tuple, float] = {}
    unique_users: set[str] = set()
    unique_jobs: set[str] = set()

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

        new_scores: dict[str, dict[str, float]] = {}
        for uid in unique_users:
            u_idx = user_to_idx[uid]
            pred_ratings = R_pred[u_idx]
            min_r = float(np.min(pred_ratings))
            max_r = float(np.max(pred_ratings))

            user_scores: dict[str, float] = {}
            for idx, rating in enumerate(pred_ratings):
                jid = idx_to_job[idx]
                norm_score = ((rating - min_r) / (max_r - min_r)) * 100.0 if max_r > min_r else 50.0
                user_scores[jid] = round(norm_score, 2)
            new_scores[uid] = user_scores

        _PRECOMPUTED_SVD_SCORES = new_scores
        logger.info(
            f"[SVD] Huấn luyện SVD offline thành công cho {num_users} users, "
            f"{num_jobs} jobs, latent={n_components}."
        )
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
