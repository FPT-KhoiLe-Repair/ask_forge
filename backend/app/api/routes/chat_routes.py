"""
Chat/Query routes - sử dụng ChromaDB để retrieve context cho RAG.
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse
import json
import asyncio

from ask_forge.backend.app.core.app_state import app_state
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
    request: Request,
    chat_service: ChatService = Depends(get_chat_service),
):
    chat_body.index_name = format_index_name(chat_body.index_name)
    return await chat_service.chat_stream_sse(body=chat_body)

    def sse_encode(payload) -> str:
        # Mỗi event phải kết thúc bằng \n\n
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    async def event_generator():
        try:
            # ❌ Sai: async for chunk in await chat_service.chat_stream_sse(...)
            # ✅ Đúng:
            async for chunk in chat_service.chat_stream_sse(body=chat_body):
                # Nếu client đóng kết nối thì dừng
                if await request.is_disconnected():
                    break

                # chunk có thể là string token hoặc dict đã format sẵn
                if isinstance(chunk, (dict, list)):
                    yield sse_encode(chunk)
                else:
                    # gói lại thành event "token"
                    yield sse_encode({"type": "token", "content": str(chunk)})

            # Kết thúc bình thường
            yield "data: [DONE]\n\n"

        except asyncio.CancelledError:
            # Client hủy kết nối: thoát im lặng (Starlette sẽ đóng response)
            raise

        except Exception as e:
            # Báo lỗi đúng chuẩn JSON + SSE
            yield sse_encode({"type": "error", "content": str(e)})
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # nếu đi qua Nginx
        },
    )


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
# ============================================================
# Request/Response checkpoints
# ============================================================