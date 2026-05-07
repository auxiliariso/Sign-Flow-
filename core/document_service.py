"""
core/document_service.py  (v2.1)
================================
- Usa hora LOCAL del sistema para fecha/hora visible en la firma
- Usa hora UTC solo para el hash encadenado (integridad criptográfica)
- firma_hash_short → formato compacto "a4b7…cda1" (4+4)
"""
import shutil
from pathlib import Path

from core.hash_service import HashService
from core.signer_base import SignaturePayload, SignResult
from services.qr_service import QRService
from services.dispatcher import get_signer


class DocumentService:

    def __init__(self, db):
        self._db = db
        self._qr  = QRService()
        self._h   = HashService()

    def sign_document(self, doc_path: str, output_path: str, user) -> dict:
        doc_path    = str(Path(doc_path).resolve())
        output_path = str(Path(output_path).resolve())

        doc_record  = self._db.doc_repo.get_or_create(
            filepath=doc_path, created_by=user.id_user
        )
        prev_sigs  = self._db.sig_repo.get_by_document(doc_record["id_document"])
        hash_previo = prev_sigs[-1]["firma_hash"] if prev_sigs else "0"

        source        = output_path if Path(output_path).exists() else doc_path
        documento_hash = self._h.file_hash(source)

        # UTC para la cadena criptográfica
        timestamp_utc = self._h.now_utc()

        # LOCAL para lo que el usuario ve
        fecha_local, hora_local = self._h.local_date_time()

        firma_hash = self._h.signature_hash(
            documento_hash=documento_hash,
            id_user=user.id_user,
            timestamp_utc=timestamp_utc,
            hash_previo=hash_previo,
        )

        next_index    = self._db.sig_repo.count() + 1
        validation_id = self._h.generate_validation_id(next_index)
        qr_bytes      = self._qr.generate(validation_id, firma_hash)

        payload = SignaturePayload(
            id_firma         = next_index,
            validation_id    = validation_id,
            nombre_completo  = user.nombre_completo,
            nombre_puesto    = user.nombre_puesto,
            firma_hash       = firma_hash,
            firma_hash_short = self._h.short_hash(firma_hash),   # "a4b7…cda1"
            fecha            = fecha_local,    # hora local
            hora             = hora_local,     # hora local
            timestamp_utc    = timestamp_utc,
            qr_image_bytes   = qr_bytes,
        )

        prev_payloads = [self._sig_to_payload(s) for s in prev_sigs]

        signer = get_signer(doc_path)
        if not Path(output_path).exists():
            shutil.copy2(doc_path, output_path)

        result: SignResult = signer.sign(
            doc_path     = output_path,
            output_path  = output_path,
            payload      = payload,
            all_previous = prev_payloads,
        )

        sig_record = {
            "id_document"        : doc_record["id_document"],
            "id_user"            : user.id_user,
            "nombre_completo"    : user.nombre_completo,
            "nombre_puesto"      : user.nombre_puesto,
            "firma_hash"         : firma_hash,
            "hash_previo"        : hash_previo,
            "documento_hash"     : documento_hash,
            "documento_hash_post": result.documento_hash_post,
            "validation_id"      : validation_id,
            "fecha"              : fecha_local,
            "hora"               : hora_local,
            "timestamp_utc"      : timestamp_utc,
            "qr_data"            : validation_id,
        }
        saved = self._db.sig_repo.save(sig_record)

        self._db.doc_repo.update_hash(
            id_document = doc_record["id_document"],
            hash_actual = result.documento_hash_post,
            version     = len(prev_sigs) + 1,
        )

        return {**saved, "output_path": result.output_path,
                "validation_id": validation_id}

    def _sig_to_payload(self, sig: dict) -> SignaturePayload:
        return SignaturePayload(
            id_firma         = sig["id_firma"],
            validation_id    = sig.get("validation_id", ""),
            nombre_completo  = sig["nombre_completo"],
            nombre_puesto    = sig["nombre_puesto"],
            firma_hash       = sig["firma_hash"],
            firma_hash_short = HashService.short_hash(sig["firma_hash"]),
            fecha            = sig["fecha"],
            hora             = sig["hora"],
            timestamp_utc    = sig.get("timestamp_utc", ""),
        )
