# app/services/ai_assistant_service/session_manager.py
"""
Quản lý in-memory session store cho AI Assistant conversations.
"""
import time
import logging

logger = logging.getLogger(__name__)

# In-memory session store: session_id -> list of messages
_SESSIONS: dict[str, list] = {}
_SESSION_TIMESTAMPS: dict[str, float] = {}
_SESSION_TTL = 3600  # 1 hour


def clean_expired_sessions() -> None:
    """Xóa các session đã hết TTL."""
    now = time.time()
    expired = [k for k, t in _SESSION_TIMESTAMPS.items() if now - t > _SESSION_TTL]
    for k in expired:
        _SESSIONS.pop(k, None)
        _SESSION_TIMESTAMPS.pop(k, None)
    if expired:
        logger.debug(f"[SessionManager] Cleaned {len(expired)} expired sessions")


def get_or_create_session(session_id: str, conversation_history: list = None) -> list:
    """Lấy hoặc tạo mới session. Nếu có conversation_history thì restore từ đó."""
    now = time.time()
    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = []
        if conversation_history:
            for msg in conversation_history:
                _SESSIONS[session_id].append({
                    "role": msg.role,
                    "content": msg.content
                })
            logger.info(f"[SessionManager] Restored {len(conversation_history)} messages for session {session_id}")
    _SESSION_TIMESTAMPS[session_id] = now
    return _SESSIONS[session_id]


def save_to_session(session_id: str, user_message: str, assistant_reply: str) -> None:
    """Lưu cặp user/assistant message vào session, giữ tối đa 50 messages."""
    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = []
    history = _SESSIONS[session_id]
    history.append({"role": "user", "content": user_message})
    history.append({"role": "model", "content": assistant_reply})
    if len(history) > 50:
        _SESSIONS[session_id] = history[-50:]


def clear_session(session_id: str) -> None:
    """Xóa lịch sử hội thoại của một session."""
    _SESSIONS.pop(session_id, None)
    _SESSION_TIMESTAMPS.pop(session_id, None)
