from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ask_forge.backend.app.core.config import settings
from ask_forge.backend.app.core.logging import setup_logging
from ask_forge.backend.app.api.routes.index_routes import router as index_router
import uvicorn

setup_logging()
app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(o) for o in settings.CORS_ORIGINS] or [
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

app.include_router(index_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

    