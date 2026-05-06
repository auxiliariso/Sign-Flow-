"""
Tests unitarios para SignFlow
Ejecutar: python -m pytest tests/ -v
"""
import os
import tempfile
import pytest
from infrastructure.database.db_manager import (
    DatabaseManager, SQLiteUserRepository, SQLiteSignatureRepository
)
from core.usecases.sign_usecases import (
    AuthenticateUser, RegisterUser, ListSignatureHistory, _hash_password
)
from core.entities.signature import SignatureRecord


@pytest.fixture
def db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    db = DatabaseManager(db_path=path)
    db.initialize()
    yield db
    os.unlink(path)


@pytest.fixture
def user_repo(db):
    return SQLiteUserRepository(db)


@pytest.fixture
def sig_repo(db):
    return SQLiteSignatureRepository(db)


def test_register_and_authenticate(user_repo):
    uc_reg  = RegisterUser(user_repo)
    uc_auth = AuthenticateUser(user_repo)

    user = uc_reg.execute("Juan Pérez", "Gerente", "secret123")
    assert user.id_user is not None

    ok, u = uc_auth.execute("Juan Pérez", "secret123")
    assert ok
    assert u.nombre_puesto == "Gerente"

    fail, _ = uc_auth.execute("Juan Pérez", "wrong")
    assert not fail


def test_duplicate_user_raises(user_repo):
    uc = RegisterUser(user_repo)
    uc.execute("Ana García", "Analista", "pass")
    with pytest.raises(ValueError):
        uc.execute("Ana García", "Directora", "pass")


def test_save_and_list_signature(sig_repo):
    record = SignatureRecord(
        id_user=1,
        nombre_completo="Test User",
        nombre_puesto="Dev",
        firma_hash="abc" * 20,
        documento_path="/tmp/doc.docx",
        tipo_documento="docx",
        fecha="2025-01-01",
        hora="10:00:00",
    )
    saved = sig_repo.save(record)
    assert saved.id_firma is not None

    results = sig_repo.get_by_user(1)
    assert len(results) == 1
    assert results[0].firma_hash == record.firma_hash


def test_list_all_signatures(sig_repo):
    for i in range(3):
        sig_repo.save(SignatureRecord(
            id_user=i+1, nombre_completo=f"User {i}",
            nombre_puesto="Dev", firma_hash=f"hash{i}" * 12,
            documento_path=f"/tmp/doc{i}.pdf", tipo_documento="pdf",
            fecha="2025-01-01", hora="00:00:00",
        ))
    all_sigs = sig_repo.get_all()
    assert len(all_sigs) == 3
