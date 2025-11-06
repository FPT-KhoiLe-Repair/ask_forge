def generate_questions_task(
        seed_question,
        contexts,
        lang,
        session_id):
    """RQ worker task - chạy sync"""
    from ask_forge.backend.app.core.app_state import get_app_state
    from ask_forge.backend.app.services.qg.service import QGService

    app_state = get_app_state()
    qg_service = QGService()

    # Gọi HF model (blocking - nhưng worker chạy riêng process)
    import asyncio
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)

    questions = loop.run_until_complete(
        qg_service.generate_questions(
            seed_question=seed_question,
            contexts=contexts,
            lang=lang,
        )
    )
    # TODO: Lưu vào cache/DB để front poll
    ...
    return questions
