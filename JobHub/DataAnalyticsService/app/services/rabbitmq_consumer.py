import json
import logging
from datetime import datetime
import asyncio
from aio_pika import connect_robust, IncomingMessage

from app.config import settings
from app.core.database import get_salary_dataset_col, get_job_trend_col
from app.models.documents import SalaryDataset, JobTrendSnapshot

logger = logging.getLogger(__name__)

async def process_job_published_event(msg_body: bytes):
    try:
        envelope = json.loads(msg_body.decode())
        # MassTransit envelope chứa message thực sự trong trường "message"
        msg = envelope.get("message", {})
        if not msg:
            logger.warning("[RabbitMQ] Message body empty or not inside envelope")
            return

        job_title = msg.get("jobTitle") or msg.get("JobTitle")
        years_of_experience = msg.get("yearsOfExperience") or msg.get("YearsOfExperience") or 0
        skill_set = msg.get("skillSet") or msg.get("SkillSet") or []
        location = msg.get("location") or msg.get("Location") or "Khác"
        level = msg.get("level") or msg.get("Level") or "JUNIOR"
        salary_min_raw = float(msg.get("salaryMin") or msg.get("SalaryMin") or 0.0)
        salary_max_raw = float(msg.get("salaryMax") or msg.get("SalaryMax") or 0.0)
        is_negotiable = bool(msg.get("isNegotiable") or msg.get("IsNegotiable") or False)
        
        currency_raw = msg.get("salaryCurrency") or msg.get("SalaryCurrency")
        salary_currency = str(currency_raw).upper().strip() if currency_raw else "USD"

        if not job_title:
            logger.warning("[RabbitMQ] Job title is missing, skipping")
            return

        # Normalize salary về đơn vị TRIỆU VND
        USD_TO_VND = 25_000
        VND_UNIT = 1_000_000

        def normalize(val: float, currency: str) -> float:
            if currency == "USD":
                if val >= 5000: # Trường hợp nhập nhầm VND vào trường USD
                    return round(val / VND_UNIT, 2)
                return round((val * USD_TO_VND) / VND_UNIT, 2)
            elif currency == "VND":
                if val > 0 and val < 5000: # Người dùng nhập dạng Triệu VND sẵn (ví dụ 30.0 hoặc 50.0)
                    return round(val, 2)
                return round(val / VND_UNIT, 2)
            else:
                # Tự động nhận diện cho trường hợp khác hoặc rỗng
                if val > 0 and val < 5000:
                    # Dưới 5000 và không khai báo VND -> Mặc định quy đổi như USD thô
                    return round((val * USD_TO_VND) / VND_UNIT, 2)
                return round(val / VND_UNIT, 2)

        salary_min = normalize(salary_min_raw, salary_currency) if not is_negotiable else 0.0
        salary_max = normalize(salary_max_raw, salary_currency) if not is_negotiable else 0.0

        logger.info(f"[RabbitMQ] Processing sync for Job: {job_title} | {salary_currency} {salary_min_raw}-{salary_max_raw} -> {salary_min}-{salary_max} tr.VND")

        # 1. Lưu vào salary_datasets để làm dữ liệu train XGBoost
        dataset_col = get_salary_dataset_col()
        dataset_doc = SalaryDataset(
            job_title=job_title,
            years_of_experience=years_of_experience,
            skill_set=skill_set,
            location=location,
            level=level,
            salary_min=salary_min,
            salary_max=salary_max,
            is_negotiable=is_negotiable,
            source="JobService-Sync"
        )
        await dataset_col.insert_one(dataset_doc.model_dump(exclude={"id"}))
        logger.info(f"[RabbitMQ] Saved job salary dataset: {job_title}")

        # 2. Cập nhật xu hướng tuyển dụng cho các kỹ năng trong tháng hiện tại
        now = datetime.utcnow()
        month = now.month
        year = now.year

        trend_col = get_job_trend_col()
        for skill in skill_set:
            if not skill:
                continue
            skill_id = skill.lower().strip().replace(" ", "_")
            skill_name = skill.strip()

            # Tìm xem có snapshot tháng này chưa
            existing = await trend_col.find_one({
                "skill_name": skill_name,
                "month": month,
                "year": year
            })

            # Tính lương trung bình của Job hiện tại làm giá trị tính toán
            job_avg_salary = 0.0
            if not is_negotiable and (salary_min > 0 or salary_max > 0):
                job_avg_salary = (salary_min + salary_max) / 2.0

            if existing:
                # Cập nhật snapshot cũ
                old_count = existing.get("job_count", 0)
                new_count = old_count + 1
                old_avg_salary = existing.get("avg_salary", 0.0)

                # Công thức cập nhật trung bình tích lũy
                if job_avg_salary > 0:
                    new_avg_salary = ((old_avg_salary * old_count) + job_avg_salary) / new_count
                else:
                    new_avg_salary = old_avg_salary

                await trend_col.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {
                        "job_count": new_count,
                        "avg_salary": round(new_avg_salary, 1),
                        "snapshot_at": datetime.utcnow()
                    }}
                )
                logger.info(f"[RabbitMQ] Updated trend snapshot for skill {skill_name}: job_count={new_count}")
            else:
                # Tạo snapshot mới
                new_trend = JobTrendSnapshot(
                    skill_id=skill_id,
                    skill_name=skill_name,
                    month=month,
                    year=year,
                    job_count=1,
                    avg_salary=round(job_avg_salary, 1) if job_avg_salary > 0 else 0.0
                )
                await trend_col.insert_one(new_trend.model_dump(exclude={"id"}))
                logger.info(f"[RabbitMQ] Created trend snapshot for skill {skill_name}")

    except Exception as e:
        logger.error(f"[RabbitMQ] Error processing event: {e}", exc_info=True)

async def on_message(message: IncomingMessage):
    async with message.process():
        logger.info(f"[RabbitMQ] Received message ID: {message.message_id}")
        await process_job_published_event(message.body)

async def start_rabbitmq_consumer():
    # Loop connection retry để an toàn khi khởi chạy cùng docker
    retry_delay = 5
    while True:
        try:
            logger.info(f"[RabbitMQ] Connecting to {settings.RABBITMQ_URL}...")
            connection = await connect_robust(settings.RABBITMQ_URL)
            channel = await connection.channel()

            # MassTransit sử dụng exchange kiểu fanout
            exchange_name = "CommonService.Events:JobPublishedEvent"
            exchange = await channel.declare_exchange(
                exchange_name, 
                type="fanout", 
                durable=True
            )

            # Khai báo queue cho Analytics Service
            queue_name = "data-analytics-job-published-queue"
            queue = await channel.declare_queue(queue_name, durable=True)
            await queue.bind(exchange)

            logger.info(f"[RabbitMQ] Bind queue {queue_name} to exchange {exchange_name} successfully")
            await queue.consume(on_message)
            logger.info("[RabbitMQ] Consumer started successfully. Waiting for messages...")
            
            # Giữ consumer hoạt động
            while True:
                await asyncio.sleep(3600)
                
        except Exception as e:
            logger.error(f"[RabbitMQ] Connection failed: {e}. Retrying in {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)
