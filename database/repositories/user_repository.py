"""
database/repositories/user_repository.py  (v2.5 — CRUD completo)
"""
from datetime import datetime
from typing import Optional


class SQLiteUserRepository:

    def __init__(self, db):
        self._db = db

    def create(self, user) -> object:
        with self._db.get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO users (nombre_completo, nombre_puesto, password_hash, activo, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (user.nombre_completo, user.nombre_puesto, user.password_hash,
                 int(user.activo), datetime.now().isoformat()),
            )
            user.id_user = cur.lastrowid
            return user

    def get_by_id(self, id_user: int) -> Optional[object]:
        with self._db.get_conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE id_user = ?", (id_user,)).fetchone()
            return _row_to_user(row) if row else None

    def get_by_nombre(self, nombre_completo: str) -> Optional[object]:
        with self._db.get_conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE nombre_completo = ?",
                               (nombre_completo,)).fetchone()
            return _row_to_user(row) if row else None

    def list_all(self) -> list:
        with self._db.get_conn() as conn:
            rows = conn.execute("SELECT * FROM users ORDER BY id_user").fetchall()
            return [_row_to_user(r) for r in rows]

    def list_activos(self) -> list:
        with self._db.get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM users WHERE activo = 1 ORDER BY nombre_completo"
            ).fetchall()
            return [_row_to_user(r) for r in rows]

    # ── UPDATE ────────────────────────────────────────────────────────────────

    def update(self, user) -> object:
        with self._db.get_conn() as conn:
            conn.execute(
                "UPDATE users SET nombre_completo=?, nombre_puesto=?, activo=? WHERE id_user=?",
                (user.nombre_completo, user.nombre_puesto, int(user.activo), user.id_user),
            )
            return user

    def update_nombre(self, id_user: int, nuevo_nombre: str) -> bool:
        """Edita SOLO el nombre_completo. Lanza ValueError si está vacío."""
        if not nuevo_nombre.strip():
            raise ValueError("El nombre completo no puede estar vacío.")
        with self._db.get_conn() as conn:
            cur = conn.execute(
                "UPDATE users SET nombre_completo=? WHERE id_user=?",
                (nuevo_nombre.strip(), id_user),
            )
            return cur.rowcount > 0

    def update_puesto(self, id_user: int, nuevo_puesto: str) -> bool:
        if not nuevo_puesto.strip():
            raise ValueError("El puesto no puede estar vacío.")
        with self._db.get_conn() as conn:
            cur = conn.execute(
                "UPDATE users SET nombre_puesto=? WHERE id_user=?",
                (nuevo_puesto.strip(), id_user),
            )
            return cur.rowcount > 0

    def update_password(self, id_user: int, nuevo_hash: str) -> bool:
        with self._db.get_conn() as conn:
            cur = conn.execute(
                "UPDATE users SET password_hash=? WHERE id_user=?",
                (nuevo_hash, id_user),
            )
            return cur.rowcount > 0

    def deactivate(self, id_user: int) -> bool:
        with self._db.get_conn() as conn:
            cur = conn.execute("UPDATE users SET activo=0 WHERE id_user=?", (id_user,))
            return cur.rowcount > 0

    def activate(self, id_user: int) -> bool:
        with self._db.get_conn() as conn:
            cur = conn.execute("UPDATE users SET activo=1 WHERE id_user=?", (id_user,))
            return cur.rowcount > 0

    def delete(self, id_user: int) -> bool:
        with self._db.get_conn() as conn:
            cur = conn.execute("DELETE FROM users WHERE id_user=?", (id_user,))
            return cur.rowcount > 0


def _row_to_user(row):
    from core.entities.user import User
    u = User(nombre_completo=row["nombre_completo"],
             nombre_puesto=row["nombre_puesto"],
             password_hash=row["password_hash"],
             activo=bool(row["activo"]))
    u.id_user = row["id_user"]
    return u
