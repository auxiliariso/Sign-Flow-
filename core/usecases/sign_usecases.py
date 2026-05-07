"""
core/usecases/sign_usecases.py
"""
from typing import Tuple, Optional, List
from core.entities.user import User
from core.entities.signature import SignatureRecord


def _hash_password(password: str) -> str:
    try:
        import bcrypt
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    except ImportError:
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()


def _check_password(password: str, hashed: str) -> bool:
    try:
        import bcrypt
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except (ImportError, Exception):
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest() == hashed


class AuthenticateUser:
    def __init__(self, user_repo):
        self._repo = user_repo

    def execute(self, nombre_completo: str, password: str) -> Tuple[bool, Optional[User]]:
        user = self._repo.get_by_nombre(nombre_completo)
        if not user:
            return False, None
        if _check_password(password, user.password_hash):
            return True, user
        return False, None


class RegisterUser:
    def __init__(self, user_repo):
        self._repo = user_repo

    def execute(self, nombre_completo: str, nombre_puesto: str, password: str) -> User:
        if self._repo.get_by_nombre(nombre_completo):
            raise ValueError(f"El usuario '{nombre_completo}' ya existe.")
        user = User(
            nombre_completo=nombre_completo,
            nombre_puesto=nombre_puesto,
            password_hash=_hash_password(password),
        )
        return self._repo.create(user)


class ListSignatureHistory:
    def __init__(self, signature_repo):
        self._repo = signature_repo

    def execute(self, id_user: Optional[int] = None) -> List:
        if id_user:
            return self._repo.get_by_user(id_user)
        return self._repo.get_all()
