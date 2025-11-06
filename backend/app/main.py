from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
import time, uuid, logging
from prometheus_fastapi_instrumentator import Instrumentator

from ask_forge.backend.app.core.config import settings
from ask_forge.backend.app.core.logging import setup_logging
from ask_forge.backend.app.core.app_state import lifespan_manager
from ask_forge.backend.app.api.routes.index_routes import router as index_router
from ask_forge.backend.app.api.routes.chat_routes import router as chat_router
from ask_forge.backend.app.core.logging import request_id_var

# 0) Logging
setup_logging()
access_logger = logging.getLogger("askforge.access")

# 1) App
app = FastAPI(
    title=settings.APP_NAME,
    version=getattr(settings, "APP_VERSION", "0.1.0"),
    description="AskForge Backend – RAG + Question Generation APIs",
    contact={"name": "AskForge Team", "email": "team@askforge.local"},
    license_info={"name": "MIT"},
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan_manager,
)

# 2) CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(o) for o in settings.CORS_ORIGINS] or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 4) Routers
API_PREFIX = getattr(settings, "APP_PREFIX", "/api")
app.include_router(index_router, prefix=API_PREFIX)
app.include_router(chat_router,  prefix=API_PREFIX)

# 5) /metrics (Prometheus)
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

@app.get("/")
async def hello():
    return {"message": "Welcome to Ask Forge!"}

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    token = request_id_var.set(req_id)
    try:
        resp = await call_next(request)
        resp.headers["X-Request-ID"] = req_id
        return resp
    finally:
        request_id_var.reset(token)