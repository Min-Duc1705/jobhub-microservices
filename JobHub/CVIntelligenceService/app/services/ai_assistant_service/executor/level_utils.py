# app/services/ai_assistant_service/executor/level_utils.py
"""
Utility functions to infer job level from job name/title, experience or other clues.
"""
import re
import logging

logger = logging.getLogger(__name__)

def infer_level_from_experience(exp_str: str, current_level: str = None) -> str:
    """
    Deprecated: use infer_level_smart instead. Keeping for backward compatibility.
    """
    return infer_level_smart("", exp_str, current_level)

def infer_level_smart(job_name: str, exp_str: str, current_level: str = None) -> str:
    """
    Infers the job level with the following priority:
    1. Explicit level keywords in the job title (job_name).
    2. Explicit level keywords in the experience requirement text (exp_str).
    3. Respect current_level if it's explicitly matched and not the default JUNIOR.
    4. Map numeric years of experience parsed from exp_str.
    5. Fallback to current_level or default JUNIOR.
    """
    name_lower = str(job_name or "").lower().strip()
    exp_lower = str(exp_str or "").lower().strip()

    # Define level keywords in descending order of seniority
    keywords = [
        ("manager", ["manager", "quản lý", "trưởng phòng", "director", "giám đốc", "head of"]),
        ("leader", ["leader", "lead", "nhóm trưởng", "chủ trì", "tổ trưởng"]),
        ("senior", ["senior", "sr", "sr."]),
        ("middle", ["middle", "mid-level", "mid level", "mid"]),
        ("junior", ["junior", "jr", "jr."]),
        ("fresher", ["fresher"]),
        ("intern", ["intern", "thực tập", "trainee"])
    ]

    # 1. Priority 1: Check explicit level keywords in Job Name / Title
    for level, kw_list in keywords:
        for kw in kw_list:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, name_lower) or kw == name_lower:
                return level.upper()

    # 2. Priority 2: Check explicit level keywords in Experience Text
    for level, kw_list in keywords:
        for kw in kw_list:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, exp_lower) or kw == exp_lower:
                return level.upper()

    # 3. Priority 3: If current_level is explicitly provided and is not default "JUNIOR"
    valid_levels = {"INTERN", "FRESHER", "MIDDLE", "SENIOR", "LEADER", "MANAGER"}
    if current_level and str(current_level).upper() in valid_levels:
        if str(current_level).upper() != "JUNIOR":
            return str(current_level).upper()

    # 4. Priority 4: Parse numeric years of experience
    numbers = [int(s) for s in re.findall(r'\d+', exp_lower)]
    if numbers:
        max_val = max(numbers)
        min_val = min(numbers)
        if max_val <= 1:
            return "FRESHER"
        elif max_val <= 3:
            if min_val >= 3:
                return "MIDDLE"
            return "JUNIOR"
        elif max_val <= 4:
            return "MIDDLE"
        elif max_val < 7:
            return "SENIOR"
        elif max_val < 8:
            return "LEADER"
        else:
            return "MANAGER"

    if "không yêu cầu" in exp_lower or "không cần" in exp_lower or "no experience" in exp_lower:
        return "INTERN"

    # 5. Priority 5: Fallback to current_level or JUNIOR
    if current_level and str(current_level).upper() in (valid_levels | {"JUNIOR"}):
        return str(current_level).upper()
    return "JUNIOR"
