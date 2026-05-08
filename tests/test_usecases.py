"""
Tests unitarios para SignFlow v2
Ejecutar: python -m pytest tests/ -v
"""
import os
import tempfile
import pytest
from database.db_manager import DatabaseManager
from core.usecases.sign_usecases import AuthenticateUser, RegisterUser
from core.entities.signature import SignatureRecord


@pytest.fixture
def db():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    path = tmp.name
    tmp.close()
    db = DatabaseManager(db_path=path)
    db.initialize()
    yield db
    db.close_all()
    try:
        os.unlink(path)
    except PermissionError:
        pass


@pytest.fixture
def user_repo(db):
    return db.user_repo


@pytest.fixture
def sig_repo(db):
    return db.sig_repo


# ── Auth ──────────────────────────────────────────────────────────────────────

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


# ── Firmas ────────────────────────────────────────────────────────────────────

def test_save_and_list_signature(sig_repo):
    record = SignatureRecord(
        id_user=1,
        nombre_completo="Test User",
        nombre_puesto="Dev",
        firma_hash="abc" * 21,
        documento_path="/tmp/doc.docx",
        tipo_documento="docx",
        fecha="2025-01-01",
        hora="10:00:00",
    )
    saved = sig_repo.save(record)
    assert saved.id_firma is not None

    results = sig_repo.get_by_user(1)
    assert len(results) == 1
    # get_by_user devuelve list[dict] — acceder con ["clave"], no .atributo
    assert results[0]["firma_hash"] == record.firma_hash


def test_list_all_signatures(sig_repo):
    for i in range(3):
        sig_repo.save(SignatureRecord(
            id_user=i + 1,
            nombre_completo=f"User {i}",
            nombre_puesto="Dev",
            firma_hash=f"{'a' * 60}{i}",
            documento_path=f"/tmp/doc{i}.pdf",
            tipo_documento="pdf",
            fecha="2025-01-01",
            hora="00:00:00",
        ))
    assert len(sig_repo.get_all()) == 3


def test_hash_short_format():
    from core.hash_service import HashService
    full  = "a4b7d5f9" * 8   # 64 chars
    short = HashService.short_hash(full, chars=4)
    assert "…" in short
    assert len(short) < 20


def test_timestamp_is_local():
    from core.hash_service import HashService
    import datetime
    ts   = HashService.now_local()
    dt   = datetime.datetime.fromisoformat(ts)
    diff = abs((datetime.datetime.now() - dt).total_seconds())
    assert diff < 5