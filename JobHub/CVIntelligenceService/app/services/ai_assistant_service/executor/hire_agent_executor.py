# app/services/ai_assistant_service/executor/hire_agent_executor.py
"""
Executor cho các tools liên quan đến Hire Agent campaigns:
get_my_hire_agent_campaigns, create_hire_agent_campaign, schedule_campaign_interview
"""
import logging
from ..api_client import _call_api

logger = logging.getLogger(__name__)


async def execute_get_my_hire_agent_campaigns(args: dict, user_token: str) -> dict:
    return await _call_api("GET", "http://notificationservice:8080/api/v1/hire-agent/campaigns", user_token)


async def execute_create_hire_agent_campaign(args: dict, user_token: str) -> dict:
    payload = {
        "jobId": args.get("job_id", ""),
        "jobName": args.get("job_name", ""),
        "jobDescription": args.get("job_description", ""),
        "targetCount": int(float(args.get("target_count") or 5)),
        "jobLocation": args.get("job_location"),
        "jobType": args.get("job_type"),
        "interviewDate": args.get("interview_date"),
        "backupInterviewDate": args.get("backup_interview_date")
    }
    return await _call_api(
        "POST", "http://notificationservice:8080/api/v1/hire-agent/campaigns",
        user_token, json_data=payload
    )


async def execute_schedule_campaign_interview(args: dict, user_token: str) -> dict:
    camp_id = args.get("campaign_id", "")
    payload = {"interviewDate": args.get("interview_date", "")}
    return await _call_api(
        "POST", f"http://notificationservice:8080/api/v1/hire-agent/campaigns/{camp_id}/schedule",
        user_token, json_data=payload
    )


async def execute_get_campaign_conversations(args: dict, user_token: str) -> dict:
    camp_id = args.get("campaign_id", "")
    return await _call_api("GET", f"http://notificationservice:8080/api/v1/hire-agent/campaigns/{camp_id}/conversations", user_token)
