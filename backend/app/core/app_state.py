"""
Application State Manager - Quản lý lifecycle và global resources.

Singleton pattern để đảm bảo chỉ có 1 instance ChromaDB, Models, etc.
Khởi tạo khi app startup, cleanup khi shutdown.
"""
import asyncio
from functools import lru_cache
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import logging

from ask_forge.backend.app.repositories.vectorstore import ChromaRepo
from ask_forge.backend.app.core.config import settings
import os, torch

logger = logging.getLogger(__name__)

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
        # --------------------------------
        self._constructed = True
        logger.info("AppState constructed")

    # ------------------------------
    # HF model: lazy & thread-safe
    # ------------------------------
    async def ensure_hf_model(self):
        """
        Lazy-load HF CasualLM + tokenizer (non-blocking event-loop).
        Dùng thread executor để không block loop khi from_pretrained
        """
        if self._hf_model is not None:
            return self._hf_tok, self._hf_model

        async with self._hf_lock:
            if self._hf_model is not None:
                return self._hf_tok, self._hf_model

            ckpt = settings.HF_MODEL_CKPT
            local_only = settings.HF_LOCAL_ONLY=="1"

            if os.path.isdir(ckpt):
                local_only = True

            trust_remote = settings.HF_TRUST_REMOTE_CODE== "1"
            low_cpu_mem = settings.HF_LOW_CPU_MEM== "1"

            # dtype/device config
            prefer_bf16 = settings.HF_DTYPE.lower() in {"bf16", "bfloat16"}
            dtype = torch.bfloat16 if prefer_bf16 and torch.cuda.is_available() else "auto"

            device_map = settings.HF_DEVICE_MAP

            logger.info("🧠 Loading HF model %s (device_map=%s, dtype=%s)...", ckpt, device_map, dtype)

            loop = asyncio.get_running_loop()

            def _load_sync():
                # Import nặng để trong hàm -> chỉ import khi cần
                from transformers import AutoTokenizer, AutoModelForCausalLM
                tok = AutoTokenizer.from_pretrained(
                    ckpt,
                    trust_remote_code=trust_remote,
                    local_files_only=local_only,
                )
                model = AutoModelForCausalLM.from_pretrained(
                    ckpt,
                    torch_dtype=dtype,
                    device_map=device_map,
                    low_cpu_mem=low_cpu_mem,
                    trust_remote_code=trust_remote,
                    local_files_only=local_only,
                )
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
                self.hf_tok = None
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
        Khởi tạo tất cả resources khi app startup.
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

                prefix = getattr(settings, "CHROMA_COLLECTION_PREFIX", None)
                def strip_prefix(name: str) -> str:
                    if not prefix:
                        return name
                    return name[len(prefix):] if name.startswith(prefix) else name

                self.active_indexes = {strip_prefix(col.name) for col in collections}
                logger.info(
                    "✅ ChromaDB ready. Found %d existing indexes: %s",
                    len(self.active_indexes), self.active_indexes
                )
            except Exception:
                logger.exception("❌ Failed to initialize ChromaDB")
                # _initialized vẫn False nếu fail
                raise

            # 2) Load ML Models
            try:
                if os.getenv("HF_RELOAD_AT_STARTUP", "0") == "1":
                    await  self.ensure_hf_model()
                else:
                    logger.info("ℹ️ HF preload disabled (HF_PRELOAD_AT_STARTUP!=1)")
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
        prefix = getattr(settings, "CHROMA_COLLECTION_PREFIX", None)
        def strip_prefix(name: str) -> str:
            if not prefix:
                return name
            return name[len(prefix):] if name.startswith(prefix) else name
        cols = self.chroma_repo.list_collections()
        self.active_indexes = {strip_prefix(c.name) for c in cols}

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

    try:
        yield
    finally:
        await app_state.shutdown()
