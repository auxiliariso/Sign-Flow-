"""
SignFlow v2 — Plataforma Empresarial de Firma Digital
=====================================================
Punto de entrada unificado.

Modos:
  gui     → Interfaz gráfica Tkinter
  api     → Servicio REST FastAPI en segundo plano
  both    → GUI + API simultáneos
  verify  → Verificar integridad de un documento

Ejemplos:
  python main.py
  python main.py --mode api --port 8765
  python main.py --mode both
  python main.py --verify contrato.docx
"""
import sys
import argparse
import threading

from database.db_manager import DatabaseManager


def main():
    parser = argparse.ArgumentParser(
        prog="signflow",
        description="SignFlow v2 — Firma Digital Empresarial",
    )
    parser.add_argument("--mode", choices=["gui", "api", "both"],
                        default="gui")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--db-path", default="signflow.db")
    parser.add_argument("--verify", metavar="ARCHIVO",
                        help="Verificar integridad de un documento")
    args = parser.parse_args()

    # ── Modo verificación CLI ────────────────────────────────────────────────
    if args.verify:
        _run_verify(args.verify, args.db_path)
        return

    # ── Inicializar BD ───────────────────────────────────────────────────────
    db = DatabaseManager(db_path=args.db_path)
    db.initialize()

    if args.mode == "api":
        _start_api(args.host, args.port, db)

    elif args.mode == "both":
        t = threading.Thread(
            target=_start_api, args=(args.host, args.port, db), daemon=True
        )
        t.start()
        _start_gui(db)

    else:
        _start_gui(db)


def _start_gui(db):
    from presentation.gui.app import SignFlowApp
    SignFlowApp(db=db).run()


def _start_api(host, port, db):
    from api.server import create_app
    import uvicorn
    app = create_app(db)
    uvicorn.run(app, host=host, port=port, log_level="info")


def _run_verify(filepath: str, db_path: str):
    from database.db_manager import DatabaseManager
    from core.verification_service import VerificationService
    db = DatabaseManager(db_path=db_path)
    db.initialize()
    svc = VerificationService(db)
    result = svc.verify_file(filepath)
    print(result.format_cli())


if __name__ == "__main__":
    main()
