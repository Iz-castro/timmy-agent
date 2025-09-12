# core/persistence.py
# -*- coding: utf-8 -*-
"""
Sistema de persistência multi-tenant
Genérico e extensível
"""
from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

class PersistenceManager:
    """
    Multi-tenant file persistence.

    Estrutura por tenant:
    data/
      tenants/
        <tenant_id>/
          conversations/
            <session>.csv                # canonical
            <slug>__<session>.csv       # alias amigável (se houver nome)
          sessions/
            <session>.json               # estado + metadados (inclui display_name/phone)
          users/
            <slug-ou-user_id>.json      # perfil do cliente
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.root = Path("data") / "tenants" / tenant_id
        self.conv_dir = self.root / "conversations"
        self.sess_dir = self.root / "sessions"
        self.users_dir = self.root / "users"
        for d in (self.conv_dir, self.sess_dir, self.users_dir):
            d.mkdir(parents=True, exist_ok=True)

    # ---- Propriedade usada nos testes
    @property
    def data_path(self) -> Path:
        return self.root

    # ---------------- Utils ----------------
    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    @staticmethod
    def _slugify(text: str) -> str:
        if not text:
            return ""
        text = text.strip().lower()
        text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
        text = re.sub(r"[\s_-]+", "-", text)
        return text.strip("-")[:60]  # limite de segurança

    def _session_meta_path(self, session_key: str) -> Path:
        return self.sess_dir / f"{session_key}.json"

    def _canonical_conv_path(self, session_key: str) -> Path:
        return self.conv_dir / f"{session_key}.csv"

    def _friendly_conv_path(self, session_key: str, display_name: Optional[str]) -> Optional[Path]:
        if not display_name:
            return None
        slug = self._slugify(display_name)
        if not slug:
            return None
        return self.conv_dir / f"{slug}__{session_key}.csv"

    def _load_session_meta(self, session_key: str) -> Dict[str, Any]:
        p = self._session_meta_path(session_key)
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_session_meta(self, session_key: str, meta: Dict[str, Any]) -> None:
        p = self._session_meta_path(session_key)
        p.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---------------- Conversas ----------------
    def save_message(self, session_key: str, role: str, content: str, **kwargs) -> None:
        """
        Append no CSV da conversa. Usa alias amigável se houver display_name definido;
        caso contrário usa o arquivo canônico <session>.csv.

        **kwargs absorve parâmetros extras (ex.: metadata) vindos do chamador.
        """
        meta = self._load_session_meta(session_key)
        display_name = meta.get("display_name")
        friendly = self._friendly_conv_path(session_key, display_name)
        path = friendly if friendly else self._canonical_conv_path(session_key)

        is_new = not path.exists()
        with path.open("a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if is_new:
                w.writerow(["timestamp", "role", "content"])
            w.writerow([self._now(), role, content])

    def get_conversation_history(self, session_key: str, limit: Optional[int] = None) -> List[Dict[str, str]]:
        meta = self._load_session_meta(session_key)
        display_name = meta.get("display_name")
        # tenta alias primeiro; se não existir, cai no canônico
        candidates = []
        friendly = self._friendly_conv_path(session_key, display_name)
        if friendly and friendly.exists():
            candidates.append(friendly)
        canonical = self._canonical_conv_path(session_key)
        if canonical.exists():
            candidates.append(canonical)

        if not candidates:
            return []

        path = candidates[0]
        out: List[Dict[str, str]] = []
        with path.open("r", newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                out.append({"timestamp": row["timestamp"], "role": row["role"], "content": row["content"]})
        return out[-limit:] if (limit and limit > 0) else out

    # ---------------- Session State ----------------
    def update_session_state(self, session_key: str, updates: Dict[str, Any]) -> None:
        path = self._session_meta_path(session_key)
        state = {}
        if path.exists():
            try:
                state = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                state = {}
        state.setdefault("session_key", session_key)
        state.setdefault("created_at", self._now())
        state.setdefault("state", {})
        state["state"].update(updates)
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_session_state(self, session_key: str) -> Dict[str, Any]:
        path = self._session_meta_path(session_key)
        if not path.exists():
            return {}
        try:
            meta = json.loads(path.read_text(encoding="utf-8"))
            return meta.get("state", {})
        except Exception:
            return {}

    # ---------------- User Profile ----------------
    def upsert_user_profile(self, user_id: str, updates: Dict[str, Any]) -> Path:
        """
        Salva / mescla perfil. Usa slug do nome (se houver) como nome de arquivo;
        caso contrário, usa o próprio user_id.
        """
        name = updates.get("name")
        base = self._slugify(name) if name else user_id
        p = self.users_dir / f"{base}.json"

        data = {}
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                data = {}

        # merge superficial
        for k, v in updates.items():
            if isinstance(v, dict) and isinstance(data.get(k), dict):
                data[k].update(v)
            else:
                data[k] = v

        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return p

    def get_user_profile(self, user_id_or_slug: str) -> Dict[str, Any]:
        # tenta slug.json; se não, tenta id.json
        p1 = self.users_dir / f"{user_id_or_slug}.json"
        if p1.exists():
            try:
                return json.loads(p1.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    # ---------------- Identidade & Arquivo amigável ----------------
    def register_identity(self, session_key: str, name: Optional[str] = None, phone: Optional[str] = None) -> Dict[str, Any]:
        """
        Declara identidade da sessão:
        - salva em sessions/<session>.json  -> display_name / phone
        - renomeia (na prática: passa a escrever em) conversations/<slug>__<session>.csv
          (mantém o canônico <session>.csv intocado; você pode deletá-lo depois se quiser)
        - cria/merge users/<slug>.json

        Retorna metadados atualizados da sessão.
        """
        meta = self._load_session_meta(session_key)
        state = meta.get("state", {})

        display_name = name or state.get("client_name")
        if display_name:
            meta["display_name"] = display_name
            # cria/merge perfil
            self.upsert_user_profile(user_id=self._slugify(display_name) or display_name, updates={
                "name": display_name,
                **({"phone": phone} if phone else {})
            })
        if phone:
            meta["phone"] = phone

        # aponta o arquivo amigável (se houver nome)
        friendly = self._friendly_conv_path(session_key, meta.get("display_name"))
        if friendly:
            meta["conversation_file"] = str(friendly)

        # salva meta de sessão
        self._save_session_meta(session_key, meta)
        return meta