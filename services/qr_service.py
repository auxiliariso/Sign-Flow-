"""
services/qr_service.py
======================
Genera imágenes QR únicas por firma.
El QR codifica el validation_id (SF-2026-000182) y el hash corto.
"""
import io
import qrcode
from qrcode.image.pil import PilImage


class QRService:

    def generate(self, validation_id: str, firma_hash: str) -> bytes:
        """
        Devuelve bytes PNG del QR con los datos de validación.
        """
        data = f"SIGNFLOW:{validation_id}:{firma_hash[:16]}"
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=4,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img: PilImage = qr.make_image(
            fill_color="#1F3864",
            back_color="white",
        )
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()