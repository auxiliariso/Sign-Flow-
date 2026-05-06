"""
Handler - Firma en documentos PDF
Agrega una página de firma al final usando reportlab.
Requiere: pip install reportlab PyMuPDF
"""
import shutil
import io
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
import fitz  # PyMuPDF
from core.interfaces.repositories import IDocumentSigner

BRAND = HexColor("#1F3864")
LIGHT = HexColor("#D6E4F0")
WHITE = HexColor("#FFFFFF")
DARK  = HexColor("#333333")


class PdfSigner(IDocumentSigner):
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
        # Generar página de firma como PDF en memoria
        sig_pdf_bytes = _build_signature_page(
            nombre_completo, nombre_puesto, firma_hash, fecha, hora
        )

        # Unir documento original + página de firma
        original = fitz.open(doc_path)
        sig_doc  = fitz.open("pdf", sig_pdf_bytes)
        original.insert_pdf(sig_doc)
        original.save(output_path)
        original.close()
        sig_doc.close()

        return output_path


def _build_signature_page(nombre, puesto, hash_val, fecha, hora) -> bytes:
    buf = io.BytesIO()
    W, H = letter
    c = canvas.Canvas(buf, pagesize=letter)

    # Banner superior
    c.setFillColor(BRAND)
    c.rect(0, H - 90, W, 90, fill=1, stroke=0)

    # Título
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, H - 52, "\u2756 Documento Firmado Digitalmente")

    c.setFont("Helvetica", 10)
    c.drawString(40, H - 74, "SignFlow — Sistema de Firma Digital")

    # Filas de datos
    rows = [
        ("Firmado por",         nombre),
        ("Cargo / Puesto",      puesto),
        ("Fecha (UTC)",         fecha),
        ("Hora (UTC)",          hora),
        ("Hash de verificación", hash_val),
    ]

    y = H - 130
    row_h = 32

    for i, (label, value) in enumerate(rows):
        bg = LIGHT if i % 2 == 0 else WHITE
        c.setFillColor(bg)
        c.rect(36, y - 6, W - 72, row_h, fill=1, stroke=0)

        c.setFillColor(BRAND)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(44, y + 10, label)

        # Truncar hash para que quepa en una línea
        display_value = value if len(value) <= 80 else value[:77] + "..."
        c.setFillColor(DARK)
        c.setFont("Helvetica", 9)
        c.drawString(200, y + 10, display_value)

        y -= row_h

    # Nota al pie
    c.setFillColor(BRAND)
    c.setFont("Helvetica-Oblique", 7)
    note = ("Este documento ha sido firmado digitalmente. "
            "El hash de verificación certifica su autenticidad e integridad.")
    c.drawString(36, 40, note)

    c.showPage()
    c.save()
    return buf.getvalue()
