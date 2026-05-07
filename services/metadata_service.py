"""
services/metadata_service.py
============================
Incrusta y lee metadata SignFlow dentro de los documentos.
Funciona para docx, xlsx, pptx (custom properties) y pdf (XMP / info dict).

Esquema de metadata:
{
  "signflow_document_id": "DOC-0001",
  "signature_count": 3,
  "last_signature": "SF-2026-000003",
  "last_hash": "a4b7d5f9…",
  "created_by": "Juan Pérez"
}
"""
import json
from pathlib import Path


PROP_NAME = "SignFlow_Metadata"


class MetadataService:

    # ── DOCX ─────────────────────────────────────────────────────────────────

    def write_docx(self, filepath: str, metadata: dict):
        from docx import Document
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
        import lxml.etree as etree

        doc = Document(filepath)
        cp = doc.core_properties
        cp.description = json.dumps(metadata, ensure_ascii=False)
        doc.save(filepath)

    def read_docx(self, filepath: str) -> dict:
        from docx import Document
        doc = Document(filepath)
        raw = doc.core_properties.description or "{}"
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    # ── XLSX ─────────────────────────────────────────────────────────────────

    def write_xlsx(self, filepath: str, metadata: dict):
        import openpyxl
        wb = openpyxl.load_workbook(filepath)
        wb.properties.description = json.dumps(metadata, ensure_ascii=False)
        wb.save(filepath)

    def read_xlsx(self, filepath: str) -> dict:
        import openpyxl
        wb = openpyxl.load_workbook(filepath)
        raw = wb.properties.description or "{}"
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    # ── PPTX ─────────────────────────────────────────────────────────────────

    def write_pptx(self, filepath: str, metadata: dict):
        from pptx import Presentation
        prs = Presentation(filepath)
        prs.core_properties.description = json.dumps(metadata, ensure_ascii=False)
        prs.save(filepath)

    def read_pptx(self, filepath: str) -> dict:
        from pptx import Presentation
        prs = Presentation(filepath)
        raw = prs.core_properties.description or "{}"
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    # ── PDF ──────────────────────────────────────────────────────────────────

    def write_pdf(self, filepath: str, metadata: dict):
        import fitz
        doc = fitz.open(filepath)
        doc.set_metadata({"subject": json.dumps(metadata, ensure_ascii=False)})
        doc.saveIncr()
        doc.close()

    def read_pdf(self, filepath: str) -> dict:
        import fitz
        doc = fitz.open(filepath)
        raw = doc.metadata.get("subject", "{}")
        doc.close()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    # ── API unificada ─────────────────────────────────────────────────────────

    def write(self, filepath: str, metadata: dict):
        ext = filepath.rsplit(".", 1)[-1].lower()
        dispatch = {
            "docx": self.write_docx, "doc": self.write_docx,
            "xlsx": self.write_xlsx, "xls": self.write_xlsx,
            "pptx": self.write_pptx, "ppt": self.write_pptx,
            "pdf":  self.write_pdf,
        }
        fn = dispatch.get(ext)
        if fn:
            fn(filepath, metadata)

    def read(self, filepath: str) -> dict:
        ext = filepath.rsplit(".", 1)[-1].lower()
        dispatch = {
            "docx": self.read_docx, "doc": self.read_docx,
            "xlsx": self.read_xlsx, "xls": self.read_xlsx,
            "pptx": self.read_pptx, "ppt": self.read_pptx,
            "pdf":  self.read_pdf,
        }
        fn = dispatch.get(ext)
        return fn(filepath) if fn else {}
