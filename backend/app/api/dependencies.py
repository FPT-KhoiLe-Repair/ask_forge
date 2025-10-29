"""
Updated dependencies với AppState integration.
"""
from typing import Optional, Annotated
from fastapi import Depends, HTTPException, Header, Request, Query

from ask_forge.backend.app.core.config import settings
from ask_forge.backend.app.core.app_state import AppState
from ask_forge.backend.app.repositories.vectorstore import ChromaRepo
from ask_forge.backend.app.services.chat.service import ChatService

DEFAULT_INDEX = getattr(settings, "DEFAULT_INDEX", "default")

# ---------- Core DI ----------
def get_app_state(request: Request) -> AppState:
    """
    Lấy instance AppState đã được gắn trong lifespan: app.state.app_state
    """
    app_state = getattr(request.app.state, "app_state", None)
    if app_state is None:
        # Service chưa sẵn sàng (lifespan chưa chạy hoặc lỗi startup)
        raise HTTPException(status_code=503, detail="AppState not initialized")
    return app_state

def get_settings() -> type[settings]:
    """Inject settings (read-only)."""
    return settings

def get_chroma_repo(app_state: Annotated[AppState, Depends(get_app_state)]) -> ChromaRepo:
    """
    Inject ChromaDB repository từ AppState.
    """
    return app_state.get_chroma_repo()

def get_chat_service(
        app_state: AppState = Depends(get_app_state),
        repo: ChromaRepo = Depends(get_chroma_repo)
) -> ChatService:
    return ChatService(app_state=app_state, repo=repo)
