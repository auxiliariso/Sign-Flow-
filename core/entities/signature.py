"""
core/entities/signature.py
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SignatureRecord:
    id_user: int
    nombre_completo: str
    nombre_puesto: str
    firma_hash: str
    documento_path: str
    tipo_documento: str
    hora: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))
    fecha: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
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
