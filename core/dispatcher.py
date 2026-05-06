"""
services/dispatcher.py
======================
Selecciona el firmador correcto según la extensión del archivo.
"""
from core.signer_base import SignerBase


def get_signer(filepath: str) -> SignerBase:
    ext = filepath.rsplit(".", 1)[-1].lower()
    if ext in ("docx", "doc"):
        from signers.docx_signer import DocxSigner
        return DocxSigner()
    if ext in ("xlsx", "xls"):
        from signers.xlsx_signer import XlsxSigner
        return XlsxSigner()
    if ext in ("pptx", "ppt"):
        from signers.pptx_signer import PptxSigner
        return PptxSigner()
    if ext == "pdf":
        from signers.pdf_signer import PdfSigner
        return PdfSigner()
    raise ValueError(f"Tipo de documento no soportado: '{ext}'")