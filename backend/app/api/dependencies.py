from ask_forge.backend.app.core.config import settings
from ask_forge.backend.app.repositories.vectorstore import ChromaRepo

def get_settings():
    return settings

def get_vector_repo():
    return ChromaRepo()

