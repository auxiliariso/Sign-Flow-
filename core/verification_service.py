"""
core/verification_service.py
============================
Verificación de integridad de documentos firmados.

Uso CLI:
    python main.py --verify archivo.docx

Verifica:
  ✓ Documento registrado en la BD
  ✓ Hash actual coincide con el hash almacenado
  ✓ Cadena de firmas íntegra (encadenamiento correcto)
  ✓ Timestamps en orden cronológico
"""
from dataclasses import dataclass, field
from pathlib import Path
from core.hash_service import HashService


@dataclass
class VerificationResult:
    filepath: str
    registered: bool = False
    hash_ok: bool = False
    chain_ok: bool = False
    signature_count: int = 0
    signatures: list[dict] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    document_id: str = ""

    @property
    def valid(self) -> bool:
        return self.registered and self.hash_ok and self.chain_ok

    def format_cli(self) -> str:
        lines = [
            "",
            "╔══════════════════════════════════════════════════════╗",
            "║         SignFlow v2 — Verificación de Documento      ║",
            "╚══════════════════════════════════════════════════════╝",
            f"  Archivo : {Path(self.filepath).name}",
            f"  Doc ID  : {self.document_id or '—'}",
            "",
        ]
        for msg in self.messages:
            lines.append(f"  {msg}")
        lines.append("")
        if self.signature_count:
            lines.append(f"  Firmas detectadas: {self.signature_count}")
            for i, s in enumerate(self.signatures, 1):
                lines.append(
                    f"    {i}. {s['nombre_completo']} ({s['nombre_puesto']}) "
                    f"— {s['fecha']} {s['hora']} — {s['validation_id']}"
                )
        lines.append("")
        status = "✓ DOCUMENTO VÁLIDO" if self.valid else "⚠ DOCUMENTO ALTERADO O NO REGISTRADO"
        lines.append(f"  {status}")
        lines.append("")
        return "\n".join(lines)


class VerificationService:

    def __init__(self, db):
        self._db = db
        self._hash = HashService()

    def verify_file(self, filepath: str) -> VerificationResult:
        result = VerificationResult(filepath=filepath)
        filepath = str(Path(filepath).resolve())

        if not Path(filepath).exists():
            result.messages.append("✘ Archivo no encontrado.")
            return result

        # 1. ¿Está registrado?
        doc = self._db.doc_repo.get_by_path(filepath)
        if not doc:
            result.messages.append("✘ Documento no registrado en SignFlow.")
            return result

        result.registered = True
        result.document_id = f"DOC-{doc['id_document']:04d}"

        # 2. Hash del archivo actual vs hash guardado
        current_hash = self._hash.file_hash(filepath)
        stored_hash  = doc["hash_actual"]

        if current_hash == stored_hash:
            result.hash_ok = True
            result.messages.append("✓ Integridad del archivo correcta.")
        else:
            result.messages.append(
                f"⚠ El archivo fue modificado después de la última firma.\n"
                f"     Guardado : {stored_hash[:32]}…\n"
                f"     Actual   : {current_hash[:32]}…"
            )

        # 3. Cadena de firmas
        sigs = self._db.sig_repo.get_by_document(doc["id_document"])
        result.signature_count = len(sigs)
        result.signatures      = sigs

        if sigs:
            chain_ok, chain_msg = self._hash.verify_chain(sigs)
            result.chain_ok = chain_ok
            result.messages.append(chain_msg)

            # 4. Orden cronológico
            timestamps = [s["timestamp_utc"] for s in sigs if s.get("timestamp_utc")]
            if timestamps == sorted(timestamps):
                result.messages.append("✓ Timestamps en orden cronológico correcto.")
            else:
                result.messages.append("⚠ Los timestamps están fuera de orden.")
                result.chain_ok = False
        else:
            result.chain_ok = True
            result.messages.append("✓ Sin firmas previas (documento limpio).")

        return result

    def verify_by_id(self, id_document: int) -> VerificationResult:
        doc = self._db.doc_repo.get_by_id(id_document)
        if not doc:
            r = VerificationResult(filepath="")
            r.messages.append("✘ Documento no encontrado en BD.")
            return r
        return self.verify_file(doc["filepath"])