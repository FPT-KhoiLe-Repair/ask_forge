import asyncio
import uuid
import logging
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class AsyncBackgroundQueue:
    """
    ✅ In-process background task queue using asyncio

    Advantages:
    - Share memory with FastAPI (same AppState instance)
    - No Redis dependency
    - Simple setup

    Disadvantages:
    - No persistence (lost on restart)
    - Runs in same process (CPU bound tasks block event loop)
    """

    def __init__(self):
        self._jobs: Dict[str, dict] = {} # {job_id: {status, result, error}}
        self._lock = asyncio.Lock()

    async def enqueue_qg(
            self,
            seed_question: str,
            contexts: List[dict],
            lang: str,
            session_id: str,
            app_state,
    ) -> str:
        """Enqueue QG task to background worker"""
        job_id = str(uuid.uuid4())

        # Initialize job status
        async with self._lock:
            self._jobs[job_id] = {
                "status": "pending",
                "result": None,
                "error": None,
                "created_at": datetime.now().isoformat(),
            }

        # ✅ Create background task (non-blocking)
        asyncio.create_task(
            self._run_qg_task(
                job_id=job_id,
                seed_question=seed_question,
                contexts=contexts,
                lang=lang,
                session_id=session_id,
                app_state=app_state,
            )
        )
        return job_id

    async def _run_qg_task(
            self,
            job_id: str,
            seed_question: str,
            contexts: List[dict],
            lang: str,
            session_id: str,
            app_state,
    ):
        """Actually run the QG task"""
        try:
            logger.info(f"🔧 QG task started: {job_id}")

            # Route to provider
            provider = await app_state.llm_router.route({
                "task": "question_generation",
                "prefer_local": True,
            })

            logger.info(f"✅ Routed to: {provider.model_name}")

            # Generate questions
            questions = await provider.generate(
                prompt=seed_question,
                contexts=contexts,
                n=5,
                lang=lang,
            )

            # Update job status
            async with self._lock:
                self._jobs[job_id].update({
                    "status": "completed",
                    "result": questions,
                    "completed_at": datetime.now().isoformat(),
                })

            logger.info(f"✅ QG task completed: {job_id} ({len(questions)} questions)")
        except Exception as e:
            logger.exception(f"❌ QG task failed: {job_id}")
            async with self._lock:
                self._jobs[job_id].update({
                    "status": "failed",
                    "error": str(e),
                    "failed_at": datetime.now().isoformat(),
                })

    async def get_result(self, job_id: str) -> Optional[list]:
        """Poll job result"""
        async with self._lock:
            job = self._jobs.get(job_id)

        if job is None:
            raise KeyError(f"Job ID: {job_id} not found")

        status = job["status"]
        if status == "completed":
            return job["result"]
        elif status == "failed":
            raise RuntimeError(f"Job ID: {job_id} failed")

        # pending
        return None


    async def cleanup_old_jobs(self, max_age_seconds: int = 3000):
        """Cleanup jobs older than max_age_seconds"""
        from datetime import timedelta, datetime

        cutoff = datetime.now() - timedelta(days=max_age_seconds)

        async with self._lock:
            to_remove = []
            for job_id, job in self._jobs.items():
                created = datetime.fromisoformat(job["created_at"])
                if created < cutoff:
                    to_remove.append(job_id)

            for job_id in to_remove:
                del self._jobs[job_id]

            if to_remove:
                logger.info(f"🗑️ Cleaned up {len(to_remove)} old jobs")