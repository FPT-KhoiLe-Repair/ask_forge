"""
LangChain-powered application state with LCEL (LangChain Expression Language)
"""
from functools import lru_cache
from typing import Optional, Dict, Any
import logging
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

from ask_forge.backend.app.core.config import settings

logger = logging.getLogger(__name__)

CORE_DIR = Path(__file__).resolve().parent  # …/backend/app/core
APP_DIR = CORE_DIR.parent  # …/backend/app
BACKEND_DIR = APP_DIR.parent  # …/backend
PROJECT_ROOT = BACKEND_DIR.parent  # …/ask_forge

class LangChainState:
    """
    Centralized LangChain components manager
    """

    _instance: Optional["LangChainState"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Core components
        self.embeddings: Optional[HuggingFaceEmbeddings] = None
        self.gemini_llm: Optional[ChatGoogleGenerativeAI] = None
        self.hf_llm: Optional[HuggingFacePipeline] = None

        # Vector stores (lazy loaded per index)
        self._vectorstores: Dict[str,Chroma] = {}

        # Chains cache
        self._qa_chains: Dict[str, ConversationalRetrievalChain] = {}

        # Memory stores (per session)
        self._memories: Dict[str, ConversationBufferWindowMemory] = {}

        self._initialized = True
        logger.info("LangChainState initialized")

    async def startup(self):
        """Initialize core LangChain components"""
        logger.info("🚀 Starting LangChain components...")

        # 1. Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={'device': 'cuda' if settings.HF_DEVICE_MAP == 'cuda' else 'cpu'},
            encode_kwargs={'normalize_embeddings': True},
        )
        logger.info("✅ Embeddings loaded: %s", settings.EMBEDDING_MODEL)

        # 2. Initialize Gemini LLM
        self.gemini_llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL_NAME,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.7,
            convert_system_message_to_human=True
        )
        logger.info("✅ Gemini LLM initialized: %s", settings.GEMINI_MODEL_NAME)

        # 3. Preload HF model if needed
        if settings.HF_PRELOAD_AT_STARTUP:
            await self._load_hf_pipeline()

    async def _load_hf_pipeline(self):
        """Lazy load HuggingFace pipeline"""
        # TODO: Check đường dẫn tới model
        if self.hf_llm is not None:
            return

        logger.info("🧠 Loading HuggingFace pipeline...")
        from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
        import torch

        model_path = settings.HF_QUESTION_GENERATOR_CKPT
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            dtye=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            device_map = settings.HF_DEVICE_MAP,
        )

        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=512,
            repetition_penalty=1.1,
        )

        self.hf_llm = HuggingFacePipeline(pipeline=pipe)
        logger.info("✅ HuggingFace pipeline ready")

    def get_vectorstore(self, index_name:str) -> Chroma:
        """Get or create Chroma vectorstore for an index"""
        if index_name not in self._vectorstores:
            self._vectorstores[index_name] = Chroma(
                collection_name=index_name,
                embedding_function=self.embeddings,
                persist_directory=settings.CHROMA_PERSIST_DIR,
            )
            logger.info("📦 Vectorstore loaded: %s", index_name)
        return self._vectorstores[index_name]

    def get_memory(self, session_id:str, k: int = 6) -> ConversationalRetrievalChain:
        """Get or create conversation memory for a session"""
        if session_id not in self._memories:
            self._memories[session_id] = ConversationBufferWindowMemory(
                k=k,
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"
            )
        return self._memories[session_id]

    def build_rag_chain(
            self,
            index_name: str,
            session_id: str,
            prompt_template: str = "default",
    ):
        """
        Build LCEL chain: retriever -> prompt -> LLM -> parser
        """
        # 1. Retriever
        vectorstore = self.get_vectorstore(index_name)
        retriever = vectorstore.as_retriever(
            search_kwargs={"k":5}
        )

        # 2. Prompt template (tùy chỉnh theo role)
        if prompt_template == "tutor":
            system_msg = "You are a patient tutor. Explain step-by-step."
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_msg),
                MessagesPlaceholder("chat_history"),  # Memory injection
                ("human", "{question}"),
                ("system", "Context:\n{context}")
            ])
        elif prompt_template == "qg":
            system_msg = "" # TODO: Xem xét lại cách thiết lập prompt chuyên cho QG
        else:
            system_msg = "You are a helpful educational assistant." # TODO: Khúc này bạn có thể suy nghĩ phát triển hệ thống theo system_msg theo role nè
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_msg),
                MessagesPlaceholder("chat_history"),  # Memory injection
                ("human", "{question}"),
                ("system", "Context:\n{context}")
            ])

        # 3. Memory
        memory = self.get_memory(session_id, k=6)

        # 4. Chain assembly (LCEL)
        chain = (
                RunnableParallel({
                    "context": retriever,
                    "question": RunnablePassthrough(),
                    "chat_history": lambda _: memory.load_memory_variables({})["chat_history"]
                })
                | prompt
                | self.gemini_llm
                | StrOutputParser()
        )

        return chain, memory