"""
Chat/Query routes - sử dụng ChromaDB để retrieve context cho RAG.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse

from ask_forge.backend.app.services.chat.service import ChatService
from ask_forge.backend.app.repositories.vectorstore import ChromaRepo
from ask_forge.backend.app.api.dependencies import get_chroma_repo, get_chat_service

from ask_forge.backend.app.utils.naming import format_index_name
from ask_forge.backend.app.services.chat.schemas import ChatBody

router = APIRouter(
    tags=["chat"],
)


# TODO: rewrite the chat, this is just a sample usage of get_context_for_chat
@router.post("/chat")
async def chat(
        chat_body: ChatBody, # Đây sẽ là JSON type
        chat_service: ChatService = Depends(get_chat_service)
):
    try:
        chat_body.index_name = format_index_name(chat_body.index_name)
        response = await chat_service.chat_non_streaming(chat_body)
        return response.model_dump()

    except Exception as e:
        return JSONResponse(status_code=500, content={
            "ok": False,
            "error": str(e),
        })
@router.post("/chat/stream")
async def chat_stream(
        chat_body: ChatBody,
        chat_service: ChatService = Depends(get_chat_service),
):
    chat_body.index_name = format_index_name(chat_body.index_name)

    async def event_generator():
        """SSE format: data: {json}\n\n"""
        try:
            async for chunk in chat_service.chat_stream_sse(body=chat_body):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            yield f"data: {{'error': '{str(e)}'}}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"  # Nginx proxy fix
        }
    )


@router.get("/chat/qg/{job_id}")
async def poll_qg_result(
        job_id: str,
        chat_service: ChatService = Depends(get_chat_service)
):
    """Frontend poll để lấy follow-up questions"""
    try:
        result = await chat_service.bq_queue.get_result(job_id)

        if result is None:
            return JSONResponse({
                "status": "pending",
                "job_id": job_id
            })

        return JSONResponse({
            "status": "completed",
            "job_id": job_id,
            "questions": result
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "failed",
                "error": str(e)
            }
        )
# ============================================================
# Request/Response checkpoints
# ============================================================