"""
SignFlow - Sistema de Firma Digital para Documentos Office y PDF
Punto de entrada principal
"""
import sys
import argparse
from presentation.gui.app import SignFlowApp
from services.api_service import start_api_service
from infrastructure.database.db_manager import DatabaseManager


def main():
    parser = argparse.ArgumentParser(
        description="SignFlow - Generador de Firmas Digitales",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modos de ejecución:
  gui       Interfaz gráfica (predeterminado)
  api       Servicio API en segundo plano
  both      GUI + API simultáneos
        """
    )
    parser.add_argument(
        "--mode", choices=["gui", "api", "both"],
        default="gui", help="Modo de ejecución"
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host para la API")
    parser.add_argument("--port", type=int, default=8765, help="Puerto para la API")
    parser.add_argument("--db-path", default="signflow.db", help="Ruta a la base de datos")

    args = parser.parse_args()

    # Inicializar base de datos
    db = DatabaseManager(db_path=args.db_path)
    db.initialize()

    if args.mode == "api":
        start_api_service(host=args.host, port=args.port, db=db)
    elif args.mode == "both":
        import threading
        api_thread = threading.Thread(
            target=start_api_service,
            args=(args.host, args.port, db),
            daemon=True
        )
        api_thread.start()
        app = SignFlowApp(db=db)
        app.run()
    else:
        app = SignFlowApp(db=db)
        app.run()


if __name__ == "__main__":
    main()
