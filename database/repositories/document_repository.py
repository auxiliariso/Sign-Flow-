"""
database/repositories/document_repository.py
"""
from datetime import datetime
from pathlib import Path
from typing import Optional


class SQLiteDocumentRepository:

    def __init__(self, db):
        self._db = db

    def get_or_create(self, filepath: str, created_by: int) -> dict:
        with self._db.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE filepath = ?", (filepath,)
            ).fetchone()
            if row:
                return dict(row)

            p    = Path(filepath)
            tipo = p.suffix.lstrip(".").lower()
            cur  = conn.execute(
                "INSERT INTO documents "
                "(filepath, nombre, tipo, hash_original, hash_actual, "
                " version_actual, created_at, created_by) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (filepath, p.name, tipo, None, None, 0,
                 datetime.now().isoformat(), created_by),
            )
            return {
                "id_document": cur.lastrowid,
                "filepath": filepath,
                "nombre": p.name,
                "tipo": tipo,
                "hash_original": None,
                "hash_actual": None,
                "version_actual": 0,
            }

    def update_hash(self, id_document: int, hash_actual: str, version: int):
        with self._db.get_conn() as conn:
            conn.execute(
                "UPDATE documents SET hash_actual=?, version_actual=? "
                "WHERE id_document=?",
                (hash_actual, version, id_document),
            )

    def get_by_id(self, id_document: int) -> Optional[dict]:
        with self._db.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE id_document = ?", (id_document,)
            ).fetchone()
            return dict(row) if row else None

    def get_by_path(self, filepath: str) -> Optional[dict]:
        with self._db.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE filepath = ?", (filepath,)
            ).fetchone()
            return dict(row) if row else None

    def list_all(self) -> list:
        with self._db.get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM documents ORDER BY id_document DESC"
            ).fetchall()
            return [dict(r) for r in rows]
