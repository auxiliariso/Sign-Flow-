"""
Servicio API REST - FastAPI
Permite que otros sistemas gestionen firmas en segundo plano.
Endpoints:
  POST   /auth/login
  POST   /users/register
  POST   /sign
  GET    /signatures
  GET    /signatures/{id_user}
  GET    /signatures/hash/{hash}
  GET    /health
"""
import os
import tempfile
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from infrastructure.database.db_manager import (
    DatabaseManager, SQLiteUserRepository, SQLiteSignatureRepository
)
from infrastructure.document_handlers.dispatcher import DocumentSignerDispatcher
from core.usecases.sign_usecases import (
    AuthenticateUser, RegisterUser, GenerateSignature, ListSignatureHistory
)

app = FastAPI(
    title="SignFlow API",
    description="API de firma digital para documentos Office y PDF",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Modelos Pydantic ──────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    nombre_completo: str
    password: str

class RegisterRequest(BaseModel):
    nombre_completo: str
    nombre_puesto: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    id_user: Optional[int] = None
    nombre_completo: Optional[str] = None
    nombre_puesto: Optional[str] = None
    message: str = ""

# ── Estado global (inyectado al arrancar) ─────────────────────────────────────

_db: Optional[DatabaseManager] = None


def get_db() -> DatabaseManager:
    if _db is None:
        raise HTTPException(500, "Base de datos no inicializada")
    return _db


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "SignFlow API"}


@app.post("/auth/login", response_model=LoginResponse)
def login(body: LoginRequest, db: DatabaseManager = Depends(get_db)):
    repo = SQLiteUserRepository(db)
    uc   = AuthenticateUser(repo)
    ok, user = uc.execute(body.nombre_completo, body.password)
    if not ok:
        raise HTTPException(401, "Credenciales incorrectas")
    return LoginResponse(
        success=True,
        id_user=user.id_user,
        nombre_completo=user.nombre_completo,
        nombre_puesto=user.nombre_puesto,
    )


@app.post("/users/register")
def register(body: RegisterRequest, db: DatabaseManager = Depends(get_db)):
    repo = SQLiteUserRepository(db)
    uc   = RegisterUser(repo)
    try:
        user = uc.execute(body.nombre_completo, body.nombre_puesto, body.password)
    except ValueError as e:
        raise HTTPException(409, str(e))
    return {"id_user": user.id_user, "nombre_completo": user.nombre_completo}


@app.post("/sign")
async def sign_document(
    id_user: int = Form(...),
    file: UploadFile = File(...),
    db: DatabaseManager = Depends(get_db),
):
    user_repo = SQLiteUserRepository(db)
    user = user_repo.get_by_id(id_user)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    suffix = "." + file.filename.rsplit(".", 1)[-1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_in:
        tmp_in.write(await file.read())
        tmp_in_path = tmp_in.name

    tmp_out_path = tmp_in_path.replace(suffix, f"_firmado{suffix}")

    try:
        sig_repo  = SQLiteSignatureRepository(db)
        dispatcher = DocumentSignerDispatcher()
        uc = GenerateSignature(sig_repo, dispatcher)
        record = uc.execute(user, tmp_in_path, tmp_out_path)
    except ValueError as e:
        raise HTTPException(400, str(e))
    finally:
        os.unlink(tmp_in_path)

    return record.to_dict()


@app.get("/signatures")
def list_signatures(db: DatabaseManager = Depends(get_db)):
    repo = SQLiteSignatureRepository(db)
    uc   = ListSignatureHistory(repo)
    return [r.to_dict() for r in uc.execute()]


@app.get("/signatures/user/{id_user}")
def list_by_user(id_user: int, db: DatabaseManager = Depends(get_db)):
    repo = SQLiteSignatureRepository(db)
    uc   = ListSignatureHistory(repo)
    return [r.to_dict() for r in uc.execute(id_user=id_user)]


@app.get("/signatures/hash/{hash_val}")
def get_by_hash(hash_val: str, db: DatabaseManager = Depends(get_db)):
    repo   = SQLiteSignatureRepository(db)
    record = repo.get_by_hash(hash_val)
    if not record:
        raise HTTPException(404, "Hash no encontrado")
    return record.to_dict()


# ── Arranque ──────────────────────────────────────────────────────────────────

def start_api_service(host: str, port: int, db: DatabaseManager):
    global _db
    _db = db
    uvicorn.run(app, host=host, port=port, log_level="info")
