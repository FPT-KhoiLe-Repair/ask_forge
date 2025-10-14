import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List
from tempfile import NamedTemporaryFile
import os, json

# LangChain splitters & PDF loader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
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

@app.post("/api/build_index")
async def build_index(
    files: List[UploadFile] = File(...),
    index_name: str = Form(default="default"),
):
    try:
        if not files:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": "No files uploaded!"}
            )

        # 0) Chuẩn bị splitter như trước
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )

        all_chunks = []  # cấu trúc để ghi ra pages.json
        total_pages = 0
        total_raw_chunks = 0

        for uf in files:
            # 1) Lưu UploadFile thành file tạm (đảm bảo có .pdf)
            suffix = ".pdf" if not uf.filename.lower().endswith(".pdf") else ""
            with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(await uf.read())
                tmp_path = tmp.name

            try:
                # 2) Load PDF → docs (mỗi trang là 1 Document)
                loader = PyPDFLoader(tmp_path)
                docs = loader.load()
                total_pages += len(docs)

                # 3) Split như code cũ
                raw_chunks = splitter.split_documents(docs)
                total_raw_chunks += len(raw_chunks)

                # 4) Lọc theo MIN_CHARS
                kept = [c for c in raw_chunks if len((c.page_content or "").strip()) >= MIN_CHARS]

                # 5) Chuẩn hóa content để ghi ra JSON
                contents = []
                for i, c in enumerate(kept):
                    page0 = c.metadata.get("page", 0)
                    page1 = int(page0) + 1  # chuyển sang 1-based
                    contents.append({
                        "text": c.page_content,
                        "page": page1,
                        "chunk_id": f"{page1}_{i}",
                    })

                all_chunks.append({
                    "source": uf.filename,
                    "content": contents
                })
            finally:
                # 6) Xóa file tạm
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

        # 7) (Tuỳ chọn) ghi ra file Experiments/datas/pages.json
        os.makedirs("D:/Works/AskForge/downstream/Experiments/datas", exist_ok=True)
        with open("D:/Works/AskForge/downstream/Experiments/datas/pages.json", "w", encoding="utf-8") as f:
            json.dump(all_chunks, f, ensure_ascii=False, indent=2)

        if not all_chunks:
            return JSONResponse(status_code=400, content={"detail": "No text extracted"})

        kept_chunks_after_min_chars = sum(len(item["content"]) for item in all_chunks)

        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "index_name": index_name,
                "total_files": len(files),
                "total_pages": total_pages,
                "total_raw_chunks": total_raw_chunks,
                "kept_chunks_after_min_chars": kept_chunks_after_min_chars,
                "message": f"Index '{index_name}' built successfully"
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal Server Error: {str(e)}"}
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

    