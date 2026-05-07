"""
core/hash_service.py  (v2.1)
============================
- now_local()  → hora LOCAL del sistema (visible al usuario)
- now_utc()    → UTC para metadata/cadena criptográfica
- short_hash() → "a4b7…cda1"  (4+4 chars, muy compacto para la firma visual)
- medium_hash()→ "a4b7d5f9…fa281cda" (8+8, para historial/registros)
"""
import hashlib
import os
from datetime import datetime, timezone


class HashService:

    @staticmethod
    def now_utc() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def now_local() -> str:
        """Hora LOCAL del sistema — la que el usuario ve en su reloj."""
        return datetime.now().isoformat()

    @staticmethod
    def local_date_time() -> tuple[str, str]:
        """Devuelve (fecha, hora) en hora local. Ej: ('2026-05-07', '14:32:11')"""
        now = datetime.now()
        return now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")

    @staticmethod
    def file_hash(filepath: str) -> str:
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def signature_hash(documento_hash, id_user, timestamp_utc, hash_previo, nonce=None):
        if nonce is None:
            nonce = os.urandom(16).hex()
        raw = "|".join([documento_hash, str(id_user), timestamp_utc, hash_previo, nonce])
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def short_hash(full_hash: str, chars: int = 4) -> str:
        """Compacto: 'a4b7…cda1' (4+4 chars). Para la firma VISIBLE."""
        if len(full_hash) <= chars * 2:
            return full_hash
        return f"{full_hash[:chars]}…{full_hash[-chars:]}"

    @staticmethod
    def medium_hash(full_hash: str) -> str:
        """'a4b7d5f9…fa281cda' (8+8). Para historial y registros."""
        if len(full_hash) <= 20:
            return full_hash
        return f"{full_hash[:8]}…{full_hash[-8:]}"

    @staticmethod
    def generate_validation_id(index: int, year: int = None) -> str:
        if year is None:
            year = datetime.now().year
        return f"SF-{year}-{index:06d}"

    @staticmethod
    def verify_chain(signatures: list) -> tuple[bool, str]:
        if not signatures:
            return True, "Sin firmas registradas."
        prev_hash = "0"
        for i, sig in enumerate(signatures):
            expected = sig.get("hash_previo", "0")
            if expected != prev_hash:
                return False, f"⚠ Cadena rota en firma #{i+1}."
            prev_hash = sig["firma_hash"]
        return True, f"✓ Cadena de {len(signatures)} firma(s) íntegra."
