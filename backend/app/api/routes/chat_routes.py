"""
Chat/Query routes - sử dụng ChromaDB để retrieve context cho RAG.
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from ask_forge.backend.app.core.app_state import app_state
from ask_forge.backend.app.services.chat.service import ChatService
from ask_forge.backend.app.api.dependencies import get_chat_service

from ask_forge.backend.app.utils.naming import format_index_name
from ask_forge.backend.app.services.chat.schemas import ChatBody

router = APIRouter(
    tags=["chat"],
)

@router.post("/chat/stream")
async def chat_stream(
    chat_body: ChatBody,
    request: Request,
    chat_service: ChatService = Depends(get_chat_service),
):
    chat_body.index_name = format_index_name(chat_body.index_name)
    return await chat_service.chat_stream_sse(body=chat_body)


@router.get("/chat/qg/{job_id}")
async def poll_qg_result(
        job_id: str,
        chat_service: ChatService = Depends(get_chat_service)
):
    """Frontend poll để lấy follow-up questions"""
    try:
        result = await app_state.bq.get_result(job_id)

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