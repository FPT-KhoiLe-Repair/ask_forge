from pathlib import Path

import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Tuple, Dict, Any
from tempfile import NamedTemporaryFile
import os, json

# LangChain splitters & PDF loader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader


async def extract_all_chunks(
        files: List[UploadFile],
        splitter: RecursiveCharacterTextSplitter,
        min_chars: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    all_chunks: List[Dict[str, Any]] = []
    total_pages = 0
    total_raw_chunks = 0

    for uf in files:
        suffix = ".pdf" if not uf.filename.lower().endswith(".pdf") else ""
        tmp_path = None

        try:
            # 1️⃣ Lưu file tạm
            with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(await uf.read())
                tmp_path = tmp.name

            # 2️⃣ Load PDF → docs
            loader = PyPDFLoader(tmp_path)
            docs = loader.load()
            total_pages += len(docs)

            # 3️⃣ Split thành chunks
            raw_chunks = splitter.split_documents(docs)
            total_raw_chunks += len(raw_chunks)

            # 4️⃣ Lọc theo min_chars
            kept = [c for c in raw_chunks if len((c.page_content or "").strip()) >= min_chars]

            # 5️⃣ Tạo content list có chunk_id theo thứ tự
            contents = []
            # Tạo counter cho từng page
            page_counters: Dict[int, int] = {}

            for c in kept:
                page0 = c.metadata.get("page", 0)
                page1 = int(page0) + 1  # 1-based index

                # Đếm chunk theo page
                page_counters[page1] = page_counters.get(page1, 0) + 1
                chunk_num = page_counters[page1]

                chunk_id = f"p{page1}_c{chunk_num}"

                contents.append({
                    "text": c.page_content,
                    "page": page1,
                    "chunk_id": chunk_id
                })

            all_chunks.append({
                "source": uf.filename,
                "content": contents
            })

        finally:
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
        "http://10.10.10.237:3000"
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
MIN_CHARS = 300
PAGES_JSON_PATH = "/downstream/Experiments/user_db/"

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
            with open(PAGES_JSON_PATH + f"{index_name}.json", "r", encoding="utf-8") as f:
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
        print(e)
        return JSONResponse(status_code=500, content={"detail": f"Internal Server Error: {str(e)}"})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

    