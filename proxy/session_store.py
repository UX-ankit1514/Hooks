"""Lightweight per-session state, kept in memory and mirrored to a JSON file.

Prompts are never stored, only a short fingerprint (sha256 prefix).

Per session:
    session_id, cwd, source, start_model, last_seen_model,
    turn: prompt_id, prompt_fingerprint, recommendation_id, recommended_model,
          model_id, provider, recommendation_reason, confidence, routable,
          accepted (true/false/null), decided_by, timestamp
    active_route: model id applied to this human turn (null = keep original)
    route_status: none | applied | failed
"""

import json
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

MAX_SESSIONS = 200
MAX_AGE_SECONDS = 7 * 24 * 3600


def _now() -> float:
    return round(time.time(), 3)


class SessionStore:
    def __init__(self, path: Optional[Path] = None):
        self.path = path
        self._lock = threading.Lock()
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._load()

    # -- persistence -------------------------------------------------------

    def _load(self) -> None:
        if not self.path or not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            sessions = data.get("sessions", {})
            if isinstance(sessions, dict):
                self._sessions = {k: v for k, v in sessions.items() if isinstance(v, dict)}
        except (OSError, ValueError):
            self._sessions = {}  # a corrupt state file must never stop the proxy

    def _save(self) -> None:
        if not self.path:
            return
        self._prune()
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps({"sessions": self._sessions}, indent=2), encoding="utf-8")
            os.replace(str(tmp), str(self.path))
        except OSError:
            pass  # state is best-effort; in-memory copy stays authoritative

    def _prune(self) -> None:
        cutoff = time.time() - MAX_AGE_SECONDS
        items = [(sid, s) for sid, s in self._sessions.items() if s.get("updated_at", 0) >= cutoff]
        items.sort(key=lambda kv: kv[1].get("updated_at", 0), reverse=True)
        self._sessions = dict(items[:MAX_SESSIONS])

    def _session(self, session_id: str) -> Dict[str, Any]:
        session = self._sessions.get(session_id)
        if session is None:
            session = {
                "session_id": session_id,
                "cwd": None,
                "source": None,
                "start_model": None,
                "last_seen_model": None,
                "created_at": _now(),
                "updated_at": _now(),
                "turn": None,
                "active_route": None,
                "route_status": "none",
            }
            self._sessions[session_id] = session
        session["updated_at"] = _now()
        return session

    # -- operations ----------------------------------------------------------

    def start_session(self, session_id: str, cwd: Optional[str] = None, source: Optional[str] = None,
                      model: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            session = self._session(session_id)
            session["cwd"] = cwd or session.get("cwd")
            session["source"] = source
            if model:
                session["start_model"] = model
            # A new/resumed/cleared session starts on its original model.
            session["active_route"] = None
            session["route_status"] = "none"
            self._save()
            return dict(session)

    def new_turn(self, session_id: str, prompt_id: Optional[str], fingerprint: str) -> None:
        """A new human prompt arrived: forget the previous turn's route."""
        with self._lock:
            session = self._session(session_id)
            session["turn"] = {
                "prompt_id": prompt_id,
                "prompt_fingerprint": fingerprint,
                "recommendation_id": None,
                "accepted": None,
                "timestamp": _now(),
            }
            session["active_route"] = None
            session["route_status"] = "none"
            self._save()

    def set_recommendation(self, session_id: str, recommendation: Dict[str, Any]) -> str:
        with self._lock:
            session = self._session(session_id)
            turn = session.get("turn") or {"timestamp": _now()}
            recommendation_id = uuid.uuid4().hex[:12]
            turn.update(recommendation)
            turn["recommendation_id"] = recommendation_id
            turn["accepted"] = None
            session["turn"] = turn
            self._save()
            return recommendation_id

    def set_selection(self, session_id: str, recommendation_id: str, accepted: bool,
                      decided_by: str) -> Dict[str, Any]:
        with self._lock:
            session = self._sessions.get(session_id)
            turn = (session or {}).get("turn") or {}
            if not session or turn.get("recommendation_id") != recommendation_id:
                return {"ok": False, "applied": False, "error": "stale or unknown recommendation"}
            turn["accepted"] = bool(accepted)
            turn["decided_by"] = decided_by
            turn["decided_at"] = _now()
            applied = bool(accepted) and bool(turn.get("routable")) and bool(turn.get("model_id"))
            session["active_route"] = turn.get("model_id") if applied else None
            session["route_status"] = "applied" if applied else "none"
            session["updated_at"] = _now()
            self._save()
            return {"ok": True, "applied": applied, "active_model": session["active_route"]}

    def active_route(self, session_id: str) -> Optional[str]:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session or session.get("route_status") != "applied":
                return None
            return session.get("active_route")

    def mark_route_failed(self, session_id: str, reason: str) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session["route_status"] = "failed"
                session["route_error"] = reason[:200]
                session["updated_at"] = _now()
                self._save()

    def note_seen_model(self, session_id: str, model: str) -> None:
        with self._lock:
            session = self._session(session_id)
            if session.get("last_seen_model") != model:
                session["last_seen_model"] = model
                self._save()

    def current_model(self, session_id: str) -> Optional[str]:
        with self._lock:
            session = self._sessions.get(session_id) or {}
            return session.get("last_seen_model") or session.get("start_model")

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            session = self._sessions.get(session_id)
            return json.loads(json.dumps(session)) if session else None

    def count(self) -> int:
        with self._lock:
            return len(self._sessions)
