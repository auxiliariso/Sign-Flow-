"""
Infraestructura - Dispatcher de manejadores de documentos
Selecciona el handler correcto según la extensión del archivo.
"""
import os
from core.interfaces.repositories import IDocumentSigner
from infrastructure.document_handlers.docx_handler import DocxSigner
from infrastructure.document_handlers.xlsx_handler import XlsxSigner
from infrastructure.document_handlers.pptx_handler import PptxSigner
from infrastructure.document_handlers.pdf_handler import PdfSigner


class DocumentSignerDispatcher(IDocumentSigner):
    """
    Fachada que selecciona el handler correcto según la extensión.
    """
    _handlers = {
        "docx": DocxSigner,
        "doc":  DocxSigner,
        "xlsx": XlsxSigner,
        "xls":  XlsxSigner,
        "pptx": PptxSigner,
        "ppt":  PptxSigner,
        "pdf":  PdfSigner,
    }

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
        ext = doc_path.rsplit(".", 1)[-1].lower()
        handler_cls = self._handlers.get(ext)
        if not handler_cls:
            raise ValueError(f"Tipo de documento no soportado: '{ext}'")

        handler: IDocumentSigner = handler_cls()
        return handler.sign(
            doc_path=doc_path,
            output_path=output_path,
            nombre_completo=nombre_completo,
            nombre_puesto=nombre_puesto,
            firma_hash=firma_hash,
            fecha=fecha,
            hora=hora,
        )
