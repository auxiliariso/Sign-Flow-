"""
services/signature_render_service.py
=====================================
Genera los bloques visuales de firma (para todos los tipos de documento).
Devuelve datos listos para que cada signer los inserte.

Diseño visual:
  ┌─────────────────────────────────────────────────────┐
  │  ✦ FIRMA DIGITAL — SF-2026-000182                   │
  │  ─────────────────────────────────────────────────  │
  │  Firmado por : Juan Francisco López                 │
  │  Cargo       : Coordinador ISO                      │
  │  Fecha       : 2026-05-06  |  Hora: 14:32:11 UTC   │
  │  Hash        : a4b7d5f9…fa281cda                   │
  │                                    [QR]             │
  └─────────────────────────────────────────────────────┘

Paleta corporativa basada en #1F3864
"""
from dataclasses import dataclass
from typing import Optional
from core.signer_base import SignaturePayload

# Colores en distintos formatos que necesitan los handlers
NAVY  = "#1F3864"
MID   = "#2E5090"
LIGHT = "#D6E4F0"
PALE  = "#F0F4FA"
WHITE = "#FFFFFF"
DARK  = "#1A1A2E"


@dataclass
class RenderedBlock:
    """Datos estructurados para que cada handler construya el bloque."""
    validation_id: str
    nombre_completo: str
    nombre_puesto: str
    fecha: str
    hora: str
    hash_short: str
    qr_bytes: Optional[bytes]
    is_first: bool      # True si es la primera firma del documento


def render(payload: SignaturePayload, is_first: bool = False) -> RenderedBlock:
    return RenderedBlock(
        validation_id   = payload.validation_id,
        nombre_completo = payload.nombre_completo,
        nombre_puesto   = payload.nombre_puesto,
        fecha           = payload.fecha,
        hora            = payload.hora,
        hash_short      = payload.firma_hash_short,
        qr_bytes        = payload.qr_image_bytes,
        is_first        = is_first,
    )
