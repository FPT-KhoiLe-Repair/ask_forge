import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

def generate_questions_task(
        seed_question: str,
        contexts: List[Dict],
        lang: str,
        session_id: str,
        n: int = 5,
) -> List[str]:
    """
    ✅ RQ worker task - MUST be sync function

    RQ (Redis Queue) only supports synchronous functions.
    We use sync wrappers to call async code internally.
    """
    import asyncio
    from ask_forge.backend.app.core.app_state import get_app_state

    logger.info(
        f"🔧 QG Worker started: session={session_id}, "
        f"seed='{seed_question[:50]}...', n={n}"
    )
    try:

        app_state = get_app_state()

        async def _get_provider():
            return await app_state.llm_router.route({
                "task": "question_generation",
                "prefer_local": True,
                "lang": lang,
            })

        try:
            provider = asyncio.run(_get_provider())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                provider = loop.run_until_complete(_get_provider())
            finally:
                loop.close()
        logger.info(f"✅ Routed to provider: {provider.model_name}")

        # Generate questions
        async def _generate():
            return await provider.generate(
                prompt=seed_question,
                contexts=contexts,
                n=n,
                lang=lang,
                history_block="", # Optional: add from session if needed
                summary_block="",
            )
        try:
            questions = asyncio.run(_generate())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                questions = loop.run_until_complete(_generate())
            finally:
                loop.close()
        logger.info(f"✅ Generated {len(questions)} questions")
        return questions
    except Exception as e:
        logger.exception(f"❌ QG Worker failed: {e}")
        # Return empty list instead of raising (RQ will mark as failed anyway)
        return []