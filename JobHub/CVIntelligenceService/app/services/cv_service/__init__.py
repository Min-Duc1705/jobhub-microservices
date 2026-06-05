# app/services/cv_service/__init__.py
"""
CV Intelligence Service package.
Re-exports all public APIs for backward compatibility.
"""
from .scoring import score_single_cv, batch_score
from .interaction import track_interaction, get_analyses_by_job
from .svd_engine import train_and_cache_svd_for_all_users, start_periodic_svd_training
from .recommender import recommend_jobs_for_candidate

__all__ = [
    # Scoring
    "score_single_cv",
    "batch_score",
    # Interaction
    "track_interaction",
    "get_analyses_by_job",
    # SVD Engine
    "train_and_cache_svd_for_all_users",
    "start_periodic_svd_training",
    # Recommender
    "recommend_jobs_for_candidate",
]
