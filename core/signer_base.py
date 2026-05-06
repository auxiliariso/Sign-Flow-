"""
core/signer_base.py
===================
Clase base abstracta para todos los firmadores de documentos.
Define el contrato que DocxSigner, XlsxSigner, PptxSigner y PdfSigner
deben cumplir.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class SignaturePayload:
    """Datos de una firma a insertar en el documento."""
    id_firma: int
    validation_id: str          # SF-2026-000182
    nombre_completo: str
    nombre_puesto: str
    firma_hash: str             # hash completo (guardado en metadata)
    firma_hash_short: str       # "a4b7d5f9…fa281cda" (visible)
    fecha: str                  # YYYY-MM-DD
    hora: str                   # HH:MM:SS
    timestamp_utc: str
    qr_image_bytes: Optional[bytes] = None   # PNG del QR


@dataclass
class SignResult:
    """Resultado de la operación de firma."""
    output_path: str
    firma_hash: str
    documento_hash_post: str    # hash del archivo después de firmado


class SignerBase(ABC):
    """
    Interfaz que todo firmador debe implementar.
    """

    @abstractmethod
    def sign(
        self,
        doc_path: str,
        output_path: str,
        payload: SignaturePayload,
        all_previous: list[SignaturePayload],
    ) -> SignResult:
        """
        Firma el documento.

        :param doc_path:       Ruta del archivo original (o ya firmado).
        :param output_path:    Ruta de salida.
        :param payload:        Datos de la firma actual.
        :param all_previous:   Firmas ya insertadas (para el bloque acumulativo).
        :return:               SignResult con ruta y hashes.
        """
        ...

    @abstractmethod
    def detect_signature_zones(self, doc_path: str) -> list[dict]:
        """
        Detecta zonas de firma en el documento.
        Devuelve lista de dicts con al menos: {'type': str, 'location': str}
        """
        ...

    @staticmethod
    def _all_signatures_block(
        payload: SignaturePayload,
        all_previous: list[SignaturePayload],
    ) -> list[SignaturePayload]:
        """Devuelve la lista completa de firmas incluyendo la actual."""
        return list(all_previous) + [payload]