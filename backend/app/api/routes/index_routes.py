"""
Updated index routes sử dụng dependencies và AppState.
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends
from ask_forge.backend.app.api.dependencies import get_app_state, get_chroma_repo
from ask_forge.backend.app.core.app_state import AppState
from ask_forge.backend.app.repositories.vectorstore import ChromaRepo
from ask_forge.backend.app.services.indexing.schemas import BuildIndexResponse, Metrics
from ask_forge.backend.app.services.indexing.pipeline import build_index, add_to_index, load_index
from ask_forge.backend.app.utils.naming import format_index_name
from fastapi.responses import JSONResponse
from typing import List

# ----------------------------------------------------------------------------------

router = APIRouter(tags=["index"])

@router.post("/build_index", response_model=BuildIndexResponse)
async def build_index_ep(
        files: List[UploadFile] = File(...),
        index_name: str = Form(default="default"),
        app_state: AppState = Depends(get_app_state),  # 🔥 Inject state
        repo: ChromaRepo = Depends(get_chroma_repo),  # 🔥 Inject singleton
):
    """
        Build index từ uploaded PDFs.
        ChromaDB repository được inject tự động từ AppState singleton.
        """

    index_name = format_index_name(index_name)
    if not files:
        return (JSONResponse
                (status_code=400,
                 content={"ok": False, "error": "No files provided"}))
    try:
        all_chunks, metrics = await build_index(files, index_name, repo)
    except Exception as e:
        return (JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        ))

    app_state.register_index(index_name)

    return BuildIndexResponse(
        ok=True,
        index_name=index_name,
        total_files=str(len(files)),
        message=f"Index '{index_name}' built successfully",
        metrics=Metrics(**metrics),
    )

@router.post("/add_to_index", response_model=BuildIndexResponse)
async def add_to_index_ep(
        files: List[UploadFile] = File(...),
        index_name: str = Form(default="default"),
        repo: ChromaRepo = Depends(get_chroma_repo),
        state: AppState = Depends(get_app_state),
):
    """Add files to existing index."""
    index_name = format_index_name(index_name)
    if not files:
        return JSONResponse(status_code=400,
                            content={"ok": False, "error": "No files uploaded!"})

    _, metrics = await add_to_index(files, index_name, repo)

    state.register_index(index_name)

    return BuildIndexResponse(
        ok=True,
        index_name=index_name,
        total_files=str(len(files)),
        message=f"Index '{index_name}' added successfully",
        metrics=Metrics(**metrics),
    )

@router.get("/load_index", response_model=BuildIndexResponse)
async def load_index_ep(
        index_name: str = Form(default="default"),
):
    index_name = format_index_name(index_name)
    data = load_index(index_name)
    return {"ok": True, "index_name": index_name, "data": data}

@router.get("/active_indexes")
async def list_indexes(
        state: AppState = Depends(get_app_state),
):
    """
    List tất cả indexes hiện có.

    Trả về danh sách indexes từ AppState.
    """
    return {
        "ok": True,
        "active_indexes": list(state.active_indexes),
        "count": len(state.active_indexes),
    }

@router.get("/index/{index_name}/stats")
async def get_index_stats(
        index_name: str,
        repo: ChromaRepo = Depends(get_chroma_repo),
):
    """
    Lấy thống kê về một index cụ thể.

    Returns số lượng chunks, metadata, etc.
    """
    index_name = format_index_name(index_name)
    try:
        stats = repo.get_collection_stats(index_name)
        return {
            "ok": True,
            "index_name": index_name,
            "stats": stats,
        }
    except ValueError as e:
        return JSONResponse(
            status_code=404,
            content={"ok": False, "error": str(e)},
        )

@router.delete("/index/{index_name}")
async def delete_index(
        index_name: str,
        repo: ChromaRepo = Depends(get_chroma_repo),
        state: AppState = Depends(get_app_state),
):
    """
    Xóa một index (collection + JSON file).
    """
    index_name = format_index_name(index_name)
    try:
        # Xóa ChromDB collection
        repo.delete_collection(index_name)

        # Xóa JSON file
        from ask_forge.backend.app.constants import PAGES_JSON_DIR
        json_file = PAGES_JSON_DIR / f"{index_name}.json"
        if json_file.exists():
            json_file.unlink()

        # Remove khỏi AppState
        state.active_indexes.discard(index_name)

        return {
            "ok": True,
            "message": f"Index '{index_name}' deleted successfully",
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)},
        )
