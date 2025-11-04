"""
Application State Manager - Quản lý lifecycle và global resources.

Singleton pattern để đảm bảo chỉ có 1 instance ChromaDB, checkpoints, etc.
Khởi tạo khi app startup, cleanup khi shutdown.
"""
import asyncio
from functools import lru_cache
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import logging

from ask_forge.backend.app.repositories.vectorstore import ChromaRepo
from ask_forge.backend.app.core.config import settings
from ask_forge.backend.app.services.chat_history.chat_history import InMemoryHistoryRepo

import os, torch
from pathlib import Path
import google.genai as genai

logger = logging.getLogger(__name__)

CORE_DIR = Path(__file__).resolve().parent  # …/backend/app/core
APP_DIR = CORE_DIR.parent  # …/backend/app
BACKEND_DIR = APP_DIR.parent  # …/backend
PROJECT_ROOT = BACKEND_DIR.parent  # …/ask_forge

class AppState:
    """
    Singleton class quản lý tất cả global resources của application.

    Attributes:
        chroma_repo: ChromaDB repository instance (singleton)
        loaded_models: Dictionary chứa các ML models đã load
        active_indexes: Set các index names đang tồn tại
    """
    _instance: Optional["AppState"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Đặt cờ cho lần khởi tạo đầu tiên của instance
            cls._instance._constructed = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_constructed", False):
            return

        # ---- Fields chỉ tạo 1 lần ----
        self._init_lock = asyncio.Lock()   # Lock để tránh race khi startup
        self._initialized = False          # Chỉ True sau khi startup xong

        self.chroma_repo: Optional[ChromaRepo] = None
        self.loaded_models: Dict[str, Any] = {}
        self.active_indexes: set[str] = set()

        # HF (lazy)
        self._hf_tok = None
        self._hf_model = None
        self._hf_lock = asyncio.Lock() # Tránh double-load HF

        # History repo
        self.history_repo = InMemoryHistoryRepo(
            default_last_k=12,
            max_turns_per_session=800)

        # --------------------------------
        self._constructed = True
        logger.info("AppState constructed")

    @lru_cache(maxsize=None)
    def ensure_gemini_client(self) -> genai.Client:
        """
        Trả về 1 instance google.genai.Client, cache theo process
        Yêu cầu: settings.GEMINI_API_KEY
        """
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise RuntimeError(("❌ Missing GEMINI_API_KEY in env/.env (core/config.py)"))
        return genai.Client(api_key=api_key)

    def get_gemini_model_name(self) -> str:
        """Tên model Gemini mặc định lấy từ settings"""
        return settings.GEMINI_MODEL_NAME

    # ------------------------------
    # HF model: lazy & thread-safe
    # ------------------------------
    async def ensure_hf_model(self, model_repo):
        """
        Lazy-load HF CasualLM + tokenizer (non-blocking event-loop).
        - Nếu không dùng hf repo: dùng Qwen/Qwen2.5-0.5B
        """
        if self._hf_model is not None:
            return self._hf_tok, self._hf_model

        async with self._hf_lock:
            if self._hf_model is not None:
                return self._hf_tok, self._hf_model

            qg_ckpt = APP_DIR.joinpath("services","checkpoints","QG_Models")
            qwen_ckpt = qg_ckpt / model_repo
            # dtype/device config
            prefer_bf16 = settings.HF_DTYPE.lower() in {"bf16", "bfloat16"}
            dtype = torch.bfloat16 if prefer_bf16 and torch.cuda.is_available() else "auto"

            device_map = settings.HF_DEVICE_MAP


            logger.info("🧠 Loading HF model %s (device_map=%s, dtype=%s)...", qwen_ckpt, device_map, dtype)

            loop = asyncio.get_running_loop()

            def _load_sync():
                from transformers import AutoTokenizer, AutoModelForCausalLM
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
                # Import nặng để trong hàm -> chỉ import khi cần
                tok = AutoTokenizer.from_pretrained(
                    qwen_ckpt,
                )
                model = AutoModelForCausalLM.from_pretrained(
                    qwen_ckpt,
                    dtype=dtype,
                    device_map=device_map,
                ).to(device).eval()
                return tok, model
        self._hf_tok, self._hf_model = await loop.run_in_executor(None, _load_sync)
        logger.info(f"✅ HF model loaded. Model: {self._hf_model}")
        return self._hf_tok, self._hf_model

    def unload_hf_model(self):
        """Giải phóng GPU/VRAM khi tắt app."""
        if self._hf_model is not None:
            try:
                # chuyển v CPU trước khi drop reference
                try:
                    self._hf_model.to("cpu")
                except Exception:
                    pass
                self._hf_model = None
                self._hf_tok = None
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                elif getattr(torch, "mps", None) and torch.backends.mps.is_available():
                    try:
                        torch.mps.empty_cache()
                    except Exception:
                        pass
                logger.info("🧹 HF model unloaded")
            except Exception:
                logger.exception("Failed to unload HF model safely!")

    # ------------------------------
    # App lifecycle
    # ------------------------------
    async def startup(self):
        """
        Khởi tạo chroma_repo, ensure_hf_model.
        Gọi hàm này trong FastAPI lifespan event.
        """
        async with self._init_lock:
            if self._initialized:
                return

            logger.info("🚀 Starting up application resources...")

            # 1) Khởi tạo ChromaDB
            try:
                logger.info("📦 Initializing ChromaDB repository...")
                self.chroma_repo = ChromaRepo()

                # Load danh sách các collections hiện có
                collections = self.chroma_repo.list_collections()

                self.active_indexes = {col.name for col in collections}
                logger.info(
                    "✅ ChromaDB ready. Found %d existing indexes: %s",
                    len(self.active_indexes), self.active_indexes
                )
            except Exception as e:
                logger.exception(f"❌ Failed to initialize ChromaDB. Error: {e}")
                # _initialized vẫn False nếu fail
                raise

            # 2) Load ML checkpoints
            try:
                if settings.HF_PRELOAD_AT_STARTUP:
                    await  self.ensure_hf_model(settings.HF_QG_CKPT)
                else:
                    logger.info("ℹ️ HF preload disabled (HF_RELOAD_AT_STARTUP==False)")
            except Exception:
                logger.exception("❌ Failed to preload HF model (will continue without it)")

            self._initialized = True
            logger.info("✅ All application resources started successfully")

    async def shutdown(self):
        """
        Cleanup resources khi app shutdown.
        """
        logger.info("🛑 Shutting down application resources...")

        # HF model
        self.unload_hf_model()

        # Cleanup ChromaDb nếu cần
        if self.chroma_repo:
            try:
                # Nếu có handle close/flush, gọi ở đây (ChromaRepo optional)
                logger.info("📦 ChromaDB persisted to disk")
            finally:
                self.chroma_repo = None

        if self.loaded_models:
            logger.info("🧠 Unloading ML models...")
            self.loaded_models.clear()

        self._initialized = False
        logger.info("✅ All resources cleaned up")

    # ------------------------------
    # Utilities
    # ------------------------------
    def get_chroma_repo(self) -> ChromaRepo:
        """
        Lấy ChromaDB repository instance.

        Raises:
            RuntimeError: Nếu chưa được khởi tạo (startup chưa chạy)
        """
        if self.chroma_repo is None:
            raise RuntimeError(
                "ChromaDB not initialized. Make sure app_state.startup() was called."
            )
        return self.chroma_repo

    def refresh_active_indexes(self):
        """Đồng bộ lại active_indexes từ Chroma khi có thay đổi ngoài luồng."""
        if not self.chroma_repo:
            raise RuntimeError("ChromaDB not initialized. Make sure app_state.startup() was called.")
        cols = self.chroma_repo.list_collections()
        self.active_indexes = {c.name for c in cols}

    def register_index(self, index_name: str):
        """Đăng ký index mới vào active set."""
        self.active_indexes.add(index_name)
        logger.info("📝 Registered index: %s", index_name)

    def unregister_index(self, index_name: str):
        self.active_indexes.discard(index_name)
        logger.info("🗑️ Unregistered index: %s", index_name)

    def index_exists(self, index_name: str) -> bool:
        """Kiểm tra xem index có tồn tại không."""
        return index_name in self.active_indexes

    def get_model(self, model_name: str) -> Optional[Any]:
        """Lấy ML model đã load."""
        return self.loaded_models.get(model_name)

# ---- The SINGLE way to obtain AppState everywhere ----
@lru_cache(maxsize=1)
def get_app_state() -> AppState:
    return AppState()


app_state = get_app_state() # <- dùng đúng cùng 1 instance
@asynccontextmanager
async def lifespan_manager(app):
    """
        FastAPI lifespan context manager.

        Usage trong main.py:
            app = FastAPI(lifespan=lifespan_manager)
        """
    await app_state.startup()
    app.state.app_state = app_state

    try:
        yield
    finally:
        await app_state.shutdown()
