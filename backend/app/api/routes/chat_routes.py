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
        response = await chat_service.chat_with_followup(chat_body)
        return response.model_dump()

    except Exception as e:
        return JSONResponse(status_code=500, content={
            "ok": False,
            "error": str(e),
        })
@router.post("/chat/stream")
async def chat_stream(
        chat_body: ChatBody, # Đây sẽ là JSON type
        chat_service: ChatService = Depends(get_chat_service),
):
    chat_body.index_name = format_index_name(chat_body.index_name)
    gen = chat_service.chat_stream(body=chat_body)
    return StreamingResponse(gen, media_type="application/octet-stream")

# ============================================================
# Request/Response checkpoints
# ============================================================