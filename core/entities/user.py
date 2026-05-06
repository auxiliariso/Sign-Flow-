"""
Entidad Usuario - Núcleo del dominio
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class User:
    nombre_completo: str
    nombre_puesto: str
    password_hash: str
    id_user: Optional[int] = None
    activo: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if not self.nombre_completo.strip():
            raise ValueError("El nombre completo no puede estar vacío.")
        if not self.nombre_puesto.strip():
            raise ValueError("El nombre del puesto no puede estar vacío.")

    @property
    def display_name(self) -> str:
        return f"{self.nombre_completo} — {self.nombre_puesto}"
