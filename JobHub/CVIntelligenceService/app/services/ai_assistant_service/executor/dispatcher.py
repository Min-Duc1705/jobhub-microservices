# app/services/ai_assistant_service/executor/dispatcher.py
"""
Dispatcher trung tâm: nhận tool_name và args, gọi đúng executor tương ứng.
"""
import logging
from .job_executor import (
    execute_search_jobs, execute_get_job_detail, execute_get_my_jobs,
    execute_preview_create_job, execute_delete_job,
    execute_update_job, execute_change_job_status
)
from .candidate_executor import (
    execute_search_candidates, execute_get_applications_for_job,
    execute_apply_job, execute_cancel_application, execute_review_application,
    execute_score_candidates_for_job, execute_get_candidate_evaluation_detail
)
from .profile_executor import (
    execute_update_my_profile, execute_get_my_resumes,
    execute_set_default_resume, execute_delete_resume, execute_get_my_applications
)
from .company_executor import (
    execute_get_my_company_info, execute_search_companies,
    execute_update_company_info, execute_create_company
)
from .skill_executor import (
    execute_get_all_skills, execute_create_skill, execute_update_skill,
    execute_delete_skill, execute_add_my_skill, execute_remove_my_skill,
    execute_import_skills_to_my_profile
)
from .hire_agent_executor import (
    execute_get_my_hire_agent_campaigns, execute_create_hire_agent_campaign,
    execute_schedule_campaign_interview, execute_get_campaign_conversations,
    execute_get_my_interviews
)
from .admin_executor import (
    execute_get_all_users, execute_get_user_detail, execute_update_user,
    execute_delete_user, execute_reset_user_password,
    execute_get_all_roles, execute_get_all_permissions,
    execute_verify_company, execute_delete_company, execute_delete_customer,
    execute_get_admin_jobs, execute_get_my_account,
    execute_create_role, execute_update_role, execute_delete_role,
    execute_create_permission, execute_update_permission, execute_delete_permission
)
from .misc_executor import (
    execute_navigate_to_page, execute_predict_salary, execute_broadcast_notification,
    execute_get_my_saved_jobs, execute_save_job, execute_unsave_job,
    execute_import_users, execute_import_skills, execute_import_companies, execute_import_jobs,
    execute_get_my_conversations, execute_get_chat_history, execute_get_my_notifications,
    execute_telegram_subscribe, execute_telegram_list_subscriptions,
    execute_telegram_delete_subscription, execute_telegram_pause_subscription,
    execute_telegram_resume_subscription, execute_telegram_set_reminder,
    execute_send_chat_message
)

logger = logging.getLogger(__name__)

# Map tool_name -> executor function
_TOOL_EXECUTOR_MAP = {
    # Job tools
    "search_jobs":          execute_search_jobs,
    "get_job_detail":       execute_get_job_detail,
    "get_my_jobs":          execute_get_my_jobs,
    "preview_create_job":   execute_preview_create_job,
    "delete_job":           execute_delete_job,
    "update_job":           execute_update_job,
    "change_job_status":    execute_change_job_status,
    # Candidate/Application tools
    "search_candidates":            execute_search_candidates,
    "get_applications_for_job":     execute_get_applications_for_job,
    "score_candidates_for_job":     execute_score_candidates_for_job,
    "get_candidate_evaluation_detail": execute_get_candidate_evaluation_detail,
    "apply_job":                    execute_apply_job,
    "cancel_application":           execute_cancel_application,
    "review_application":           execute_review_application,
    # Profile/Resume tools
    "update_my_profile":    execute_update_my_profile,
    "get_my_resumes":       execute_get_my_resumes,
    "set_default_resume":   execute_set_default_resume,
    "delete_resume":        execute_delete_resume,
    "get_my_applications":  execute_get_my_applications,
    # Company tools
    "get_my_company_info":  execute_get_my_company_info,
    "search_companies":     execute_search_companies,
    "update_company_info":  execute_update_company_info,
    "create_company":       execute_create_company,
    # Skills — Admin
    "get_all_skills":       execute_get_all_skills,
    "create_skill":         execute_create_skill,
    "update_skill":         execute_update_skill,
    "delete_skill":         execute_delete_skill,
    # Skills — Personal
    "add_my_skill":         execute_add_my_skill,
    "remove_my_skill":      execute_remove_my_skill,
    "import_skills_to_my_profile": execute_import_skills_to_my_profile,
    # Hire Agent tools
    "get_my_hire_agent_campaigns":  execute_get_my_hire_agent_campaigns,
    "create_hire_agent_campaign":   execute_create_hire_agent_campaign,
    "schedule_campaign_interview":  execute_schedule_campaign_interview,
    "get_campaign_conversations":   execute_get_campaign_conversations,
    "get_my_interviews":            execute_get_my_interviews,
    # Misc tools
    "navigate_to_page":         execute_navigate_to_page,
    "predict_salary":           execute_predict_salary,
    "broadcast_notification":   execute_broadcast_notification,
    "get_my_saved_jobs":        execute_get_my_saved_jobs,
    "save_job":                 execute_save_job,
    "unsave_job":               execute_unsave_job,
    "get_my_conversations":     execute_get_my_conversations,
    "get_chat_history":         execute_get_chat_history,
    "get_my_notifications":     execute_get_my_notifications,
    "telegram_subscribe":       execute_telegram_subscribe,
    "telegram_list_subscriptions": execute_telegram_list_subscriptions,
    "telegram_delete_subscription": execute_telegram_delete_subscription,
    "telegram_pause_subscription": execute_telegram_pause_subscription,
    "telegram_resume_subscription": execute_telegram_resume_subscription,
    "telegram_set_reminder":    execute_telegram_set_reminder,
    "send_chat_message":        execute_send_chat_message,
    # Admin — Users
    "get_all_users":        execute_get_all_users,
    "get_user_detail":      execute_get_user_detail,
    "update_user":          execute_update_user,
    "delete_user":          execute_delete_user,
    "reset_user_password":  execute_reset_user_password,
    # Admin — Roles & Permissions
    "get_all_roles":        execute_get_all_roles,
    "get_all_permissions":  execute_get_all_permissions,
    # Admin — Company
    "verify_company":       execute_verify_company,
    "delete_company":       execute_delete_company,
    # Admin — Customer
    "delete_customer":      execute_delete_customer,
    # Admin — Jobs (mọi trạng thái)
    "get_admin_jobs":       execute_get_admin_jobs,
    # Auth — Account
    "get_my_account":       execute_get_my_account,
    # Admin — Role CRUD
    "create_role":          execute_create_role,
    "update_role":          execute_update_role,
    "delete_role":          execute_delete_role,
    # Admin — Permission CRUD
    "create_permission":    execute_create_permission,
    "update_permission":    execute_update_permission,
    "delete_permission":    execute_delete_permission,
    # Admin — Import guides (file upload → navigate to Admin UI)
    "import_users":         execute_import_users,
    "import_skills":        execute_import_skills,
    "import_companies":     execute_import_companies,
    "import_jobs":          execute_import_jobs,
}


async def _execute_tool(tool_name: str, args: dict, user_token: str) -> dict:
    """Dispatcher chính: thực thi một tool cụ thể với token của user."""
    executor_fn = _TOOL_EXECUTOR_MAP.get(tool_name)
    if executor_fn is None:
        return {"error": f"Tool '{tool_name}' chưa được triển khai"}

    try:
        return await executor_fn(args, user_token)
    except Exception as e:
        logger.error(f"[Dispatcher] Tool '{tool_name}' failed: {e}")
        return {"error": str(e)}
