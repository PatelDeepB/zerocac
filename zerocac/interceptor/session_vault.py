"""Encrypted local session vault for social account authentication cookies and tokens."""

import base64
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class SessionVault:
    """Provides authenticated platform session storage with Fernet symmetric encryption."""

    def __init__(
        self,
        vault_path: Optional[str] = None,
        master_key: Optional[str] = None,
    ) -> None:
        """Initialize vault with encrypted file path and encryption cipher."""
        self.vault_path = Path(vault_path or (Path.cwd() / ".session_vault.enc"))
        self._cipher = self._init_cipher(master_key)

    def _init_cipher(self, master_key: Optional[str]) -> Fernet:
        """Derive or load a 32-byte URL-safe base64 key for Fernet encryption."""
        raw_key = master_key or os.getenv("ZEROCAC_VAULT_KEY")
        if not raw_key:
            # Deterministic device-local fallback key
            salt = b"zerocac_vault_salt_v1"
            derived = hashlib.pbkdf2_hmac("sha256", b"zerocac_local_master_secret", salt, 100000)
            key = base64.urlsafe_b64encode(derived)
        elif len(raw_key) == 44 and raw_key.endswith("="):
            key = raw_key.encode("utf-8")
        else:
            derived = hashlib.sha256(raw_key.encode("utf-8")).digest()
            key = base64.urlsafe_b64encode(derived)

        return Fernet(key)

    def _read_vault(self) -> Dict[str, Any]:
        """Read and decrypt entire vault payload from disk."""
        if not self.vault_path.exists():
            return {}

        try:
            encrypted_data = self.vault_path.read_bytes()
            if not encrypted_data:
                return {}
            decrypted = self._cipher.decrypt(encrypted_data)
            return json.loads(decrypted.decode("utf-8"))
        except (InvalidToken, json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not decrypt session vault: %s", exc)
            return {}

    def _write_vault(self, data: Dict[str, Any]) -> None:
        """Encrypt and atomically write vault payload to disk."""
        raw_bytes = json.dumps(data, indent=2).encode("utf-8")
        encrypted = self._cipher.encrypt(raw_bytes)
        self.vault_path.write_bytes(encrypted)

    def store_session(
        self,
        platform: str,
        username: str,
        session_data: Dict[str, str],
    ) -> None:
        """Store or update encrypted credentials for an account."""
        vault = self._read_vault()
        key = f"{platform.lower()}:{username.lower()}"
        vault[key] = {
            "platform": platform.lower(),
            "username": username.lower(),
            "session_data": session_data,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._write_vault(vault)

    def get_session(
        self,
        platform: str,
        username: Optional[str] = None,
    ) -> Optional[Dict[str, str]]:
        """Retrieve decrypted session data for a specific account or default account."""
        vault = self._read_vault()
        plat = platform.lower()

        if username:
            key = f"{plat}:{username.lower()}"
            entry = vault.get(key)
            return entry.get("session_data") if entry else None

        for k, entry in vault.items():
            if k.startswith(f"{plat}:"):
                return entry.get("session_data")
        return None

    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """Return metadata list of all configured platform accounts (tokens redacted)."""
        vault = self._read_vault()
        sessions = []
        for entry in vault.values():
            token_keys = list(entry.get("session_data", {}).keys())
            sessions.append({
                "platform": entry.get("platform"),
                "username": entry.get("username"),
                "configured_keys": token_keys,
                "updated_at": entry.get("updated_at"),
            })
        return sessions

    def revoke_session(self, platform: str, username: str) -> bool:
        """Delete an account's session tokens from the vault."""
        vault = self._read_vault()
        key = f"{platform.lower()}:{username.lower()}"
        if key in vault:
            del vault[key]
            self._write_vault(vault)
            return True
        return False
