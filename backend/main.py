from pathlib import Path

import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Tuple, Dict, Any, Optional
from tempfile import NamedTemporaryFile
import os, json

# LangChain splitters & PDF loader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

async def extract_all_chunks(
    files: List[UploadFile],
    splitter: RecursiveCharacterTextSplitter,
    min_chars: int,
    make_chunk_id: Optional[callable] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Đọc danh sách UploadFile (PDF), split theo splitter, lọc theo min_chars,
    trả về (all_chunks, metrics).

    all_chunks: [
      {"source": "<original filename>", "content": [
         {"text": "...", "page": 1-based, "chunk_id": "..."}, ...
      ]},
      ...
    ]

    metrics: {"total_pages": int, "total_raw_chunks": int, "kept_chunks_after_min_chars": int}
    """

    all_chunks: List[Dict[str, Any]] = []
    total_pages = 0
    total_raw_chunks = 0

    # chunk_id mặc định: <stem>-<page>-<i> để tránh trùng giữa nhiều file
    def _default_chunk_id(source_name: str, page1: int, i: int) -> str:
        stem = Path(source_name).stem
        return f"{stem}_{page1}_{i}"

    make_chunk_id = make_chunk_id or _default_chunk_id

    for uf in files:
        suffix = ".pdf" if not uf.filename.lower().endswith(".pdf") else ""
        tmp_path = None

        try:
            # Lưu file upload ra file tạm (Windows cần delete=False để loader có thể mở)
            with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(await uf.read())
                tmp_path = tmp.name

            # Load mỗi trang thành 1 Document
            loader = PyPDFLoader(tmp_path)
            docs = loader.load()
            total_pages += len(docs)

            # Split
            raw_chunks = splitter.split_documents(docs)
            total_raw_chunks += len(raw_chunks)

            # Lọc theo min_chars
            kept = [c for c in raw_chunks if len((c.page_content or "").strip()) >= min_chars]

            # Chuẩn hoá content
            contents = []
            for i, c in enumerate(kept):
                page0 = c.metadata.get("page", 0)
                page1 = int(page0) + 1  # 1-based cho dễ đọc
                contents.append({
                    "text": c.page_content,
                    "page": page1,
                    "chunk_id": make_chunk_id(uf.filename, page1, i),
                })

            all_chunks.append({
                "source": uf.filename,
                "content": contents
            })

        finally:
            # Xoá file tạm nếu có
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    kept_chunks_after_min_chars = sum(len(item["content"]) for item in all_chunks)

    metrics = {
        "total_pages": total_pages,
        "total_raw_chunks": total_raw_chunks,
        "kept_chunks_after_min_chars": kept_chunks_after_min_chars,
    }
    return all_chunks, metrics


def write_pages_json(all_chunks: List[Dict[str, Any]], out_path: str) -> None:
    """Ghi all_chunks ra JSON (tự tạo thư mục nếu chưa có)."""
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)




app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://192.168.11.154:3000",
    ],

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def hello():
    return {"message": "Welcome to Ask Forge!"}

CHUNK_SIZE = 1024
CHUNK_OVERLAP = 300
MIN_CHARS = 100
PAGES_JSON_PATH = "D:/Works/AskForge/downstream/Experiments/datas/"

@app.post("/api/build_index")
async def build_index(
    files: List[UploadFile] = File(...),
    index_name: str = Form(default="default"),
):
    try:
        if not files:
            return JSONResponse(status_code=400, content={"ok": False, "error": "No files uploaded!"})

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )

        all_chunks, metrics = await extract_all_chunks(
            files=files,
            splitter=splitter,
            min_chars=MIN_CHARS,
            # make_chunk_id=lambda src, p, i: f"{p}_{i}",  # nếu muốn giữ kiểu cũ
        )

        if not all_chunks:
            return JSONResponse(status_code=400, content={"ok": False, "error": "No text extracted"})

        # (tuỳ chọn) ghi ra JSON
        write_pages_json(all_chunks, PAGES_JSON_PATH + f"{index_name}.json")

        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "index_name": index_name,
                "total_files": len(files),
                **metrics,
                "message": f"Index '{index_name}' built successfully",
            },
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Internal Server Error: {str(e)}"})


    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal Server Error: {str(e)}"}
        )
@app.post("/api/add_to_index")
async def add_to_index(
    files: List[UploadFile] = File(...),
    index_name: str = Form(default="default"),
):
    try:
        if not files:
            return JSONResponse(status_code=400, content={"ok": False, "error": "No files uploaded!"})

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )

        all_chunks, metrics = await extract_all_chunks(files, splitter, MIN_CHARS)

        # tuỳ yêu cầu: có thể merge với pages.json cũ hoặc ghi file riêng
        # ví dụ merge:
        try:
            with open(PAGES_JSON_PATH, "r", encoding="utf-8") as f:
                old = json.load(f)
        except FileNotFoundError:
            old = []
        write_pages_json(old + all_chunks, PAGES_JSON_PATH + f"{index_name}.json")

        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "index_name": index_name,
                "added_files": len(files),
                **metrics,
                "message": f"Added to index '{index_name}'",
            },
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Internal Server Error: {str(e)}"})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

    