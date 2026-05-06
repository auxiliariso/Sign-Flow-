"""
core/document_service.py
========================
Orquestador principal del flujo de firma.

Responsabilidades:
  1. Registrar documento en BD (si no existe)
  2. Obtener historial de firmas previas
  3. Calcular hash encadenado
  4. Llamar al signer correcto según tipo de documento
  5. Guardar registro en BD
  6. Actualizar hash_actual del documento
"""
import shutil
from pathlib import Path
from datetime import datetime, timezone

from core.hash_service import HashService
from core.signer_base import SignaturePayload, SignResult
from services.qr_service import QRService
from services.dispatcher import get_signer


class DocumentService:

    def __init__(self, db):
        self._db = db
        self._qr = QRService()
        self._hash = HashService()

    # ── Flujo principal ───────────────────────────────────────────────────────

    def sign_document(
        self,
        doc_path: str,
        output_path: str,
        user,              # entidad User
        responsables: list[str] | None = None,
    ) -> dict:
        """
        Firma un documento. Si ya tiene firmas previas las conserva.
        Devuelve dict con info del registro generado.
        """
        doc_path = str(Path(doc_path).resolve())
        output_path = str(Path(output_path).resolve())

        # 1. Registrar o recuperar documento
        doc_record = self._db.doc_repo.get_or_create(
            filepath=doc_path,
            created_by=user.id_user,
        )

        # 2. Firmas previas del documento
        prev_sigs = self._db.sig_repo.get_by_document(doc_record["id_document"])
        hash_previo = prev_sigs[-1]["firma_hash"] if prev_sigs else "0"

        # 3. Hash actual del archivo en disco
        source = output_path if Path(output_path).exists() else doc_path
        documento_hash = self._hash.file_hash(source)
        timestamp_utc  = self._hash.now_utc()

        # 4. Hash encadenado de esta firma
        firma_hash = self._hash.signature_hash(
            documento_hash=documento_hash,
            id_user=user.id_user,
            timestamp_utc=timestamp_utc,
            hash_previo=hash_previo,
        )

        # 5. Validation ID y QR
        next_index    = self._db.sig_repo.count() + 1
        validation_id = self._hash.generate_validation_id(next_index)
        qr_bytes      = self._qr.generate(validation_id, firma_hash)

        # 6. Payload de la firma
        fecha = timestamp_utc[:10]
        hora  = timestamp_utc[11:19]

        payload = SignaturePayload(
            id_firma        = next_index,
            validation_id   = validation_id,
            nombre_completo = user.nombre_completo,
            nombre_puesto   = user.nombre_puesto,
            firma_hash      = firma_hash,
            firma_hash_short= self._hash.short_hash(firma_hash),
            fecha           = fecha,
            hora            = hora,
            timestamp_utc   = timestamp_utc,
            qr_image_bytes  = qr_bytes,
        )

        # 7. Construir payloads previos (para bloque acumulativo)
        prev_payloads = [self._sig_to_payload(s) for s in prev_sigs]

        # 8. Llamar al firmador del tipo correcto
        signer = get_signer(doc_path)
        if not Path(output_path).exists():
            shutil.copy2(doc_path, output_path)

        result: SignResult = signer.sign(
            doc_path      = output_path,
            output_path   = output_path,
            payload       = payload,
            all_previous  = prev_payloads,
        )

        # 9. Guardar en BD
        sig_record = {
            "id_document"     : doc_record["id_document"],
            "id_user"         : user.id_user,
            "nombre_completo" : user.nombre_completo,
            "nombre_puesto"   : user.nombre_puesto,
            "firma_hash"      : firma_hash,
            "hash_previo"     : hash_previo,
            "documento_hash"  : documento_hash,
            "documento_hash_post": result.documento_hash_post,
            "validation_id"   : validation_id,
            "fecha"           : fecha,
            "hora"            : hora,
            "timestamp_utc"   : timestamp_utc,
            "qr_data"         : validation_id,
        }
        saved = self._db.sig_repo.save(sig_record)

        # 10. Actualizar hash_actual del documento
        self._db.doc_repo.update_hash(
            id_document  = doc_record["id_document"],
            hash_actual  = result.documento_hash_post,
            version      = len(prev_sigs) + 1,
        )

        return {**saved, "output_path": result.output_path,
                "validation_id": validation_id}

    # ── helpers ───────────────────────────────────────────────────────────────

    def _sig_to_payload(self, sig: dict) -> SignaturePayload:
        return SignaturePayload(
            id_firma        = sig["id_firma"],
            validation_id   = sig.get("validation_id", ""),
            nombre_completo = sig["nombre_completo"],
            nombre_puesto   = sig["nombre_puesto"],
            firma_hash      = sig["firma_hash"],
            firma_hash_short= HashService.short_hash(sig["firma_hash"]),
            fecha           = sig["fecha"],
            hora            = sig["hora"],
            timestamp_utc   = sig.get("timestamp_utc", ""),
        )