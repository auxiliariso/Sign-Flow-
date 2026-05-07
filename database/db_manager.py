"""
database/db_manager.py  (v2.2)
==============================
- Migración automática: detecta BD vieja y agrega columnas faltantes
- close_all() para Windows
"""
import sqlite3
from pathlib import Path
from datetime import datetime


DDL = """
CREATE TABLE IF NOT EXISTS users (
    id_user          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_completo  TEXT    NOT NULL UNIQUE,
    nombre_puesto    TEXT    NOT NULL,
    password_hash    TEXT    NOT NULL,
    activo           INTEGER NOT NULL DEFAULT 1,
    created_at       TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id_document    INTEGER PRIMARY KEY AUTOINCREMENT,
    filepath       TEXT    NOT NULL UNIQUE,
    nombre         TEXT    NOT NULL,
    tipo           TEXT    NOT NULL,
    hash_original  TEXT,
    hash_actual    TEXT,
    version_actual INTEGER NOT NULL DEFAULT 0,
    created_at     TEXT    NOT NULL,
    created_by     INTEGER
);

CREATE TABLE IF NOT EXISTS signatures (
    id_firma             INTEGER PRIMARY KEY AUTOINCREMENT,
    id_document          INTEGER,
    id_user              INTEGER NOT NULL,
    nombre_completo      TEXT    NOT NULL,
    nombre_puesto        TEXT    NOT NULL,
    firma_hash           TEXT    NOT NULL UNIQUE,
    hash_previo          TEXT    NOT NULL DEFAULT '0',
    documento_hash       TEXT,
    documento_hash_post  TEXT,
    validation_id        TEXT,
    fecha                TEXT    NOT NULL,
    hora                 TEXT    NOT NULL,
    timestamp_utc        TEXT,
    qr_data              TEXT,
    documento_path       TEXT,
    tipo_documento       TEXT
);

CREATE INDEX IF NOT EXISTS idx_sig_doc  ON signatures(id_document);
CREATE INDEX IF NOT EXISTS idx_sig_user ON signatures(id_user);
CREATE INDEX IF NOT EXISTS idx_sig_hash ON signatures(firma_hash);
"""

# Columnas que pueden faltar en BDs antiguas → se agregan automáticamente
MIGRATIONS = {
    "signatures": [
        "id_document         INTEGER",
        "hash_previo         TEXT    NOT NULL DEFAULT '0'",
        "documento_hash      TEXT",
        "documento_hash_post TEXT",
        "validation_id       TEXT",
        "timestamp_utc       TEXT",
        "qr_data             TEXT",
        "documento_path      TEXT",
        "tipo_documento      TEXT",
    ],
    "users": [
        "activo     INTEGER NOT NULL DEFAULT 1",
        "created_at TEXT    NOT NULL DEFAULT ''",
    ],
}


class DatabaseManager:

    def __init__(self, db_path: str = "signflow.db"):
        self.db_path = db_path
        self._conn = None

        self.user_repo = None
        self.sig_repo  = None
        self.doc_repo  = None

    def initialize(self):
        with self._connect() as conn:
            conn.executescript(DDL)
        self._migrate()
        self._bind_repos()

    def _migrate(self):
        """Agrega columnas faltantes sin tocar datos existentes."""
        with self._connect() as conn:
            for table, columns in MIGRATIONS.items():
                existing = self._existing_columns(conn, table)
                for col_def in columns:
                    col_name = col_def.split()[0]
                    if col_name not in existing:
                        try:
                            conn.execute(
                                f"ALTER TABLE {table} ADD COLUMN {col_def}"
                            )
                        except sqlite3.OperationalError:
                            pass   # ya existe o tabla no existe aún

    @staticmethod
    def _existing_columns(conn, table: str) -> set:
        try:
            rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
            return {row[1] for row in rows}
        except Exception:
            return set()

    def _bind_repos(self):
        from database.repositories.user_repository import SQLiteUserRepository
        from database.repositories.signature_repository import SQLiteSignatureRepository
        from database.repositories.document_repository import SQLiteDocumentRepository
        self.user_repo = SQLiteUserRepository(self)
        self.sig_repo  = SQLiteSignatureRepository(self)
        self.doc_repo  = SQLiteDocumentRepository(self)

    def get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def close_all(self):
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn