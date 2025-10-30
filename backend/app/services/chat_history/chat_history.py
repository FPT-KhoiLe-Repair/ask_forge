from __future__ import annotations
from typing import Dict, Optional, List
from collections import defaultdict, deque
from threading import RLock

from ask_forge.backend.app.services.chat.schemas import ChatSession, ChatTurn

class HistoryRepo:
    """Interface"""
    def get_or_create(self,
                      session_id: str,
                      user_id: Optional[str] = None)->ChatSession: ...

    def append(self,
               session_id: str,
               turn: ChatTurn,) -> None:...

    def get(self,
            session_id: str,) -> Optional[ChatSession]: ...

    def set_summary(self,
                    session_id: str,
                    summary: str,) -> None: ...

    def clear(self,
              session_id: str) -> None: ...


class InMemoryHistoryRepo(HistoryRepo):
    def __init__(self, default_last_k: int = 6, max_turns_per_session: int = 500) -> None:
        self._session: Dict[int, ChatSession] = {}
        self._lock = RLock()
        self._default_last_k = default_last_k
        self._max_turns_per_session = max_turns_per_session

    def get_or_create(self,
                      session_id: str,
                      user_id: Optional[str] = None)->ChatSession:
        with self._lock:
            sess = self._session.get(session_id)
            if not sess:
                sess = ChatSession(session_id=session_id, user_id=user_id, last_k=self._max_turns_per_session)
                self._session[session_id] = sess
            return sess

    def append(self,
               session_id: str,
               chat_turn: ChatTurn, ) -> None:
        with self._lock:
            sess = self.get_or_create(session_id)
            sess.chat_turn.append(chat_turn)

            # Chỉ lấy k turns đổ lại
            if len(sess.chat_turn) > self._max_turns_per_session:
                sess.chat_turn = sess.chat_turn[-sess.last_k:]

    def get(self,
            session_id: str,) -> Optional[ChatSession]:
        with self._lock:
            return self._session.get(session_id)

    def set_summary(self,
                    session_id: str,
                    summary: str,) -> None:
        with self._lock:
            sess = self.get_or_create(session_id)
            sess.rolling_summary = summary

    def clear(self,
              session_id: str) -> None:
        with self._lock:
            if session_id in self._session:
                del self._session[session_id]

# TODO: để mà bền vững, thay thế InMemoryHistoryRepo bằng RedisHistoryRepo hoặc SQLiteHistoryRepo (SQL Model), giữ nguyên interface
