"""
Entidad Firma - Registro de cada firma generada
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SignatureRecord:
    """
    Cada vez que un usuario firma un documento,
    se crea un registro en esta entidad.
    Columnas: id_user, nombre_completo, nombre_puesto,
              firma_hash, hora, fecha
    """
    id_user: int
    nombre_completo: str
    nombre_puesto: str
    firma_hash: str            # SHA-256 de (user_id + doc_path + timestamp)
    documento_path: str
    tipo_documento: str        # docx | xlsx | pptx | pdf
    hora: str = field(default_factory=lambda: datetime.utcnow().strftime("%H:%M:%S"))
    fecha: str = field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d"))
    id_firma: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "id_firma": self.id_firma,
            "id_user": self.id_user,
            "nombre_completo": self.nombre_completo,
            "nombre_puesto": self.nombre_puesto,
            "firma_hash": self.firma_hash,
            "documento_path": self.documento_path,
            "tipo_documento": self.tipo_documento,
            "hora": self.hora,
            "fecha": self.fecha,
        }
