"""
presentation/gui/app.py
=======================
Interfaz gráfica principal de SignFlow v2.
Paleta corporativa basada en #1F3864.

Pantallas:
  - Login
  - Registro
  - Dashboard con pestañas:
      · Firmar documento
      · Historial de firmas
      · Verificar documento
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Optional

from core.usecases.sign_usecases import AuthenticateUser, RegisterUser
from core.entities.user import User

# ── Paleta ────────────────────────────────────────────────────────────────────
C = {
    "navy":     "#1F3864",
    "mid":      "#2E5090",
    "blue":     "#4A7FC1",
    "light":    "#D6E4F0",
    "pale":     "#F0F4FA",
    "white":    "#FFFFFF",
    "dark":     "#1A1A2E",
    "grey":     "#6B7A99",
    "success":  "#1E6B3C",
    "error":    "#A01E1E",
}

FONT      = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_LG   = ("Segoe UI", 13, "bold")
FONT_SM   = ("Segoe UI", 9)
FONT_MONO = ("Consolas", 8)


class SignFlowApp:

    def __init__(self, db):
        self._db   = db
        self._user: Optional[User] = None

        self._root = tk.Tk()
        self._root.title("SignFlow v2 — Firma Digital Empresarial")
        self._root.geometry("920x640")
        self._root.minsize(800, 560)
        self._root.configure(bg=C["pale"])

        self._apply_styles()

        self._container = ttk.Frame(self._root)
        self._container.pack(fill="both", expand=True)

        self._show_login()

    def run(self):
        self._root.mainloop()

    # ── Estilos TTK ──────────────────────────────────────────────────────────

    def _apply_styles(self):
        s = ttk.Style(self._root)
        s.theme_use("clam")

        s.configure("TFrame",         background=C["pale"])
        s.configure("White.TFrame",   background=C["white"])
        s.configure("Navy.TFrame",    background=C["navy"])

        s.configure("TLabel",         background=C["pale"],
                    foreground=C["dark"], font=FONT)
        s.configure("Navy.TLabel",    background=C["navy"],
                    foreground=C["white"], font=FONT_LG)
        s.configure("Sub.TLabel",     background=C["pale"],
                    foreground=C["grey"], font=FONT_SM)
        s.configure("Card.TLabel",    background=C["white"],
                    foreground=C["dark"], font=FONT)
        s.configure("Err.TLabel",     background=C["white"],
                    foreground=C["error"], font=FONT_SM)
        s.configure("OK.TLabel",      background=C["pale"],
                    foreground=C["success"], font=FONT_BOLD)

        s.configure("Primary.TButton",
                    background=C["navy"], foreground=C["white"],
                    font=FONT_BOLD, relief="flat", padding=(16, 8))
        s.map("Primary.TButton",
              background=[("active", C["mid"]), ("pressed", C["blue"])])

        s.configure("Ghost.TButton",
                    background=C["light"], foreground=C["navy"],
                    font=FONT_BOLD, relief="flat", padding=(16, 8))
        s.map("Ghost.TButton",
              background=[("active", C["pale"])])

        s.configure("Treeview",
                    background=C["white"], fieldbackground=C["white"],
                    foreground=C["dark"], font=FONT, rowheight=26)
        s.configure("Treeview.Heading",
                    background=C["navy"], foreground=C["white"],
                    font=FONT_BOLD, relief="flat")
        s.map("Treeview",
              background=[("selected", C["light"])],
              foreground=[("selected", C["navy"])])

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _clear(self):
        for w in self._container.winfo_children():
            w.destroy()

    def _header(self, parent, subtitle: str = ""):
        hf = tk.Frame(parent, bg=C["navy"])
        hf.pack(fill="x")
        tk.Label(hf, text="✦  SignFlow",
                 bg=C["navy"], fg=C["white"],
                 font=("Segoe UI", 14, "bold"),
                 padx=20, pady=12).pack(side="left")
        if subtitle:
            tk.Label(hf, text=subtitle,
                     bg=C["navy"], fg=C["light"],
                     font=FONT_SM, padx=20, pady=12).pack(side="right")

    def _card(self, parent, **pack_kw) -> tk.Frame:
        f = tk.Frame(parent, bg=C["white"],
                     highlightbackground=C["light"],
                     highlightthickness=1)
        f.pack(**pack_kw)
        return f

    def _entry(self, parent, row: int, label: str,
               secret=False, width=32) -> tk.Entry:
        tk.Label(parent, text=label, bg=C["white"],
                 fg=C["grey"], font=FONT_SM).grid(
                     row=row * 2, column=0, columnspan=2,
                     sticky="w", pady=(8, 0), padx=4)
        e = tk.Entry(parent, font=FONT, width=width,
                     bg=C["pale"], fg=C["dark"],
                     relief="flat", bd=4,
                     show="●" if secret else "")
        e.grid(row=row * 2 + 1, column=0, columnspan=2,
               sticky="ew", padx=4, pady=(2, 0))
        return e

    # ── LOGIN ─────────────────────────────────────────────────────────────────

    def _show_login(self):
        self._clear()
        self._header(self._container)

        body = ttk.Frame(self._container)
        body.pack(expand=True)

        card = self._card(body, padx=0, pady=40,
                          ipadx=36, ipady=28)

        tk.Label(card, text="Iniciar sesión",
                 bg=C["white"], fg=C["navy"],
                 font=FONT_LG).grid(
                     row=0, column=0, columnspan=2,
                     sticky="w", padx=4, pady=(0, 4))

        self._ln = self._entry(card, 1, "Nombre completo")
        self._lp = self._entry(card, 2, "Contraseña", secret=True)

        self._lmsg = tk.Label(card, text="",
                              bg=C["white"], fg=C["error"], font=FONT_SM)
        self._lmsg.grid(row=6, column=0, columnspan=2,
                        sticky="w", padx=4, pady=(6, 0))

        btn_frame = tk.Frame(card, bg=C["white"])
        btn_frame.grid(row=7, column=0, columnspan=2,
                       sticky="ew", pady=(12, 0), padx=4)

        ttk.Button(btn_frame, text="Entrar →",
                   style="Primary.TButton",
                   command=self._do_login).pack(side="left")
        ttk.Button(btn_frame, text="Registrarse",
                   style="Ghost.TButton",
                   command=self._show_register).pack(side="left", padx=(8, 0))

        self._ln.bind("<Return>", lambda _: self._do_login())
        self._lp.bind("<Return>", lambda _: self._do_login())
        self._ln.focus()

    def _do_login(self):
        nombre   = self._ln.get().strip()
        password = self._lp.get()
        if not nombre or not password:
            self._lmsg.config(text="Completa todos los campos.")
            return
        uc = AuthenticateUser(self._db.user_repo)
        ok, user = uc.execute(nombre, password)
        if ok:
            self._user = user
            self._show_dashboard()
        else:
            self._lmsg.config(text="Nombre o contraseña incorrectos.")

    # ── REGISTRO ──────────────────────────────────────────────────────────────

    def _show_register(self):
        self._clear()
        self._header(self._container, "Registro de usuario")

        body = ttk.Frame(self._container)
        body.pack(expand=True)

        card = self._card(body, padx=0, pady=40, ipadx=36, ipady=28)

        tk.Label(card, text="Nuevo usuario",
                 bg=C["white"], fg=C["navy"],
                 font=FONT_LG).grid(
                     row=0, column=0, columnspan=2,
                     sticky="w", padx=4, pady=(0, 4))

        self._rn  = self._entry(card, 1, "Nombre completo")
        self._rp0 = self._entry(card, 2, "Cargo / Puesto")
        self._rp1 = self._entry(card, 3, "Contraseña", secret=True)

        self._rmsg = tk.Label(card, text="",
                              bg=C["white"], fg=C["error"], font=FONT_SM)
        self._rmsg.grid(row=8, column=0, columnspan=2,
                        sticky="w", padx=4, pady=(6, 0))

        btn_frame = tk.Frame(card, bg=C["white"])
        btn_frame.grid(row=9, column=0, columnspan=2,
                       sticky="ew", pady=(12, 0), padx=4)

        ttk.Button(btn_frame, text="Crear cuenta",
                   style="Primary.TButton",
                   command=self._do_register).pack(side="left")
        ttk.Button(btn_frame, text="← Volver",
                   style="Ghost.TButton",
                   command=self._show_login).pack(side="left", padx=(8, 0))

    def _do_register(self):
        nombre   = self._rn.get().strip()
        puesto   = self._rp0.get().strip()
        password = self._rp1.get()
        if not all([nombre, puesto, password]):
            self._rmsg.config(text="Todos los campos son obligatorios.")
            return
        uc = RegisterUser(self._db.user_repo)
        try:
            uc.execute(nombre, puesto, password)
            messagebox.showinfo("Registro exitoso",
                                f"Usuario '{nombre}' creado.\nYa puedes iniciar sesión.")
            self._show_login()
        except ValueError as e:
            self._rmsg.config(text=str(e))

    # ── DASHBOARD ─────────────────────────────────────────────────────────────

    def _show_dashboard(self):
        self._clear()
        u = self._user
        self._header(self._container,
                     f"{u.nombre_completo}  ·  {u.nombre_puesto}")

        # Tab bar
        tab_bar = tk.Frame(self._container, bg=C["navy"])
        tab_bar.pack(fill="x")

        content = ttk.Frame(self._container)
        content.pack(fill="both", expand=True, padx=20, pady=16)

        self._tabs = {}
        self._tab_btns = {}

        def make_tab(key, label):
            frame = ttk.Frame(content)
            self._tabs[key] = frame
            btn = tk.Button(
                tab_bar, text=label,
                bg=C["navy"], fg=C["light"],
                font=FONT_BOLD, relief="flat", bd=0,
                activebackground=C["mid"], activeforeground=C["white"],
                padx=18, pady=10,
                command=lambda k=key: self._switch_tab(k),
            )
            btn.pack(side="left")
            self._tab_btns[key] = btn

        make_tab("sign",    "✦  Firmar documento")
        make_tab("history", "  Historial")
        make_tab("verify",  "  Verificar")

        tk.Button(tab_bar, text="Cerrar sesión",
                  bg=C["navy"], fg=C["grey"],
                  font=FONT_SM, relief="flat", bd=0,
                  activebackground=C["mid"], activeforeground=C["white"],
                  padx=12, pady=10,
                  command=self._logout).pack(side="right")

        self._build_sign_tab(self._tabs["sign"])
        self._build_history_tab(self._tabs["history"])
        self._build_verify_tab(self._tabs["verify"])
        self._switch_tab("sign")

    def _switch_tab(self, key: str):
        for k, f in self._tabs.items():
            f.pack_forget()
            self._tab_btns[k].config(bg=C["navy"], fg=C["light"])
        self._tabs[key].pack(fill="both", expand=True)
        self._tab_btns[key].config(bg=C["mid"], fg=C["white"])
        if key == "history":
            self._refresh_history()

    # ── PESTAÑA: FIRMAR ───────────────────────────────────────────────────────

    def _build_sign_tab(self, parent):
        tk.Label(parent,
                 text="Selecciona un documento para firmar digitalmente",
                 bg=C["pale"], fg=C["grey"], font=FONT_SM).pack(anchor="w")

        row1 = tk.Frame(parent, bg=C["pale"])
        row1.pack(fill="x", pady=(6, 0))

        self._doc_var = tk.StringVar()
        tk.Entry(row1, textvariable=self._doc_var,
                 font=FONT, bg=C["white"], fg=C["dark"],
                 relief="flat", bd=4, width=58).pack(side="left",
                                                      fill="x", expand=True)

        ttk.Button(row1, text="Examinar…",
                   style="Ghost.TButton",
                   command=self._browse).pack(side="left", padx=(8, 0))

        self._file_info = tk.Label(parent, text="",
                                   bg=C["pale"], fg=C["grey"],
                                   font=FONT_SM)
        self._file_info.pack(anchor="w", pady=(4, 0))

        ttk.Button(parent, text="✦  Firmar documento",
                   style="Primary.TButton",
                   command=self._do_sign).pack(anchor="w", pady=(14, 0))

        self._sign_result = tk.Label(parent, text="",
                                     bg=C["pale"], fg=C["success"],
                                     font=FONT_BOLD, wraplength=760,
                                     justify="left")
        self._sign_result.pack(anchor="w", pady=(10, 0))

        # Detalle en mono
        self._sign_detail = tk.Label(parent, text="",
                                     bg=C["pale"], fg=C["grey"],
                                     font=FONT_MONO, wraplength=760,
                                     justify="left")
        self._sign_detail.pack(anchor="w", pady=(2, 0))

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Seleccionar documento",
            filetypes=[
                ("Documentos soportados",
                 "*.docx *.doc *.xlsx *.xls *.pptx *.ppt *.pdf"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if path:
            self._doc_var.set(path)
            p = Path(path)
            size_kb = p.stat().st_size // 1024
            self._file_info.config(
                text=f"Archivo: {p.name}   |   Tamaño: {size_kb} KB   |   Tipo: {p.suffix.upper()}"
            )
            self._sign_result.config(text="")
            self._sign_detail.config(text="")

    def _do_sign(self):
        doc_path = self._doc_var.get().strip()
        if not doc_path or not Path(doc_path).exists():
            messagebox.showwarning("Sin archivo",
                                   "Selecciona un documento válido.")
            return

        p = Path(doc_path)
        output_path = str(p.parent / (p.stem + "_firmado" + p.suffix))

        try:
            from core.document_service import DocumentService
            svc    = DocumentService(self._db)
            result = svc.sign_document(doc_path, output_path, self._user)

            self._sign_result.config(
                fg=C["success"],
                text=f"✔  Documento firmado correctamente",
            )
            self._sign_detail.config(
                text=(
                    f"ID de validación : {result.get('validation_id', '—')}\n"
                    f"Guardado en      : {result.get('output_path', output_path)}\n"
                    f"Hash             : {result.get('firma_hash', '')[:32]}…"
                )
            )
            self._refresh_history()

        except Exception as e:
            self._sign_result.config(fg=C["error"],
                                     text=f"✘  Error al firmar")
            self._sign_detail.config(text=str(e))

    # ── PESTAÑA: HISTORIAL ────────────────────────────────────────────────────

    def _build_history_tab(self, parent):
        cols = ("id", "validacion", "fecha", "hora", "tipo", "hash", "archivo")
        self._tree = ttk.Treeview(parent, columns=cols,
                                   show="headings", selectmode="browse")
        hdrs = {
            "id":        ("#",           44),
            "validacion":("ID Validación",120),
            "fecha":     ("Fecha",        88),
            "hora":      ("Hora",         72),
            "tipo":      ("Tipo",         52),
            "hash":      ("Hash",        140),
            "archivo":   ("Documento",   260),
        }
        for col, (lbl, w) in hdrs.items():
            self._tree.heading(col, text=lbl)
            self._tree.column(col, width=w, anchor="w")

        sb = ttk.Scrollbar(parent, orient="vertical",
                           command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Colores alternados
        self._tree.tag_configure("even", background=C["pale"])
        self._tree.tag_configure("odd",  background=C["white"])

    def _refresh_history(self):
        for row in self._tree.get_children():
            self._tree.delete(row)

        from core.hash_service import HashService
        records = self._db.sig_repo.get_by_user(self._user.id_user)

        for i, r in enumerate(records):
            firma_hash = r.get("firma_hash", "") if isinstance(r, dict) else getattr(r, "firma_hash", "")
            val_id     = r.get("validation_id", "—") if isinstance(r, dict) else "—"
            fecha      = r.get("fecha", "") if isinstance(r, dict) else getattr(r, "fecha", "")
            hora       = r.get("hora", "")  if isinstance(r, dict) else getattr(r, "hora", "")
            doc_path   = r.get("documento_path", "") or r.get("documento_path", "") if isinstance(r, dict) else ""
            tipo       = r.get("tipo_documento", "—") if isinstance(r, dict) else "—"
            id_firma   = r.get("id_firma", i+1) if isinstance(r, dict) else getattr(r, "id_firma", i+1)

            tag = "even" if i % 2 == 0 else "odd"
            self._tree.insert("", "end", tags=(tag,), values=(
                id_firma,
                val_id,
                fecha,
                hora,
                tipo,
                HashService.medium_hash(firma_hash),
                Path(doc_path).name if doc_path else "—",
            ))

    # ── PESTAÑA: VERIFICAR ────────────────────────────────────────────────────

    def _build_verify_tab(self, parent):
        tk.Label(parent,
                 text="Verifica la integridad y autenticidad de un documento firmado",
                 bg=C["pale"], fg=C["grey"], font=FONT_SM).pack(anchor="w")

        row1 = tk.Frame(parent, bg=C["pale"])
        row1.pack(fill="x", pady=(6, 0))

        self._ver_var = tk.StringVar()
        tk.Entry(row1, textvariable=self._ver_var,
                 font=FONT, bg=C["white"], fg=C["dark"],
                 relief="flat", bd=4, width=58).pack(side="left",
                                                      fill="x", expand=True)

        ttk.Button(row1, text="Examinar…",
                   style="Ghost.TButton",
                   command=self._browse_verify).pack(side="left", padx=(8, 0))

        ttk.Button(parent, text="  Verificar documento",
                   style="Primary.TButton",
                   command=self._do_verify).pack(anchor="w", pady=(14, 0))

        self._ver_result = tk.Text(
            parent, height=14, width=80,
            font=FONT_MONO, bg=C["white"], fg=C["dark"],
            relief="flat", bd=4, state="disabled",
        )
        self._ver_result.pack(anchor="w", pady=(10, 0), fill="x")

    def _browse_verify(self):
        path = filedialog.askopenfilename(
            title="Seleccionar documento a verificar",
            filetypes=[("Documentos", "*.docx *.xlsx *.pptx *.pdf"),
                       ("Todos", "*.*")],
        )
        if path:
            self._ver_var.set(path)

    def _do_verify(self):
        path = self._ver_var.get().strip()
        if not path:
            messagebox.showwarning("Sin archivo", "Selecciona un documento.")
            return
        from core.verification_service import VerificationService
        svc    = VerificationService(self._db)
        result = svc.verify_file(path)
        text   = result.format_cli()

        self._ver_result.config(state="normal")
        self._ver_result.delete("1.0", "end")
        self._ver_result.insert("end", text)
        self._ver_result.config(state="disabled")

    # ── Logout ────────────────────────────────────────────────────────────────

    def _logout(self):
        self._user = None
        self._show_login()