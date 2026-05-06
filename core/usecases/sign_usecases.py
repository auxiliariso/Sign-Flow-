"""
Casos de Uso:
  - AuthenticateUser
  - RegisterUser
  - GenerateSignature
  - ListSignatureHistory
"""
import hashlib
import secrets
from datetime import datetime
from typing import Tuple, Optional, List

from core.entities.user import User
from core.entities.signature import SignatureRecord
from core.interfaces.repositories import IUserRepository, ISignatureRepository, IDocumentSigner


class AuthenticateUser:
    def __init__(self, user_repo: IUserRepository):
        self._repo = user_repo

    def execute(self, nombre_completo: str, password: str) -> Tuple[bool, Optional[User]]:
        user = self._repo.get_by_nombre(nombre_completo)
        if not user:
            return False, None
        expected = _hash_password(password)
        if user.password_hash == expected:
            return True, user
        return False, None


class RegisterUser:
    def __init__(self, user_repo: IUserRepository):
        self._repo = user_repo

    def execute(self, nombre_completo: str, nombre_puesto: str, password: str) -> User:
        existing = self._repo.get_by_nombre(nombre_completo)
        if existing:
            raise ValueError(f"El usuario '{nombre_completo}' ya existe.")
        user = User(
            nombre_completo=nombre_completo,
            nombre_puesto=nombre_puesto,
            password_hash=_hash_password(password),
        )
        return self._repo.create(user)


class GenerateSignature:
    def __init__(
        self,
        signature_repo: ISignatureRepository,
        document_signer: IDocumentSigner,
    ):
        self._sig_repo = signature_repo
        self._doc_signer = document_signer

    def execute(self, user: User, doc_path: str, output_path: str) -> SignatureRecord:
        now = datetime.utcnow()
        fecha = now.strftime("%Y-%m-%d")
        hora = now.strftime("%H:%M:%S")

        # Generar firma_hash trazable y único
        raw = f"{user.id_user}|{doc_path}|{now.isoformat()}|{secrets.token_hex(8)}"
        firma_hash = hashlib.sha256(raw.encode()).hexdigest()

        # Delegar al handler específico del tipo de documento
        signed_path = self._doc_signer.sign(
            doc_path=doc_path,
            output_path=output_path,
            nombre_completo=user.nombre_completo,
            nombre_puesto=user.nombre_puesto,
            firma_hash=firma_hash,
            fecha=fecha,
            hora=hora,
        )

        record = SignatureRecord(
            id_user=user.id_user,
            nombre_completo=user.nombre_completo,
            nombre_puesto=user.nombre_puesto,
            firma_hash=firma_hash,
            documento_path=signed_path,
            tipo_documento=_detect_type(doc_path),
            fecha=fecha,
            hora=hora,
        )
        return self._sig_repo.save(record)


class ListSignatureHistory:
    def __init__(self, signature_repo: ISignatureRepository):
        self._repo = signature_repo

    def execute(self, id_user: Optional[int] = None) -> List[SignatureRecord]:
        if id_user:
            return self._repo.get_by_user(id_user)
        return self._repo.get_all()


# ── helpers ──────────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _detect_type(path: str) -> str:
    ext = path.rsplit(".", 1)[-1].lower()
    mapping = {"docx": "docx", "doc": "docx", "xlsx": "xlsx",
                "xls": "xlsx", "pptx": "pptx", "ppt": "pptx", "pdf": "pdf"}
    return mapping.get(ext, "unknown")
