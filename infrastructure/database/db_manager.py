"""
Infraestructura - Gestor de base de datos SQLite
Genera automáticamente las tablas al inicializarse.

Esquema:
  users       → id_user (PK autoincrement), nombre_completo, nombre_puesto,
                password_hash, activo, created_at
  signatures  → id_firma (PK), id_user (FK), nombre_completo, nombre_puesto,
                firma_hash, documento_path, tipo_documento, hora, fecha
"""
import sqlite3
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from core.entities.user import User
from core.entities.signature import SignatureRecord
from core.interfaces.repositories import IUserRepository, ISignatureRepository


class DatabaseManager:
    def __init__(self, db_path: str = "signflow.db"):
        self.db_path = db_path

    def get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self):
        """Crea las tablas si no existen."""
        with self.get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id_user        INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre_completo TEXT NOT NULL UNIQUE,
                    nombre_puesto   TEXT NOT NULL,
                    password_hash   TEXT NOT NULL,
                    activo          INTEGER NOT NULL DEFAULT 1,
                    created_at      TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS signatures (
                    id_firma        INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_user         INTEGER NOT NULL,
                    nombre_completo TEXT NOT NULL,
                    nombre_puesto   TEXT NOT NULL,
                    firma_hash      TEXT NOT NULL UNIQUE,
                    documento_path  TEXT NOT NULL,
                    tipo_documento  TEXT NOT NULL,
                    hora            TEXT NOT NULL,
                    fecha           TEXT NOT NULL,
                    FOREIGN KEY (id_user) REFERENCES users(id_user)
                );

                CREATE INDEX IF NOT EXISTS idx_sig_user ON signatures(id_user);
                CREATE INDEX IF NOT EXISTS idx_sig_hash ON signatures(firma_hash);
            """)


class SQLiteUserRepository(IUserRepository):
    def __init__(self, db: DatabaseManager):
        self._db = db

    def create(self, user: User) -> User:
        with self._db.get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO users (nombre_completo, nombre_puesto, password_hash, activo, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (user.nombre_completo, user.nombre_puesto,
                 user.password_hash, int(user.activo),
                 datetime.utcnow().isoformat()),
            )
            user.id_user = cur.lastrowid
            return user

    def get_by_id(self, id_user: int) -> Optional[User]:
        with self._db.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE id_user = ?", (id_user,)
            ).fetchone()
            return _row_to_user(row) if row else None

    def get_by_nombre(self, nombre_completo: str) -> Optional[User]:
        with self._db.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE nombre_completo = ?", (nombre_completo,)
            ).fetchone()
            return _row_to_user(row) if row else None

    def list_all(self) -> List[User]:
        with self._db.get_conn() as conn:
            rows = conn.execute("SELECT * FROM users ORDER BY id_user").fetchall()
            return [_row_to_user(r) for r in rows]

    def update(self, user: User) -> User:
        with self._db.get_conn() as conn:
            conn.execute(
                "UPDATE users SET nombre_completo=?, nombre_puesto=?, activo=? WHERE id_user=?",
                (user.nombre_completo, user.nombre_puesto, int(user.activo), user.id_user),
            )
            return user


class SQLiteSignatureRepository(ISignatureRepository):
    def __init__(self, db: DatabaseManager):
        self._db = db

    def save(self, record: SignatureRecord) -> SignatureRecord:
        with self._db.get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO signatures "
                "(id_user, nombre_completo, nombre_puesto, firma_hash, "
                " documento_path, tipo_documento, hora, fecha) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (record.id_user, record.nombre_completo, record.nombre_puesto,
                 record.firma_hash, record.documento_path, record.tipo_documento,
                 record.hora, record.fecha),
            )
            record.id_firma = cur.lastrowid
            return record

    def get_by_user(self, id_user: int) -> List[SignatureRecord]:
        with self._db.get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM signatures WHERE id_user = ? ORDER BY fecha DESC, hora DESC",
                (id_user,),
            ).fetchall()
            return [_row_to_sig(r) for r in rows]

    def get_all(self) -> List[SignatureRecord]:
        with self._db.get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM signatures ORDER BY fecha DESC, hora DESC"
            ).fetchall()
            return [_row_to_sig(r) for r in rows]

    def get_by_hash(self, firma_hash: str) -> Optional[SignatureRecord]:
        with self._db.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM signatures WHERE firma_hash = ?", (firma_hash,)
            ).fetchone()
            return _row_to_sig(row) if row else None


# ── helpers ──────────────────────────────────────────────────────────────────

def _row_to_user(row) -> User:
    u = User(
        nombre_completo=row["nombre_completo"],
        nombre_puesto=row["nombre_puesto"],
        password_hash=row["password_hash"],
        activo=bool(row["activo"]),
    )
    u.id_user = row["id_user"]
    return u


def _row_to_sig(row) -> SignatureRecord:
    r = SignatureRecord(
        id_user=row["id_user"],
        nombre_completo=row["nombre_completo"],
        nombre_puesto=row["nombre_puesto"],
        firma_hash=row["firma_hash"],
        documento_path=row["documento_path"],
        tipo_documento=row["tipo_documento"],
        hora=row["hora"],
        fecha=row["fecha"],
    )
    r.id_firma = row["id_firma"]
    return r
