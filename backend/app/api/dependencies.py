"""
Updated dependencies với AppState integration.
"""
from fastapi import Depends, HTTPException, Header
from typing import Optional

from ask_forge.backend.app.core.config import settings
from ask_forge.backend.app.core.app_state import app_state
from ask_forge.backend.app.repositories.vectorstore import ChromaRepo

def get_settings():
    """Dependency để inject settings"""
    return settings

def get_chroma_repo() -> ChromaRepo:
    """
    Dependency để inject ChromaDB repository.

    Sử dụng singleton instance từ AppState thay vì tạo mới mỗi request.

    Usage:
        @app.get("/search")
        async def search(repo: ChromaRepo = Depends(get_chroma_repo)):
            results = repo.query(...)
    """
    return app_state.get_chroma_repo()

def get_current_index(
        index_name: Optional[str] = Header(None, alias="X-Index-Name")
) -> str:
    """
        Dependency để lấy index name từ header hoặc query param.

        Usage:
            @app.get("/query")
            async def query_index(
                q: str,
                index: str = Depends(get_current_index)
            ):
                # index sẽ được validate tự động
                ...

        Args:
            index_name: Index name từ header "X-Index-Name"

        Returns:
            str: Validated index name

        Raises:
            HTTPException: Nếu index không tồn tại
        """
    if not index_name:
        index_name = "default"

    # Validate index nếu tồn tại
    if not app_state.index_exists(index_name):
        raise HTTPException(
            status_code=404,
            detail=f"Index name '{index_name}' not found. Available indexes: {list(app_state.activate_indexes)}"
        )
    return index_name

def get_app_state():
    """
    Dependency để inject toàn bộ AppState.

    Dùng khi cần access nhiều resources cùng lúc.
    """
    return app_state