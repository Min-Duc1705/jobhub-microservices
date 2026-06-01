import asyncio
import json
import logging

import aio_pika

from app.config import settings
from app.schemas.cv_scoring import CvScoringRequest
from app.services.cv_service import score_single_cv

logger = logging.getLogger(__name__)

QUEUE_NAME    = "cv.score.queue"
EXCHANGE_NAME = "jobhub.events"
ROUTING_KEY   = "application.submitted"


async def handle_application_submitted(message: aio_pika.abc.AbstractIncomingMessage):
    """
    Xử lý event ApplicationSubmitted từ ResumeService (C#).

    Payload mong đợi từ C# MassTransit:
    {
        "applicationId": "...",
        "jobId":         "...",
        "customerId":    "...",
        "cvText":        "...",   ← nội dung text đã parse từ PDF
        "jobDescription": "..."  ← lấy từ JobService
    }
    """
    async with message.process(requeue=True):
        try:
            body = json.loads(message.body.decode())
            logger.info(f"[Consumer] Nhận event ApplicationSubmitted: applicationId={body.get('applicationId')}")

            req = CvScoringRequest(
                job_description=body["jobDescription"],
                cv_text=body["cvText"],
                application_id=body.get("applicationId"),
                job_id=body.get("jobId"),
                customer_id=body.get("customerId"),
            )
            result = await score_single_cv(req)
            logger.info(
                f"[Consumer] Chấm điểm xong: applicationId={req.application_id}, "
                f"score={result.matching_score}%"
            )
        except Exception as e:
            logger.error(f"[Consumer] Lỗi xử lý message: {e}", exc_info=True)


async def start_consumer():
    """Khởi động RabbitMQ consumer — chạy ngầm trong background khi service bật."""
    logger.info("[Consumer] Đang kết nối RabbitMQ...")
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=5)  # Xử lý tối đa 5 CV song song

        exchange = await channel.declare_exchange(
            EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
        )
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)
        await queue.bind(exchange, routing_key=ROUTING_KEY)

        logger.info(f"[Consumer] Đang lắng nghe queue '{QUEUE_NAME}'...")
        await queue.consume(handle_application_submitted)

        # Giữ consumer sống mãi
        await asyncio.Future()
