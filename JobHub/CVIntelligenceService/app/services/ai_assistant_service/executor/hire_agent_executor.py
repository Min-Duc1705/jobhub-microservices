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
    result = await _call_api("GET", f"http://notificationservice:8080/api/v1/hire-agent/campaigns/{camp_id}/conversations", user_token)
    conversations = result.get("data")
    if isinstance(conversations, list):
        import asyncio
        async def enrich_conversation(item):
            candidate_id = item.get("candidateId")
            candidate_name = "Ứng viên"
            candidate_email = ""
            if candidate_id:
                try:
                    url = f"http://profileservice:8080/api/v1/customers/{candidate_id}"
                    profile = await _call_api("GET", url, user_token)
                    if profile and "data" in profile:
                        candidate_name = profile["data"].get("fullName") or "Ứng viên"
                        candidate_email = profile["data"].get("email") or ""
                except Exception as e:
                    logger.error(f"Error fetching profile: {e}")
            item["candidate_name"] = candidate_name
            item["candidate_email"] = candidate_email
            
        tasks = [enrich_conversation(item) for item in conversations]
        await asyncio.gather(*tasks)
    return result


async def execute_get_my_interviews(args: dict, user_token: str) -> dict:
    result = await _call_api("GET", "http://resumeservice:8080/api/v1/interviews", user_token)
    interviews = result.get("data")
    if isinstance(interviews, list):
        import asyncio
        async def enrich_interview(item):
            candidate_id = item.get("candidateId")
            job_id = item.get("jobId")
            
            # Fetch candidate profile details
            candidate_name = "Ứng viên"
            candidate_email = ""
            if candidate_id:
                try:
                    url = f"http://profileservice:8080/api/v1/customers/{candidate_id}"
                    profile = await _call_api("GET", url, user_token)
                    if profile and "data" in profile:
                        candidate_name = profile["data"].get("fullName") or "Ứng viên"
                        candidate_email = profile["data"].get("email") or ""
                except Exception as e:
                    logger.error(f"Error fetching profile: {e}")
            
            # Fetch job details
            job_title = "Công việc"
            if job_id:
                try:
                    url = f"http://jobhub_jobservice:8080/api/v1/jobs/{job_id}"
                    job_data = await _call_api("GET", url, user_token)
                    if job_data and "data" in job_data:
                        job_title = job_data["data"].get("name") or "Công việc"
                except Exception as e:
                    logger.error(f"Error fetching job: {e}")
            
            item["candidate_name"] = candidate_name
            item["candidate_email"] = candidate_email
            item["job_title"] = job_title
            
        tasks = [enrich_interview(item) for item in interviews]
        await asyncio.gather(*tasks)
    return result
