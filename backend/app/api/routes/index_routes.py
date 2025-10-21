from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List

from ask_forge.backend.app.services.indexing import build_index, add_to_index, load_index
from ask_forge.backend.app.models.dto import BuildIndexResponse, Metrics

router = APIRouter(prefix="/api", tags=["index"])

@router.post("/build_index", response_model=BuildIndexResponse)
async def build_index_ep(
        files: List[UploadFile] = File(...),
        index_name: str = Form(default="default"),
):
    if not files:
        return JSONResponse(status_code=400, content={"ok": False, "error": "No files provided"})

    all_chunks, metrics = await build_index(files, index_name)
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
):
    if not files:
        return JSONResponse(status_code=400, content={"ok": False, "error": "No files uploaded!"})

    _, metrics = await add_to_index(files, index_name)
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
    data = load_index(index_name)
    return {"ok": True, "index_name": index_name, "data": data}
