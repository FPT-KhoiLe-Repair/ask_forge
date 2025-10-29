🧠 Giới thiệu dự án

AskForge Backend là hệ thống lõi cho nền tảng học tập AI hỗ trợ tạo câu hỏi thông minh (Question Generation) và truy xuất tri thức (Retrieval-Augmented Generation – RAG) từ tài liệu PDF.
Mục tiêu là xây dựng một backend modular, mở rộng linh hoạt, dễ tích hợp với frontend (Next.js) và các mô hình AI (Gemini, Qwen, v.v.).

## 🧩 Backend

```
backend/
├── app/
│   ├── main.py                  # Entry FastAPI app
│   ├── core/
│   │   ├── config.py            # Pydantic Settings (.env loader)
│   │   ├── state.py             # Singleton AppState quản lý resources
│   │   └── logger.py            # Logging setup (optional)
│   │
│   ├── repositories/
│   │   ├── vectorstore.py       # ChromaDB repo, CRUD cho index
│   │   └── loader.py            # PDF loader và chunker
│   │
│   ├── routes/
│   │   ├── chat.py              # /api/chat + /api/chat/stream
│   │   ├── index.py             # /api/build_index, /api/add_to_index
│   │   └── health.py            # /api/health
│   │
│   ├── schemas/
│   │   ├── chat_schema.py       # Pydantic models cho ChatBody, ChatResponse
│   │   └── index_schema.py      # Schema cho build/add index
│   │
│   ├── services/
│   │   ├── rag_service.py       # Logic truy xuất context + sinh câu trả lời
│   │   ├── qg_service.py        # Question Generation module (tùy chọn)
│   │   └── model_loader.py      # Load HuggingFace / Gemini model
│   │
│   ├── utils/
│   │   ├── file_utils.py        # Xử lý file, temp dir, save binary
│   │   ├── text_utils.py        # Split text, preprocess, v.v.
│   │   └── json_utils.py        # Atomic JSON append/read/write
│   │
│   └── __init__.py
│
├── tests/                       # Unit tests cho từng module
│
├── data/
│   ├── user_db/                 # Chứa metadata JSON pages
│   └── .chroma/                 # Persistent Chroma storage
│
├── .env                         # Environment variables (GEMINI_API_KEY, ...)
├── requirements.txt             # Dependencies
├── README.md                    # (Đang viết)
└── run.sh / start.py            # Script khởi động server
