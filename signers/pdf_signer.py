"""
signers/pdf_signer.py
=====================
Firmador para documentos PDF.

Capacidades:
  - Detecta texto "Firma:", "Responsable:", placeholders {{SIGNFLOW}}, etc.
  - Cada firma agrega una NUEVA PÁGINA al final (no sobrescribe).
  - Si hay múltiples firmas, la última página es un resumen acumulativo.
  - Genera página individual + QR por firma.
  - Usa reportlab para generar y PyMuPDF para fusionar.
"""
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
import fitz  # PyMuPDF

from core.signer_base import SignerBase, SignaturePayload, SignResult
from core.hash_service import HashService

NAVY  = HexColor("#1F3864")
MID   = HexColor("#2E5090")
LIGHT = HexColor("#D6E4F0")
PALE  = HexColor("#F0F4FA")
WHITE = HexColor("#FFFFFF")
DARK  = HexColor("#1A1A2E")
GREY  = HexColor("#6B7A99")

SIGNATURE_KEYWORDS = [
    "{{signflow}}", "{{firma_responsable}}", "{{multifirma}}",
    "{{responsables}}", "firma:", "responsable:", "revisó:", "autorizó:", "aprobó:",
]


class PdfSigner(SignerBase):

    def sign(
        self,
        doc_path: str,
        output_path: str,
        payload: SignaturePayload,
        all_previous: list[SignaturePayload],
    ) -> SignResult:
        all_sigs = list(all_previous) + [payload]

        # Abrir documento original
        original = fitz.open(doc_path)

        # Si hay una página de firmas anterior de SignFlow, quitarla
        original = self._remove_old_signature_pages(original)

        # Generar nueva página(s) de firma
        sig_pdf_bytes = _build_signature_page(payload, all_sigs)
        sig_doc = fitz.open("pdf", sig_pdf_bytes)
        original.insert_pdf(sig_doc)

        original.save(output_path)
        original.close()
        sig_doc.close()

        doc_hash = HashService().file_hash(output_path)
        return SignResult(
            output_path=output_path,
            firma_hash=payload.firma_hash,
            documento_hash_post=doc_hash,
        )

    def detect_signature_zones(self, doc_path: str) -> list[dict]:
        doc = fitz.open(doc_path)
        zones = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            for kw in SIGNATURE_KEYWORDS:
                if kw in text.lower():
                    zones.append({
                        "page": page_num + 1,
                        "keyword": kw,
                        "text_snippet": text[:120],
                    })
        doc.close()
        return zones

    def _remove_old_signature_pages(self, doc: fitz.Document) -> fitz.Document:
        """Elimina páginas previamente generadas por SignFlow."""
        pages_to_delete = []
        for i in range(len(doc)):
            page = doc[i]
            text = page.get_text()
            if "FIRMAS DIGITALES" in text and "SignFlow" in text:
                pages_to_delete.append(i)
        if pages_to_delete:
            doc.delete_pages(pages_to_delete)
        return doc


# ── Generación de página(s) de firma con reportlab ────────────────────────────

def _build_signature_page(
    payload: SignaturePayload,
    all_sigs: list[SignaturePayload],
) -> bytes:
    buf = io.BytesIO()
    W, H = letter
    c = canvas.Canvas(buf, pagesize=letter)

    _draw_signature_page(c, W, H, payload, all_sigs)

    c.showPage()
    c.save()
    return buf.getvalue()


def _draw_signature_page(c, W, H, payload: SignaturePayload,
                          all_sigs: list[SignaturePayload]):
    # ── Banner ────────────────────────────────────────────────────────────────
    c.setFillColor(NAVY)
    c.rect(0, H - 80, W, 80, fill=1, stroke=0)

    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(36, H - 42, f"\u2756 FIRMAS DIGITALES \u2014 SignFlow")

    c.setFont("Helvetica", 9)
    c.drawString(36, H - 62, f"Documento firmado digitalmente  \u00b7  "
                              f"{len(all_sigs)} firma(s) registrada(s)")

    # ── Tabla de firmas acumulativas ──────────────────────────────────────────
    y = H - 100
    row_h = 52

    for i, sig in enumerate(all_sigs):
        bg = LIGHT if i % 2 == 0 else PALE
        c.setFillColor(bg)
        c.roundRect(32, y - row_h + 6, W - 64, row_h - 2,
                    radius=4, fill=1, stroke=0)

        # Línea de acento izquierda
        is_current = sig.firma_hash == payload.firma_hash
        accent = NAVY if is_current else MID
        c.setFillColor(accent)
        c.rect(32, y - row_h + 6, 4, row_h - 2, fill=1, stroke=0)

        # Número
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(44, y - 12, f"#{i+1}")

        # ID de validación
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(MID)
        c.drawString(44, y - 24, sig.validation_id)

        # Nombre y cargo
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(130, y - 12, sig.nombre_completo)

        c.setFillColor(GREY)
        c.setFont("Helvetica", 9)
        c.drawString(130, y - 26, sig.nombre_puesto)

        # Fecha y hora
        c.setFont("Helvetica", 8)
        c.drawString(130, y - 40, f"{sig.fecha}  {sig.hora} UTC")

        # Hash (truncado)
        c.setFillColor(MID)
        c.setFont("Helvetica", 7)
        c.drawString(350, y - 12, f"Hash: {sig.firma_hash_short}")

        # QR del firmante actual
        if is_current and sig.qr_image_bytes:
            try:
                import PIL.Image
                qr_img = PIL.Image.open(io.BytesIO(sig.qr_image_bytes))
                qr_buf = io.BytesIO()
                qr_img.save(qr_buf, format="PNG")
                from reportlab.lib.utils import ImageReader
                qr_reader = ImageReader(io.BytesIO(qr_buf.getvalue()))
                c.drawImage(qr_reader, W - 80, y - row_h + 10,
                            width=44, height=44, mask="auto")
            except Exception:
                pass

        y -= row_h

        # Nueva página si no hay espacio
        if y < 80 and i < len(all_sigs) - 1:
            c.showPage()
            _redraw_header_mini(c, W, H)
            y = H - 80

    # ── Pie de página ─────────────────────────────────────────────────────────
    c.setFillColor(GREY)
    c.setFont("Helvetica-Oblique", 7)
    c.drawString(36, 24,
                 "Este documento fue firmado mediante SignFlow. "
                 "Los hashes garantizan integridad y trazabilidad criptográfica.")


def _redraw_header_mini(c, W, H):
    c.setFillColor(NAVY)
    c.rect(0, H - 36, W, 36, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(36, H - 22, "\u2756 FIRMAS DIGITALES (continuación) \u2014 SignFlow")