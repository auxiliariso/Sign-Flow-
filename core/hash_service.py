"""
core/hash_service.py
====================
Servicio de hashing encadenado.

Cada firma nueva incluye en su hash:
  - hash actual del documento en disco
  - id del usuario
  - timestamp UTC
  - hash de la firma previa (o '0' si es la primera)

Esto crea una cadena criptográfica: si alguien modifica el documento
o cualquier firma anterior, la verificación lo detecta.
"""
import hashlib
import hmac
import os
from datetime import datetime, timezone
from pathlib import Path


class HashService:

    @staticmethod
    def file_hash(filepath: str) -> str:
        """SHA-256 del contenido binario del archivo."""
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def signature_hash(
        documento_hash: str,
        id_user: int,
        timestamp_utc: str,
        hash_previo: str,
        nonce: str | None = None,
    ) -> str:
        """
        Hash encadenado de la firma.
        nuevo_hash = SHA256(doc_hash | id_user | timestamp | hash_previo | nonce)
        """
        if nonce is None:
            nonce = os.urandom(16).hex()
        raw = "|".join([
            documento_hash,
            str(id_user),
            timestamp_utc,
            hash_previo,
            nonce,
        ])
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def short_hash(full_hash: str, chars: int = 8) -> str:
        """Primeros y últimos N chars para mostrar visualmente."""
        if len(full_hash) <= chars * 2:
            return full_hash
        return f"{full_hash[:chars]}…{full_hash[-chars:]}"

    @staticmethod
    def now_utc() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def generate_validation_id(index: int, year: int | None = None) -> str:
        """Genera ID legible tipo SF-2026-000182."""
        if year is None:
            year = datetime.now().year
        return f"SF-{year}-{index:06d}"

    @staticmethod
    def verify_chain(signatures: list[dict]) -> tuple[bool, str]:
        """
        Verifica que la cadena de firmas sea íntegra.
        signatures: lista de dicts con keys:
          firma_hash, documento_hash, id_user, timestamp_utc, hash_previo
        Devuelve (valid: bool, message: str)
        """
        if not signatures:
            return True, "Sin firmas registradas."

        prev_hash = "0"
        for i, sig in enumerate(signatures):
            expected_prev = sig.get("hash_previo", "0")
            if expected_prev != prev_hash:
                return False, (
                    f"⚠ Cadena rota en firma #{i+1}: "
                    f"hash_previo esperado '{prev_hash[:16]}…' "
                    f"pero encontrado '{expected_prev[:16]}…'"
                )
            prev_hash = sig["firma_hash"]

        return True, f"✓ Cadena de {len(signatures)} firma(s) íntegra."