"""
presentation/gui/app.py  (v2.5)
================================
Pantallas:
  Login / Registro
  Dashboard:
    · Firmar documento
    · Plantillas (formatos con placeholders)
    · Historial
    · Verificar
    · Administración (CRUD usuarios — editar nombre, puesto, desactivar)
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
from typing import Optional

from core.usecases.sign_usecases import AuthenticateUser, RegisterUser
from core.entities.user import User

C = {
    "navy":    "#1F3864", "mid":    "#2E5090", "blue":   "#4A7FC1",
    "light":   "#D6E4F0", "pale":   "#F0F4FA", "white":  "#FFFFFF",
    "dark":    "#1A1A2E", "grey":   "#6B7A99",
    "success": "#1E6B3C", "error":  "#A01E1E",
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
        self._root.geometry("980x660")
        self._root.minsize(860, 580)
        self._root.configure(bg=C["pale"])
        self._apply_styles()
        self._container = ttk.Frame(self._root)
        self._container.pack(fill="both", expand=True)
        self._show_login()

    def run(self):
        self._root.mainloop()

    # ── Estilos ───────────────────────────────────────────────────────────────
    def _apply_styles(self):
        s = ttk.Style(self._root)
        s.theme_use("clam")
        s.configure("TFrame",        background=C["pale"])
        s.configure("TLabel",        background=C["pale"], foreground=C["dark"], font=FONT)
        s.configure("Card.TLabel",   background=C["white"], foreground=C["dark"], font=FONT)
        s.configure("Primary.TButton", background=C["navy"], foreground=C["white"],
                    font=FONT_BOLD, relief="flat", padding=(16, 8))
        s.map("Primary.TButton", background=[("active", C["mid"])])
        s.configure("Ghost.TButton", background=C["light"], foreground=C["navy"],
                    font=FONT_BOLD, relief="flat", padding=(16, 8))
        s.map("Ghost.TButton", background=[("active", C["pale"])])
        s.configure("Danger.TButton", background="#A01E1E", foreground=C["white"],
                    font=FONT_BOLD, relief="flat", padding=(10, 6))
        s.map("Danger.TButton", background=[("active", "#7A1616")])
        s.configure("Treeview", background=C["white"], fieldbackground=C["white"],
                    foreground=C["dark"], font=FONT, rowheight=26)
        s.configure("Treeview.Heading", background=C["navy"], foreground=C["white"],
                    font=FONT_BOLD, relief="flat")
        s.map("Treeview", background=[("selected", C["light"])],
              foreground=[("selected", C["navy"])])

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _clear(self):
        for w in self._container.winfo_children():
            w.destroy()

    def _header(self, parent, subtitle=""):
        hf = tk.Frame(parent, bg=C["navy"])
        hf.pack(fill="x")
        tk.Label(hf, text="✦  SignFlow", bg=C["navy"], fg=C["white"],
                 font=("Segoe UI", 14, "bold"), padx=20, pady=12).pack(side="left")
        if subtitle:
            tk.Label(hf, text=subtitle, bg=C["navy"], fg=C["light"],
                     font=FONT_SM, padx=20, pady=12).pack(side="right")

    def _card(self, parent, **kw):
        f = tk.Frame(parent, bg=C["white"],
                     highlightbackground=C["light"], highlightthickness=1)
        f.pack(**kw)
        return f

    def _entry(self, parent, row, label, secret=False, width=32):
        tk.Label(parent, text=label, bg=C["white"], fg=C["grey"],
                 font=FONT_SM).grid(row=row*2, column=0, columnspan=2,
                                    sticky="w", pady=(8, 0), padx=4)
        e = tk.Entry(parent, font=FONT, width=width, bg=C["pale"],
                     fg=C["dark"], relief="flat", bd=4,
                     show="●" if secret else "")
        e.grid(row=row*2+1, column=0, columnspan=2,
               sticky="ew", padx=4, pady=(2, 0))
        return e

    # ── LOGIN ─────────────────────────────────────────────────────────────────
    def _show_login(self):
        self._clear()
        self._header(self._container)
        body = ttk.Frame(self._container)
        body.pack(expand=True)
        card = self._card(body, padx=0, pady=40, ipadx=36, ipady=28)
        tk.Label(card, text="Iniciar sesión", bg=C["white"], fg=C["navy"],
                 font=FONT_LG).grid(row=0, column=0, columnspan=2,
                                    sticky="w", padx=4, pady=(0, 4))
        self._ln = self._entry(card, 1, "Nombre completo")
        self._lp = self._entry(card, 2, "Contraseña", secret=True)
        self._lmsg = tk.Label(card, text="", bg=C["white"],
                              fg=C["error"], font=FONT_SM)
        self._lmsg.grid(row=6, column=0, columnspan=2,
                        sticky="w", padx=4, pady=(6, 0))
        bf = tk.Frame(card, bg=C["white"])
        bf.grid(row=7, column=0, columnspan=2, sticky="ew",
                pady=(12, 0), padx=4)
        ttk.Button(bf, text="Entrar →", style="Primary.TButton",
                   command=self._do_login).pack(side="left")
        ttk.Button(bf, text="Registrarse", style="Ghost.TButton",
                   command=self._show_register).pack(side="left", padx=(8, 0))
        self._ln.bind("<Return>", lambda _: self._do_login())
        self._lp.bind("<Return>", lambda _: self._do_login())
        self._ln.focus()

    def _do_login(self):
        nombre = self._ln.get().strip()
        pwd    = self._lp.get()
        if not nombre or not pwd:
            self._lmsg.config(text="Completa todos los campos.")
            return
        ok, user = AuthenticateUser(self._db.user_repo).execute(nombre, pwd)
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
        tk.Label(card, text="Nuevo usuario", bg=C["white"], fg=C["navy"],
                 font=FONT_LG).grid(row=0, column=0, columnspan=2,
                                    sticky="w", padx=4, pady=(0, 4))
        self._rn  = self._entry(card, 1, "Nombre completo")
        self._rp0 = self._entry(card, 2, "Cargo / Puesto")
        self._rp1 = self._entry(card, 3, "Contraseña", secret=True)
        self._rmsg = tk.Label(card, text="", bg=C["white"],
                              fg=C["error"], font=FONT_SM)
        self._rmsg.grid(row=8, column=0, columnspan=2,
                        sticky="w", padx=4, pady=(6, 0))
        bf = tk.Frame(card, bg=C["white"])
        bf.grid(row=9, column=0, columnspan=2, sticky="ew",
                pady=(12, 0), padx=4)
        ttk.Button(bf, text="Crear cuenta", style="Primary.TButton",
                   command=self._do_register).pack(side="left")
        ttk.Button(bf, text="← Volver", style="Ghost.TButton",
                   command=self._show_login).pack(side="left", padx=(8, 0))

    def _do_register(self):
        nombre = self._rn.get().strip()
        puesto = self._rp0.get().strip()
        pwd    = self._rp1.get()
        if not all([nombre, puesto, pwd]):
            self._rmsg.config(text="Todos los campos son obligatorios.")
            return
        try:
            RegisterUser(self._db.user_repo).execute(nombre, puesto, pwd)
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

        tab_bar = tk.Frame(self._container, bg=C["navy"])
        tab_bar.pack(fill="x")
        content = ttk.Frame(self._container)
        content.pack(fill="both", expand=True, padx=20, pady=16)

        self._tabs     = {}
        self._tab_btns = {}

        def make_tab(key, label):
            frame = ttk.Frame(content)
            self._tabs[key] = frame
            btn = tk.Button(tab_bar, text=label, bg=C["navy"], fg=C["light"],
                            font=FONT_BOLD, relief="flat", bd=0,
                            activebackground=C["mid"], activeforeground=C["white"],
                            padx=14, pady=10,
                            command=lambda k=key: self._switch_tab(k))
            btn.pack(side="left")
            self._tab_btns[key] = btn

        make_tab("sign",      "✦  Firmar")
        make_tab("templates", "  Plantillas")
        make_tab("history",   "  Historial")
        make_tab("verify",    "  Verificar")
        make_tab("admin",     "  Usuarios")

        tk.Button(tab_bar, text="Cerrar sesión", bg=C["navy"], fg=C["grey"],
                  font=FONT_SM, relief="flat", bd=0,
                  activebackground=C["mid"], activeforeground=C["white"],
                  padx=12, pady=10, command=self._logout).pack(side="right")

        self._build_sign_tab(self._tabs["sign"])
        self._build_templates_tab(self._tabs["templates"])
        self._build_history_tab(self._tabs["history"])
        self._build_verify_tab(self._tabs["verify"])
        self._build_admin_tab(self._tabs["admin"])
        self._switch_tab("sign")

    def _switch_tab(self, key):
        for k, f in self._tabs.items():
            f.pack_forget()
            self._tab_btns[k].config(bg=C["navy"], fg=C["light"])
        self._tabs[key].pack(fill="both", expand=True)
        self._tab_btns[key].config(bg=C["mid"], fg=C["white"])
        if key == "history":
            self._refresh_history()
        if key == "admin":
            self._refresh_admin()
        if key == "templates":
            self._refresh_templates()

    # ── FIRMAR ────────────────────────────────────────────────────────────────
    def _build_sign_tab(self, parent):
        tk.Label(parent, text="Selecciona un documento para firmar",
                 bg=C["pale"], fg=C["grey"], font=FONT_SM).pack(anchor="w")
        r1 = tk.Frame(parent, bg=C["pale"])
        r1.pack(fill="x", pady=(6, 0))
        self._doc_var = tk.StringVar()
        tk.Entry(r1, textvariable=self._doc_var, font=FONT, bg=C["white"],
                 fg=C["dark"], relief="flat", bd=4, width=60).pack(
                     side="left", fill="x", expand=True)
        ttk.Button(r1, text="Examinar…", style="Ghost.TButton",
                   command=self._browse).pack(side="left", padx=(8, 0))
        self._file_info   = tk.Label(parent, text="", bg=C["pale"],
                                     fg=C["grey"], font=FONT_SM)
        self._file_info.pack(anchor="w", pady=(4, 0))
        ttk.Button(parent, text="✦  Firmar documento",
                   style="Primary.TButton",
                   command=self._do_sign).pack(anchor="w", pady=(14, 0))
        self._sign_result = tk.Label(parent, text="", bg=C["pale"],
                                     fg=C["success"], font=FONT_BOLD,
                                     wraplength=800, justify="left")
        self._sign_result.pack(anchor="w", pady=(10, 0))
        self._sign_detail = tk.Label(parent, text="", bg=C["pale"],
                                     fg=C["grey"], font=FONT_MONO,
                                     wraplength=800, justify="left")
        self._sign_detail.pack(anchor="w", pady=(2, 0))

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Seleccionar documento",
            filetypes=[("Documentos soportados",
                        "*.docx *.doc *.xlsx *.xls *.pptx *.ppt *.pdf"),
                       ("Todos los archivos", "*.*")])
        if path:
            self._doc_var.set(path)
            p = Path(path)
            self._file_info.config(
                text=f"Archivo: {p.name}   |   Tamaño: {p.stat().st_size//1024} KB"
                     f"   |   Tipo: {p.suffix.upper()}")
            self._sign_result.config(text="")
            self._sign_detail.config(text="")

    def _do_sign(self):
        doc_path = self._doc_var.get().strip()
        if not doc_path or not Path(doc_path).exists():
            messagebox.showwarning("Sin archivo", "Selecciona un documento válido.")
            return
        p = Path(doc_path)
        output_path = str(p.parent / (p.stem + "_firmado" + p.suffix))
        try:
            from core.document_service import DocumentService
            result = DocumentService(self._db).sign_document(
                doc_path, output_path, self._user)
            self._sign_result.config(fg=C["success"],
                                     text="✔  Documento firmado correctamente")
            self._sign_detail.config(
                text=f"ID de validación : {result.get('validation_id','—')}\n"
                     f"Guardado en      : {result.get('output_path', output_path)}\n"
                     f"Hash             : {result.get('firma_hash','')[:32]}…")
            self._refresh_history()
        except Exception as e:
            self._sign_result.config(fg=C["error"], text="✘  Error al firmar")
            self._sign_detail.config(text=str(e))

    # ── PLANTILLAS ────────────────────────────────────────────────────────────
    def _build_templates_tab(self, parent):
        top = tk.Frame(parent, bg=C["pale"])
        top.pack(fill="x", pady=(0, 10))
        tk.Label(top, text="Formatos configurados con placeholders",
                 bg=C["pale"], fg=C["grey"], font=FONT_SM).pack(side="left")
        ttk.Button(top, text="Aplicar placeholders al archivo…",
                   style="Primary.TButton",
                   command=self._aplicar_placeholders).pack(side="right")

        cols = ("formato_id", "nombre", "extension")
        self._tpl_tree = ttk.Treeview(parent, columns=cols,
                                       show="headings", height=6)
        for col, lbl, w in [("formato_id","Formato ID",160),
                             ("nombre","Nombre del formato",320),
                             ("extension","Extensión",90)]:
            self._tpl_tree.heading(col, text=lbl)
            self._tpl_tree.column(col, width=w, anchor="w")
        self._tpl_tree.pack(fill="x")

        # Detalle de placeholders
        tk.Label(parent, text="Placeholders disponibles en el formato seleccionado:",
                 bg=C["pale"], fg=C["grey"], font=FONT_SM).pack(
                     anchor="w", pady=(14, 2))
        self._ph_text = tk.Text(parent, height=8, font=FONT_MONO,
                                bg=C["white"], fg=C["dark"],
                                relief="flat", bd=4, state="disabled")
        self._ph_text.pack(fill="x")
        self._tpl_tree.bind("<<TreeviewSelect>>", self._on_template_select)

    def _refresh_templates(self):
        for r in self._tpl_tree.get_children():
            self._tpl_tree.delete(r)
        try:
            from core.template_service import TemplateService
            svc = TemplateService(self._db, self._user)
            for fmt in svc.listar_formatos():
                self._tpl_tree.insert("", "end", values=(
                    fmt["formato_id"], fmt["nombre_formato"], fmt["extension"]))
        except Exception as e:
            self._tpl_tree.insert("", "end", values=("—", str(e), "—"))

    def _on_template_select(self, _event=None):
        sel = self._tpl_tree.selection()
        if not sel:
            return
        fmt_id = self._tpl_tree.item(sel[0])["values"][0]
        try:
            from core.template_service import TemplateService
            svc    = TemplateService(self._db, self._user)
            config = svc.cargar_config(fmt_id)
            phs    = config.get("placeholders", {})
            lines  = []
            for ph, cfg in phs.items():
                lines.append(f"{ph}")
                lines.append(f"  → {cfg.get('descripcion','')}")
                lines.append(f"  → Fuente BD: {cfg.get('fuente_bd','')}"
                             f"  ·  Campo: {cfg.get('campo_bd','')}")
                lines.append("")
            text = "\n".join(lines) or "Sin placeholders definidos."
        except Exception as e:
            text = str(e)
        self._ph_text.config(state="normal")
        self._ph_text.delete("1.0", "end")
        self._ph_text.insert("end", text)
        self._ph_text.config(state="disabled")

    def _aplicar_placeholders(self):
        sel = self._tpl_tree.selection()
        if not sel:
            messagebox.showwarning("Selecciona un formato",
                                   "Selecciona un formato en la lista primero.")
            return
        fmt_id = self._tpl_tree.item(sel[0])["values"][0]
        path = filedialog.askopenfilename(
            title="Seleccionar documento al que aplicar placeholders",
            filetypes=[("Documentos Office", "*.xlsx *.docx *.pptx"),
                       ("Todos", "*.*")])
        if not path:
            return
        try:
            from core.template_service import TemplateService
            svc = TemplateService(self._db, self._user)
            ext = Path(path).suffix.lower()
            if ext in (".xlsx", ".xls"):
                n = svc.aplicar_a_xlsx(path, fmt_id)
            elif ext in (".docx", ".doc"):
                n = svc.aplicar_a_docx(path, fmt_id)
            else:
                messagebox.showwarning("Tipo no soportado",
                                       "Solo se soportan .xlsx y .docx por ahora.")
                return
            messagebox.showinfo("Placeholders aplicados",
                                f"Se reemplazaron {n} placeholder(s) en:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ── HISTORIAL ─────────────────────────────────────────────────────────────
    def _build_history_tab(self, parent):
        cols = ("id","validacion","fecha","hora","tipo","hash","archivo")
        self._tree = ttk.Treeview(parent, columns=cols,
                                   show="headings", selectmode="browse")
        for col, lbl, w in [("id","#",44),("validacion","ID Validación",120),
                             ("fecha","Fecha",88),("hora","Hora",72),
                             ("tipo","Tipo",52),("hash","Hash",140),
                             ("archivo","Documento",280)]:
            self._tree.heading(col, text=lbl)
            self._tree.column(col, width=w, anchor="w")
        sb = ttk.Scrollbar(parent, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._tree.tag_configure("even", background=C["pale"])
        self._tree.tag_configure("odd",  background=C["white"])

    def _refresh_history(self):
        for r in self._tree.get_children():
            self._tree.delete(r)
        from core.hash_service import HashService
        records = self._db.sig_repo.get_by_user(self._user.id_user)
        for i, r in enumerate(records):
            g = lambda k, d="": (r.get(k, d) if isinstance(r, dict)
                                 else getattr(r, k, d))
            tag = "even" if i % 2 == 0 else "odd"
            self._tree.insert("", "end", tags=(tag,), values=(
                g("id_firma", i+1),
                g("validation_id", "—"),
                g("fecha"), g("hora"),
                g("tipo_documento", "—"),
                HashService.medium_hash(g("firma_hash")),
                Path(g("documento_path","")).name or "—",
            ))

    # ── VERIFICAR ─────────────────────────────────────────────────────────────
    def _build_verify_tab(self, parent):
        tk.Label(parent, text="Verifica la integridad de un documento firmado",
                 bg=C["pale"], fg=C["grey"], font=FONT_SM).pack(anchor="w")
        r1 = tk.Frame(parent, bg=C["pale"])
        r1.pack(fill="x", pady=(6, 0))
        self._ver_var = tk.StringVar()
        tk.Entry(r1, textvariable=self._ver_var, font=FONT, bg=C["white"],
                 fg=C["dark"], relief="flat", bd=4, width=60).pack(
                     side="left", fill="x", expand=True)
        ttk.Button(r1, text="Examinar…", style="Ghost.TButton",
                   command=lambda: self._ver_var.set(
                       filedialog.askopenfilename(
                           filetypes=[("Documentos","*.docx *.xlsx *.pptx *.pdf"),
                                      ("Todos","*.*")])
                       or self._ver_var.get()
                   )).pack(side="left", padx=(8, 0))
        ttk.Button(parent, text="  Verificar",
                   style="Primary.TButton",
                   command=self._do_verify).pack(anchor="w", pady=(14, 0))
        self._ver_result = tk.Text(parent, height=14, font=FONT_MONO,
                                   bg=C["white"], fg=C["dark"],
                                   relief="flat", bd=4, state="disabled")
        self._ver_result.pack(anchor="w", pady=(10, 0), fill="x")

    def _do_verify(self):
        path = self._ver_var.get().strip()
        if not path:
            messagebox.showwarning("Sin archivo", "Selecciona un documento.")
            return
        from core.verification_service import VerificationService
        result = VerificationService(self._db).verify_file(path)
        self._ver_result.config(state="normal")
        self._ver_result.delete("1.0", "end")
        self._ver_result.insert("end", result.format_cli())
        self._ver_result.config(state="disabled")

    # ── ADMINISTRACIÓN DE USUARIOS (CRUD) ────────────────────────────────────
    def _build_admin_tab(self, parent):
        top = tk.Frame(parent, bg=C["pale"])
        top.pack(fill="x", pady=(0, 10))
        tk.Label(top, text="Gestión de usuarios registrados",
                 bg=C["pale"], fg=C["grey"], font=FONT_SM).pack(side="left")

        btn_frame = tk.Frame(top, bg=C["pale"])
        btn_frame.pack(side="right")
        ttk.Button(btn_frame, text="Editar nombre",
                   style="Ghost.TButton",
                   command=self._edit_nombre).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Editar puesto",
                   style="Ghost.TButton",
                   command=self._edit_puesto).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Desactivar",
                   style="Danger.TButton",
                   command=self._deactivate_user).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Activar",
                   style="Ghost.TButton",
                   command=self._activate_user).pack(side="left", padx=4)

        cols = ("id","nombre","puesto","activo","created_at")
        self._admin_tree = ttk.Treeview(parent, columns=cols,
                                         show="headings", selectmode="browse")
        for col, lbl, w in [("id","#",40),
                             ("nombre","Nombre completo",240),
                             ("puesto","Cargo / Puesto",200),
                             ("activo","Estado",70),
                             ("created_at","Creado",130)]:
            self._admin_tree.heading(col, text=lbl)
            self._admin_tree.column(col, width=w, anchor="w")
        sb = ttk.Scrollbar(parent, orient="vertical",
                           command=self._admin_tree.yview)
        self._admin_tree.configure(yscrollcommand=sb.set)
        self._admin_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._admin_tree.tag_configure("inactivo",
                                        background="#F5D5D5", foreground="#7A1616")
        self._admin_tree.tag_configure("activo",
                                        background=C["pale"], foreground=C["dark"])

    def _refresh_admin(self):
        for r in self._admin_tree.get_children():
            self._admin_tree.delete(r)
        for user in self._db.user_repo.list_all():
            estado = "Activo" if user.activo else "Inactivo"
            tag    = "activo" if user.activo else "inactivo"
            created = getattr(user, "created_at", "")
            if hasattr(created, "isoformat"):
                created = created.isoformat()[:10]
            elif isinstance(created, str):
                created = created[:10]
            self._admin_tree.insert("", "end", iid=str(user.id_user),
                                    tags=(tag,), values=(
                user.id_user, user.nombre_completo,
                user.nombre_puesto, estado, created,
            ))

    def _selected_user_id(self) -> Optional[int]:
        sel = self._admin_tree.selection()
        if not sel:
            messagebox.showwarning("Selecciona un usuario",
                                   "Haz clic en un usuario de la lista.")
            return None
        return int(sel[0])

    def _edit_nombre(self):
        id_user = self._selected_user_id()
        if id_user is None:
            return
        user = self._db.user_repo.get_by_id(id_user)
        nuevo = simpledialog.askstring(
            "Editar nombre completo",
            f"Nombre actual: {user.nombre_completo}\n\nNuevo nombre:",
            parent=self._root,
            initialvalue=user.nombre_completo,
        )
        if nuevo and nuevo.strip():
            try:
                ok = self._db.user_repo.update_nombre(id_user, nuevo.strip())
                if ok:
                    # Actualizar sesión si es el propio usuario
                    if self._user and self._user.id_user == id_user:
                        self._user.nombre_completo = nuevo.strip()
                    messagebox.showinfo("Actualizado",
                                        f"Nombre cambiado a:\n{nuevo.strip()}")
                    self._refresh_admin()
                else:
                    messagebox.showerror("Error", "No se encontró el usuario.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _edit_puesto(self):
        id_user = self._selected_user_id()
        if id_user is None:
            return
        user = self._db.user_repo.get_by_id(id_user)
        nuevo = simpledialog.askstring(
            "Editar cargo / puesto",
            f"Puesto actual: {user.nombre_puesto}\n\nNuevo puesto:",
            parent=self._root,
            initialvalue=user.nombre_puesto,
        )
        if nuevo and nuevo.strip():
            try:
                self._db.user_repo.update_puesto(id_user, nuevo.strip())
                if self._user and self._user.id_user == id_user:
                    self._user.nombre_puesto = nuevo.strip()
                messagebox.showinfo("Actualizado",
                                    f"Puesto cambiado a:\n{nuevo.strip()}")
                self._refresh_admin()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _deactivate_user(self):
        id_user = self._selected_user_id()
        if id_user is None:
            return
        if id_user == (self._user.id_user if self._user else -1):
            messagebox.showwarning("No permitido",
                                   "No puedes desactivar tu propia cuenta.")
            return
        if messagebox.askyesno("Confirmar",
                               "¿Desactivar este usuario?\n"
                               "Sus firmas se conservarán en el historial."):
            self._db.user_repo.deactivate(id_user)
            self._refresh_admin()

    def _activate_user(self):
        id_user = self._selected_user_id()
        if id_user is None:
            return
        self._db.user_repo.activate(id_user)
        self._refresh_admin()

    def _logout(self):
        self._user = None
        self._show_login()
