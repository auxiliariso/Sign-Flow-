"""
database/repositories/signature_repository.py  (v2.4)
Fix: documento_path y tipo_documento ahora se incluyen en el INSERT.
"""
from typing import Optional


class SQLiteSignatureRepository:

    def __init__(self, db):
        self._db = db

    def save(self, record) -> object:
        if isinstance(record, dict):
            return self._save_dict(record)
        return self._save_entity(record)

    def _save_dict(self, d: dict) -> dict:
        # Todas las columnas posibles — None si no vienen en el dict
        cols = [
            "id_document",
            "id_user",
            "nombre_completo",
            "nombre_puesto",
            "firma_hash",
            "hash_previo",
            "documento_hash",
            "documento_hash_post",
            "validation_id",
            "fecha",
            "hora",
            "timestamp_utc",
            "qr_data",
            "documento_path",      # ← antes faltaba
            "tipo_documento",      # ← antes faltaba
        ]
        vals = [d.get(c) for c in cols]
        ph   = ", ".join(["?"] * len(cols))

        with self._db.get_conn() as conn:
            cur = conn.execute(
                f"INSERT INTO signatures ({', '.join(cols)}) VALUES ({ph})",
                vals,
            )
            d["id_firma"] = cur.lastrowid
            return d

    def _save_entity(self, record) -> object:
        """Compatibilidad con entidad SignatureRecord (tests)."""
        with self._db.get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO signatures "
                "(id_user, nombre_completo, nombre_puesto, firma_hash, "
                " fecha, hora, documento_path, tipo_documento) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record.id_user,
                    record.nombre_completo,
                    record.nombre_puesto,
                    record.firma_hash,
                    record.fecha,
                    record.hora,
                    getattr(record, "documento_path", None),
                    getattr(record, "tipo_documento", None),
                ),
            )
            record.id_firma = cur.lastrowid
            return record

    def get_by_user(self, id_user: int) -> list:
        with self._db.get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM signatures WHERE id_user = ? ORDER BY id_firma",
                (id_user,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_by_document(self, id_document: int) -> list:
        with self._db.get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM signatures WHERE id_document = ? ORDER BY id_firma",
                (id_document,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_all(self) -> list:
        with self._db.get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM signatures ORDER BY id_firma DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def get_by_hash(self, firma_hash: str) -> Optional[dict]:
        with self._db.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM signatures WHERE firma_hash = ?", (firma_hash,)
            ).fetchone()
            return dict(row) if row else None

    def count(self) -> int:
        with self._db.get_conn() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM signatures"
            ).fetchone()[0]