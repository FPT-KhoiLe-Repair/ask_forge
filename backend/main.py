from typing import List
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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

@app.post("/api/build_index")
async def build_index(
    files: List[UploadFile] = File(...),
    index_name: str = Form(default="default"),
):
    if not files:
        raise  HTTPException(status_code=400, detail="No files uploaded")

    # TODO: parse PDF, chunk, embed, build FAISS
    filenames = [f.filename for f in files]

    return {
        "statusCode": 200,
        "index_name": index_name,
        "n_files": len(files),
        "files": filenames,
        "message": f"Index '{index_name}' built successfully",
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

    