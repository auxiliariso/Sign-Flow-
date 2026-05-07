"""
database/repositories/signature_repository.py
"""
from typing import Optional


class SQLiteSignatureRepository:

    def __init__(self, db):
        self._db = db

    def save(self, record) -> object:
        """Acepta tanto entidad SignatureRecord como dict."""
        if isinstance(record, dict):
            return self._save_dict(record)
        return self._save_entity(record)

    def _save_dict(self, d: dict) -> dict:
        cols = [
            "id_document", "id_user", "nombre_completo", "nombre_puesto",
            "firma_hash", "hash_previo", "documento_hash", "documento_hash_post",
            "validation_id", "fecha", "hora", "timestamp_utc", "qr_data",
        ]
        vals = [d.get(c) for c in cols]
        with self._db.get_conn() as conn:
            cur = conn.execute(
                f"INSERT INTO signatures ({', '.join(cols)}) "
                f"VALUES ({', '.join(['?']*len(cols))})",
                vals,
            )
            d["id_firma"] = cur.lastrowid
            return d

    def _save_entity(self, record) -> object:
        with self._db.get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO signatures "
                "(id_user, nombre_completo, nombre_puesto, firma_hash, "
                " fecha, hora) VALUES (?, ?, ?, ?, ?, ?)",
                (record.id_user, record.nombre_completo, record.nombre_puesto,
                 record.firma_hash, record.fecha, record.hora),
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
            return conn.execute("SELECT COUNT(*) FROM signatures").fetchone()[0]
