# backend/app/services/queue/redis_queue.py

import redis  # Sync redis cho RQ
from rq import Queue
from rq.job import Job
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class BackgroundQueue:
    def __init__(self, redis_url: str = "redis://localhost:6379", qname: str = "qg"):
        # ✅ Dùng sync redis cho RQ
        self.redis = redis.from_url(redis_url, decode_responses=False)
        self.queue = Queue("qg",connection=self.redis)
        logger.info(f"✅ BackgroundQueue initialized: {redis_url}")

    async def enqueue_qg(
            self,
            seed_question: str,
            contexts: list,
            lang: str,
            session_id: str
    ) -> str:
        """Enqueue QG task to background worker"""
        try:
            job = self.queue.enqueue(
                "ask_forge.backend.app.services.qg.worker.generate_questions_task",
                seed_question=seed_question,
                contexts=contexts,
                lang=lang,
                session_id=session_id,
                job_timeout=60,
                result_ttl=300  # Keep result 5 minutes
            )
            logger.info(f"✅ QG job enqueued: {job.id}")
            return job.id
        except Exception as e:
            logger.exception("Failed to enqueue QG job")
            raise

    async def get_result(self, job_id: str) -> Optional[list]:
        """Poll job result"""
        try:
            job = Job.fetch(job_id, connection=self.redis)

            if job.is_finished:
                return job.result
            elif job.is_failed:
                logger.error(f"Job {job_id} failed: {job.exc_info}")
                return None
            else:
                return None  # Still pending
        except Exception as e:
            logger.exception(f"Error fetching job {job_id}")
            return None