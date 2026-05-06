"""
Interfaces / Contratos de repositorios (puertos)
La capa de casos de uso depende SOLO de estas abstracciones.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from core.entities.user import User
from core.entities.signature import SignatureRecord


class IUserRepository(ABC):
    @abstractmethod
    def create(self, user: User) -> User: ...

    @abstractmethod
    def get_by_id(self, id_user: int) -> Optional[User]: ...

    @abstractmethod
    def get_by_nombre(self, nombre_completo: str) -> Optional[User]: ...

    @abstractmethod
    def list_all(self) -> List[User]: ...

    @abstractmethod
    def update(self, user: User) -> User: ...


class ISignatureRepository(ABC):
    @abstractmethod
    def save(self, record: SignatureRecord) -> SignatureRecord: ...

    @abstractmethod
    def get_by_user(self, id_user: int) -> List[SignatureRecord]: ...

    @abstractmethod
    def get_all(self) -> List[SignatureRecord]: ...

    @abstractmethod
    def get_by_hash(self, firma_hash: str) -> Optional[SignatureRecord]: ...


class IDocumentSigner(ABC):
    """Contrato para los manejadores de documentos."""
    @abstractmethod
    def sign(
        self,
        doc_path: str,
        output_path: str,
        nombre_completo: str,
        nombre_puesto: str,
        firma_hash: str,
        fecha: str,
        hora: str,
    ) -> str:
        """Firma el documento y retorna la ruta del archivo firmado."""
        ...
