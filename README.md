# SignFlow — Sistema de Firma Digital

> Genera firmas digitales trazables en documentos **Word, Excel, PowerPoint y PDF**,
> con login de usuario, registro auditado en SQLite y API REST para integración con otros sistemas.

---

## Requisitos
- Python 3.10+
- pip

## Instalación

```bash
git clone <repo>
cd signflow
pip install -r requirements.txt
```

## Ejecución

| Modo | Comando |
|------|---------|
| Interfaz gráfica (default) | `python main.py` |
| Solo API REST | `python main.py --mode api --port 8765` |
| GUI + API simultáneos | `python main.py --mode both` |

## Compilar ejecutable .exe

```bash
# .exe único (recomendado para distribución)
python build_construct.py

# Carpeta (más rápido en inicio)
python build_construct.py --onedir

# Con consola para debug
python build_construct.py --debug
```

El ejecutable queda en `dist/SignFlow.exe`.

## API REST — Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado del servicio |
| POST | `/auth/login` | Autenticar usuario |
| POST | `/users/register` | Registrar usuario |
| POST | `/sign` | Firmar un documento (multipart) |
| GET | `/signatures` | Listar todas las firmas |
| GET | `/signatures/user/{id}` | Firmas de un usuario |
| GET | `/signatures/hash/{hash}` | Verificar por hash |

Documentación interactiva: `http://localhost:8765/docs`

## Tipos de documento soportados

| Extensión | Handler | Ubicación de la firma |
|-----------|---------|----------------------|
| `.docx` / `.doc` | `DocxSigner` | Bloque al final del documento |
| `.xlsx` / `.xls` | `XlsxSigner` | Nueva hoja "Firma Digital" |
| `.pptx` / `.ppt` | `PptxSigner` | Nueva diapositiva al final |
| `.pdf` | `PdfSigner` | Nueva página de firma |

## Base de datos (SQLite — auto-generada)

### Tabla `users`
| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id_user` | INTEGER PK | ID auto-incremental |
| `nombre_completo` | TEXT | Nombre del usuario |
| `nombre_puesto` | TEXT | Cargo |
| `password_hash` | TEXT | SHA-256 de la contraseña |
| `activo` | INTEGER | 1 = activo |
| `created_at` | TEXT | Fecha/hora de creación |

### Tabla `signatures`
| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id_firma` | INTEGER PK | ID auto-incremental |
| `id_user` | INTEGER FK | Referencia al usuario |
| `nombre_completo` | TEXT | Nombre al momento de firmar |
| `nombre_puesto` | TEXT | Cargo al momento de firmar |
| `firma_hash` | TEXT UNIQUE | SHA-256 trazable de la firma |
| `documento_path` | TEXT | Ruta del documento firmado |
| `tipo_documento` | TEXT | docx / xlsx / pptx / pdf |
| `hora` | TEXT | HH:MM:SS (UTC) |
| `fecha` | TEXT | YYYY-MM-DD (UTC) |

## Ejecutar tests

```bash
pip install pytest
python -m pytest tests/ -v
```
