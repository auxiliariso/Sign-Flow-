"""
build_construct.py
==================
Genera el ejecutable .exe de SignFlow usando PyInstaller.
Incluye todos los módulos, dependencias y recursos necesarios.

Uso:
    python build_construct.py
    python build_construct.py --onedir   # carpeta (más rápido en lanzamiento)
    python build_construct.py --debug    # con consola visible
"""
import sys
import os
import subprocess
import argparse
import shutil
from pathlib import Path

# ── Configuración ─────────────────────────────────────────────────────────────

APP_NAME        = "SignFlow"
ENTRY_SCRIPT    = "main.py"
ICON_PATH       = "presentation/assets/icon.ico"
VERSION         = "1.0.0"
DIST_DIR        = "dist"
BUILD_DIR       = "build"

HIDDEN_IMPORTS = [
    # FastAPI / uvicorn
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.off",
    "fastapi",
    "starlette",
    "pydantic",
    # Documentos
    "docx",
    "openpyxl",
    "pptx",
    "reportlab",
    "fitz",               # PyMuPDF
    # Base de datos
    "sqlite3",
    # Misc
    "tkinter",
    "tkinter.ttk",
    "tkinter.filedialog",
    "tkinter.messagebox",
]

DATA_FILES = [
    # (fuente, destino_dentro_del_exe)
    ("signflow.db", "."),          # BD SQLite (si existe)
    ("presentation/assets", "presentation/assets"),
]

EXCLUDES = [
    "matplotlib",
    "numpy",
    "pandas",
    "PIL",
    "IPython",
    "jupyter",
]


# ── Build ─────────────────────────────────────────────────────────────────────

def clean():
    for d in (DIST_DIR, BUILD_DIR):
        if Path(d).exists():
            shutil.rmtree(d)
            print(f"  Limpiado: {d}/")
    for f in Path(".").glob("*.spec"):
        f.unlink()
        print(f"  Eliminado: {f}")


def build(onedir: bool = False, debug: bool = False, clean_first: bool = True):
    if clean_first:
        print("\n[1/3] Limpiando builds anteriores…")
        clean()

    print("\n[2/3] Compilando con PyInstaller…")

    # Instalar PyInstaller si no está disponible
    try:
        import PyInstaller
    except ImportError:
        print("  PyInstaller no encontrado. Instalando…")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--distpath", DIST_DIR,
        "--workpath", BUILD_DIR,
        "--noconfirm",
        "--clean",
    ]

    # Modo
    if onedir:
        cmd.append("--onedir")
    else:
        cmd.append("--onefile")

    # Consola / ventana
    if debug:
        cmd.append("--console")
    else:
        cmd.append("--windowed")    # Sin consola en producción

    # Icono
    if Path(ICON_PATH).exists():
        cmd += ["--icon", ICON_PATH]

    # Hidden imports
    for hi in HIDDEN_IMPORTS:
        cmd += ["--hidden-import", hi]

    # Archivos de datos
    for src, dst in DATA_FILES:
        if Path(src).exists():
            sep = ";" if sys.platform == "win32" else ":"
            cmd += ["--add-data", f"{src}{sep}{dst}"]

    # Exclusiones
    for ex in EXCLUDES:
        cmd += ["--exclude-module", ex]

    # Metadata de versión (Windows)
    if sys.platform == "win32":
        _write_version_file()
        cmd += ["--version-file", "build_version.txt"]

    cmd.append(ENTRY_SCRIPT)

    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("\n❌ La compilación falló.")
        sys.exit(1)

    print("\n[3/3] Post-proceso…")
    exe_ext = ".exe" if sys.platform == "win32" else ""
    if onedir:
        out = Path(DIST_DIR) / APP_NAME
    else:
        out = Path(DIST_DIR) / f"{APP_NAME}{exe_ext}"

    print(f"\n✔ Ejecutable generado en: {out.resolve()}")
    return out


def _write_version_file():
    """Genera el archivo de versión para el manifiesto de Windows."""
    content = f"""\
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({VERSION.replace('.', ', ')}, 0),
    prodvers=({VERSION.replace('.', ', ')}, 0),
    mask=0x3f, flags=0x0, OS=0x4, fileType=0x1, subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable('040904B0', [
        StringStruct('CompanyName', 'SignFlow'),
        StringStruct('FileDescription', 'Generador de Firmas Digitales'),
        StringStruct('FileVersion', '{VERSION}'),
        StringStruct('ProductName', '{APP_NAME}'),
        StringStruct('ProductVersion', '{VERSION}'),
      ])
    ]),
    VarFileInfo([VarStruct('Translation', [0x0409, 1200])])
  ]
)
"""
    Path("build_version.txt").write_text(content)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compilar SignFlow a .exe")
    parser.add_argument("--onedir", action="store_true",
                        help="Compilar como carpeta en vez de .exe único")
    parser.add_argument("--debug", action="store_true",
                        help="Incluir consola para depuración")
    parser.add_argument("--no-clean", action="store_true",
                        help="No eliminar builds anteriores")
    args = parser.parse_args()

    print(f"╔══════════════════════════════════╗")
    print(f"║  SignFlow Build Construct v{VERSION}  ║")
    print(f"╚══════════════════════════════════╝")

    build(
        onedir=args.onedir,
        debug=args.debug,
        clean_first=not args.no_clean,
    )
