"""
signers/docx_signer.py
======================
Firmador para documentos Word (.docx).

Capacidades:
  - Detecta placeholders: {{SIGNFLOW}}, {{FIRMA_RESPONSABLE}}, {{MULTIFIRMA}},
    {{RESPONSABLES}}, y texto como "Firma:", "Responsable:", "Revisó:", etc.
  - Cada firma agrega un nuevo bloque visual (NO sobrescribe el anterior).
  - Si no hay placeholder, agrega el bloque al final del documento.
  - Soporta múltiples responsables.
  - Conserva formato, estilos y celdas del documento original.
"""
import io
import shutil
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from core.signer_base import SignerBase, SignaturePayload, SignResult
from core.hash_service import HashService
from services.signature_render_service import NAVY, MID, LIGHT, WHITE, DARK

_NAVY  = RGBColor(0x1F, 0x38, 0x64)
_MID   = RGBColor(0x2E, 0x50, 0x90)
_LIGHT = RGBColor(0xD6, 0xE4, 0xF0)
_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
_DARK  = RGBColor(0x1A, 0x1A, 0x2E)

# Palabras clave para detección de zonas de firma
SIGNATURE_KEYWORDS = [
    "{{signflow}}", "{{firma_responsable}}", "{{multifirma}}",
    "{{responsables}}", "{{firma}}",
    "firma:", "responsable:", "responsables:", "nombre:", "nombre y firma:",
    "revisó:", "autorizó:", "aprobó:", "elaboró:", "verificó:",
]


class DocxSigner(SignerBase):

    def sign(
        self,
        doc_path: str,
        output_path: str,
        payload: SignaturePayload,
        all_previous: list[SignaturePayload],
    ) -> SignResult:
        doc = Document(doc_path)
        inserted = False

        # 1. Intentar insertar en placeholder detectado
        inserted = self._replace_placeholder(doc, payload, all_previous)

        # 2. Si no hay placeholder, agregar bloque al final
        if not inserted:
            self._append_signature_block(doc, payload, is_first=len(all_previous) == 0)

        doc.save(output_path)
        doc_hash = HashService().file_hash(output_path)
        return SignResult(output_path=output_path,
                         firma_hash=payload.firma_hash,
                         documento_hash_post=doc_hash)

    def detect_signature_zones(self, doc_path: str) -> list[dict]:
        doc = Document(doc_path)
        zones = []
        for i, para in enumerate(doc.paragraphs):
            text = para.text.strip().lower()
            for kw in SIGNATURE_KEYWORDS:
                if kw in text:
                    zones.append({"type": "paragraph", "index": i,
                                  "text": para.text.strip(), "keyword": kw})
        for table in doc.tables:
            for r, row in enumerate(table.rows):
                for c, cell in enumerate(row.cells):
                    text = cell.text.strip().lower()
                    for kw in SIGNATURE_KEYWORDS:
                        if kw in text:
                            zones.append({"type": "table_cell",
                                          "row": r, "col": c,
                                          "text": cell.text.strip(), "keyword": kw})
        return zones

    # ── Inserción en placeholder ──────────────────────────────────────────────

    def _replace_placeholder(
        self,
        doc: Document,
        payload: SignaturePayload,
        all_previous: list[SignaturePayload],
    ) -> bool:
        # Buscar en tablas (más común en docs ISO)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    txt = cell.text.strip().lower()
                    if any(kw in txt for kw in SIGNATURE_KEYWORDS):
                        self._fill_cell(cell, payload)
                        return True

        # Buscar en párrafos
        for i, para in enumerate(doc.paragraphs):
            txt = para.text.strip().lower()
            if any(kw in txt for kw in SIGNATURE_KEYWORDS):
                # Limpiar placeholder y sustituir
                for run in para.runs:
                    run.text = ""
                self._write_inline_block(para, payload)
                return True

        return False

    def _fill_cell(self, cell, payload: SignaturePayload):
        """Llena una celda de tabla con la tarjeta de firma."""
        for p in cell.paragraphs:
            for run in p.runs:
                run.text = ""

        p = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
        self._add_run(p, f"✦ {payload.validation_id}", bold=True,
                      color=_NAVY, size=Pt(8))
        p = cell.add_paragraph()
        self._add_run(p, payload.nombre_completo, bold=True,
                      color=_DARK, size=Pt(9))
        p = cell.add_paragraph()
        self._add_run(p, payload.nombre_puesto, bold=False,
                      color=_MID, size=Pt(8))
        p = cell.add_paragraph()
        self._add_run(p, f"{payload.fecha}  {payload.hora} UTC",
                      bold=False, color=_MID, size=Pt(7))
        p = cell.add_paragraph()
        self._add_run(p, f"Hash: {payload.firma_hash_short}",
                      bold=False, color=_LIGHT, size=Pt(7))

    def _write_inline_block(self, para, payload: SignaturePayload):
        self._add_run(para, f"[{payload.validation_id}] {payload.nombre_completo} "
                      f"({payload.nombre_puesto}) — {payload.fecha}",
                      bold=True, color=_NAVY, size=Pt(9))

    # ── Bloque al final del documento ─────────────────────────────────────────

    def _append_signature_block(
        self,
        doc: Document,
        payload: SignaturePayload,
        is_first: bool,
    ):
        if is_first:
            # Separador visual solo en la primera firma
            sep = doc.add_paragraph()
            sep.paragraph_format.space_before = Pt(20)
            r = sep.add_run("─" * 68)
            r.font.color.rgb = _NAVY
            r.font.size = Pt(8)

            title = doc.add_paragraph()
            rt = title.add_run("✦ FIRMAS DIGITALES — SignFlow")
            rt.bold = True
            rt.font.color.rgb = _NAVY
            rt.font.size = Pt(11)

        # Tarjeta de firma
        self._build_card(doc, payload)

    def _build_card(self, doc: Document, payload: SignaturePayload):
        tbl = doc.add_table(rows=1, cols=2)
        tbl.style = "Table Grid"

        # Columna izquierda: datos
        left = tbl.cell(0, 0)
        left.width = Emu(5_500_000)
        lp = left.paragraphs[0]
        lp.paragraph_format.space_before = Pt(4)

        def add(text, bold=False, color=_DARK, size=Pt(9)):
            p = left.add_paragraph()
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after  = Pt(1)
            self._add_run(p, text, bold=bold, color=color, size=size)

        self._add_run(lp, f"✦ {payload.validation_id}",
                      bold=True, color=_NAVY, size=Pt(9))
        add(f"Firmado por : {payload.nombre_completo}", bold=True, color=_DARK)
        add(f"Cargo       : {payload.nombre_puesto}", color=_MID)
        add(f"Fecha       : {payload.fecha}  Hora: {payload.hora} UTC", color=_MID)
        add(f"Hash        : {payload.firma_hash_short}", color=_MID, size=Pt(8))

        # Columna derecha: QR
        right = tbl.cell(0, 1)
        right.width = Emu(1_200_000)
        if payload.qr_image_bytes:
            rp = right.paragraphs[0]
            rp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = rp.add_run()
            run.add_picture(io.BytesIO(payload.qr_image_bytes), width=Inches(0.8))

        # Shading del header
        _set_cell_bg(left, "1F3864" if True else "F0F4FA")
        doc.add_paragraph()  # espacio entre firmas

    @staticmethod
    def _add_run(para, text, bold=False, color=_DARK, size=Pt(9)):
        run = para.add_run(text)
        run.bold = bold
        run.font.color.rgb = color
        run.font.size = size
        return run


def _set_cell_bg(cell, hex_color: str):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  hex_color)
    tcPr.append(shd)