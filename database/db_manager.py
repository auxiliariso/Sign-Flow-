"""
database/db_manager.py  (v2.3)
==============================
Estrategia:
  1. Crear tablas con CREATE TABLE IF NOT EXISTS (sin columnas nuevas en signatures viejo)
  2. Migrar columna por columna con ALTER TABLE ADD COLUMN IF NOT EXISTS
  3. Nunca fallar si la columna ya existe
"""
import sqlite3
from datetime import datetime

# ── Tablas base (compatibles con BD v1) ───────────────────────────────────────
DDL_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id_user         INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_completo TEXT    NOT NULL UNIQUE,
    nombre_puesto   TEXT    NOT NULL,
    password_hash   TEXT    NOT NULL,
    activo          INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT    NOT NULL DEFAULT ''
);
"""

DDL_DOCUMENTS = """
CREATE TABLE IF NOT EXISTS documents (
    id_document    INTEGER PRIMARY KEY AUTOINCREMENT,
    filepath       TEXT    NOT NULL UNIQUE,
    nombre         TEXT    NOT NULL,
    tipo           TEXT    NOT NULL,
    hash_original  TEXT,
    hash_actual    TEXT,
    version_actual INTEGER NOT NULL DEFAULT 0,
    created_at     TEXT    NOT NULL DEFAULT '',
    created_by     INTEGER
);
"""

DDL_SIGNATURES = """
CREATE TABLE IF NOT EXISTS signatures (
    id_firma        INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user         INTEGER NOT NULL,
    nombre_completo TEXT    NOT NULL,
    nombre_puesto   TEXT    NOT NULL,
    firma_hash      TEXT    NOT NULL UNIQUE,
    fecha           TEXT    NOT NULL,
    hora            TEXT    NOT NULL
);
"""

DDL_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_sig_user ON signatures(id_user);
CREATE INDEX IF NOT EXISTS idx_sig_hash ON signatures(firma_hash);
"""

# ── Columnas a agregar si faltan (migración incremental) ─────────────────────
SIGNATURE_EXTRA_COLS = [
    ("id_document",          "INTEGER"),
    ("hash_previo",          "TEXT NOT NULL DEFAULT '0'"),
    ("documento_hash",       "TEXT"),
    ("documento_hash_post",  "TEXT"),
    ("validation_id",        "TEXT"),
    ("timestamp_utc",        "TEXT"),
    ("qr_data",              "TEXT"),
    ("documento_path",       "TEXT"),
    ("tipo_documento",       "TEXT"),
]


class DatabaseManager:

    def __init__(self, db_path: str = "signflow.db"):
        self.db_path = db_path
        self._conn   = None
        self.user_repo = None
        self.sig_repo  = None
        self.doc_repo  = None

    def initialize(self):
        # Paso 1: crear tablas mínimas (nunca falla en BD vieja)
        with self._connect() as conn:
            conn.execute(DDL_USERS)
            conn.execute(DDL_DOCUMENTS)
            conn.execute(DDL_SIGNATURES)
            conn.executescript(DDL_INDEXES)

        # Paso 2: agregar columnas que falten (sin tocar datos)
        self._migrate()

        # Paso 3: enlazar repositorios
        self._bind_repos()

    # ── Migración ─────────────────────────────────────────────────────────────

    def _migrate(self):
        with self._connect() as conn:
            existing = self._columns(conn, "signatures")
            for col_name, col_def in SIGNATURE_EXTRA_COLS:
                if col_name not in existing:
                    try:
                        conn.execute(
                            f"ALTER TABLE signatures ADD COLUMN {col_name} {col_def}"
                        )
                    except sqlite3.OperationalError:
                        pass   # ya existe — ignorar

            # Índice de id_document (puede fallar si columna aún no existe)
            try:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_sig_doc "
                    "ON signatures(id_document)"
                )
            except sqlite3.OperationalError:
                pass

    @staticmethod
    def _columns(conn, table: str) -> set:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return {row[1] for row in rows}

    # ── Repositorios ──────────────────────────────────────────────────────────

    def _bind_repos(self):
        from database.repositories.user_repository import SQLiteUserRepository
        from database.repositories.signature_repository import SQLiteSignatureRepository
        from database.repositories.document_repository import SQLiteDocumentRepository
        self.user_repo = SQLiteUserRepository(self)
        self.sig_repo  = SQLiteSignatureRepository(self)
        self.doc_repo  = SQLiteDocumentRepository(self)

    # ── Conexión ──────────────────────────────────────────────────────────────

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