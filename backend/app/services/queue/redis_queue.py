# backend/app/services/queue/redis_queue.py
import asyncio
from typing import Optional
import redis.asyncio as aioredis
from rq import Queue
from rq.job import Job


class BackgroundQueue:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = aioredis.from_url(redis_url)
        self.queue = Queue(connection=self.redis)

    async def enqueue_qg(
            self,
            seed_question: str,
            contexts: list,
            lang: str,
            session_id: str
    ) -> str:
        """Đẩy QG task vào queue, trả job_id"""
        job = self.queue.enqueue(
            "ask_forge.backend.app.services.qg.worker.generate_questions_task",
            seed_question=seed_question,
            contexts=contexts,
            lang=lang,
            session_id=session_id,
            job_timeout=60
        )
        return job.id

    async def get_result(self, job_id: str) -> Optional[list]:
        """Poll kết quả QG"""
        job = Job.fetch(job_id, connection=self.redis)
        if job.is_finished:
            return job.result
        return None