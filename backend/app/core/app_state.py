"""
Application State Manager - Quản lý lifecycle và global resources.

Singleton pattern để đảm bảo chỉ có 1 instance ChromaDB, Models, etc.
Khởi tạo khi app startup, cleanup khi shutdown.
"""

from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import logging

from ask_forge.backend.app.repositories.vectorstore import ChromaRepo
from ask_forge.backend.app.core.config import settings

logger = logging.getLogger(__name__)

class AppState:
    """
    Singleton class quản lý tất cả global resources của application.

    Attributes:
        chroma_repo: ChromaDB repository instance (singleton)
        loaded_models: Dictionary chứa các ML models đã load
        active_indexes: Set các index names đang tồn tại
    """
    _instance : Optional['AppState'] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.chroma_repo: Optional[ChromaRepo] = None
        self.loaded_models: Dict[str, Any] = {}
        self.active_indexes: set = set()

        logger.info("AppState Initialized")
    async def startup(self):
        """
        Khởi tạo tất cả resources khi app startup.
        Gọi hàm này trong FastAPI lifespan event.
        """
        logger.info("🚀 Starting up application resources...")

        # 1. Khởi tạo ChromaDB
        try:
            logger.info("📦 Initializing ChromaDB repository...")
            self.chroma_repo = ChromaRepo()

            # Load danh sách các collections hiện có
            collections = self.chroma_repo.list_collections()
            self.active_indexes = {
                col.name.replace(settings.CHROMA_COLLECTION_PREFIX, "")
                for col in collections
            }
            logger.info(f"✅ ChromaDB ready. Found {len(self.active_indexes)} existing indexes: {self.active_indexes}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB: {e}")
            raise

        # 2. Load ML Models (nếu có)
        await self.__load_ml_models()
        logger.info("✅ All application resources started successfully")

    async def __load_ml_models(self):
        """
        Load các ML models vào GPU/memory khi startup.
        Ví dụ: LLM, reranker, embedding models, etc.
        """
        try:
            # Ví dụ: Load LLM model
            # logger.info("🧠 Loading LLM model...")
            # from transformers import AutoModelForCausalLM, AutoTokenizer
            # model_name = "meta-llama/Llama-2-7b-chat-hf"
            # self.loaded_models['llm'] = AutoModelForCausalLM.from_pretrained(
            #     model_name,
            #     device_map="auto",
            #     torch_dtype=torch.float16
            # )
            # self.loaded_models['tokenizer'] = AutoTokenizer.from_pretrained(model_name)
            # logger.info(f"✅ LLM model loaded: {model_name}")

            # Placeholder cho tương lai
            logger.info("ℹ️  No ML models configured to load at startup")

        except Exception as e:
            logger.error(f"❌ Failed to load ML models: {e}")
            # Không raise error, cho phép app chạy mà không có model

    async def shutdown(self):
        """
        Cleanup resources khi app shutdown.
        """
        logger.info("🛑 Shutting down application resources...")

        # Cleanup ChromaDb nếu cần
        if self.chroma_repo:
            # ChromaDB PersistentClient tự động persist
            logger.info("📦 ChromaDB persisted to disk")
            self.chroma_repo = None

            # Cleanup models
        if self.loaded_models:
            logger.info("🧠 Unloading ML models...")
            self.loaded_models.clear()

        logger.info("✅ All resources cleaned up")

    def get_chroma_repo(self) -> ChromaRepo:
        """
        Lấy ChromaDB repository instance.

        Raises:
            RuntimeError: Nếu chưa được khởi tạo (startup chưa chạy)
        """
        if self.chroma_repo is None:
            raise RuntimeError(
                "ChromaDB not initialized. Make sure app.startup() was called."
            )
        return self.chroma_repo

    def register_index(self, index_name: str):
        """Đăng ký index mới vào active set."""
        self.active_indexes.add(index_name)
        logger.info(f"📝 Registered index: {index_name}")

    def index_exists(self, index_name: str) -> bool:
        """Kiểm tra xem index có tồn tại không."""
        return index_name in self.active_indexes

    def get_model(self, model_name: str) -> Optional[Any]:
        """Lấy ML model đã load."""
        return self.loaded_models.get(model_name)

app_state = AppState()

@asynccontextmanager
async def lifespan_manager(app):
    """
        FastAPI lifespan context manager.

        Usage trong main.py:
            app = FastAPI(lifespan=lifespan_manager)
        """
    # Startup
    await app_state.startup()

    yield  # App đang chạy

    # Shutdown
    await app_state.shutdown()