"""
Presentación - Interfaz Gráfica Principal (Tkinter)
Paleta: #1F3864 (navy) · #2E5090 · #4A7FC1 · #D6E4F0 · #F0F4FA · blanco
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Optional

from infrastructure.database.db_manager import (
    DatabaseManager, SQLiteUserRepository, SQLiteSignatureRepository
)
from infrastructure.document_handlers.dispatcher import DocumentSignerDispatcher
from core.usecases.sign_usecases import (
    AuthenticateUser, RegisterUser, GenerateSignature, ListSignatureHistory
)
from core.entities.user import User

# ── Paleta ────────────────────────────────────────────────────────────────────
C = {
    "navy":      "#1F3864",
    "mid":       "#2E5090",
    "blue":      "#4A7FC1",
    "light_bg":  "#D6E4F0",
    "pale":      "#F0F4FA",
    "white":     "#FFFFFF",
    "text_dark": "#1A1A2E",
    "text_mid":  "#4A4A6A",
    "success":   "#2A7A4B",
    "error":     "#B0271A",
}

FONT      = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_LG   = ("Segoe UI", 13, "bold")
FONT_SM   = ("Segoe UI", 9)


class SignFlowApp:
    def __init__(self, db: DatabaseManager):
        self._db = db
        self._current_user: Optional[User] = None
        self._root = tk.Tk()
        self._build_root()
        self._show_login()

    def run(self):
        self._root.mainloop()

    # ── Setup ─────────────────────────────────────────────────────────────────

    def _build_root(self):
        self._root.title("SignFlow — Firma Digital")
        self._root.geometry("860x620")
        self._root.minsize(760, 540)
        self._root.configure(bg=C["pale"])
        self._root.resizable(True, True)

        # TTK styles
        style = ttk.Style(self._root)
        style.theme_use("clam")
        style.configure("TFrame", background=C["pale"])
        style.configure("Card.TFrame", background=C["white"],
                        relief="flat", borderwidth=1)
        style.configure("Header.TFrame", background=C["navy"])
        style.configure("TLabel", background=C["pale"],
                        foreground=C["text_dark"], font=FONT)
        style.configure("Header.TLabel", background=C["navy"],
                        foreground=C["white"], font=FONT_LG)
        style.configure("Sub.TLabel", background=C["pale"],
                        foreground=C["text_mid"], font=FONT_SM)
        style.configure("Card.TLabel", background=C["white"],
                        foreground=C["text_dark"], font=FONT)
        style.configure("Primary.TButton",
                        background=C["navy"], foreground=C["white"],
                        font=FONT_BOLD, relief="flat", padding=(14, 8))
        style.map("Primary.TButton",
                  background=[("active", C["mid"]), ("pressed", C["blue"])])
        style.configure("Secondary.TButton",
                        background=C["light_bg"], foreground=C["navy"],
                        font=FONT_BOLD, relief="flat", padding=(14, 8))
        style.configure("TEntry", fieldbackground=C["white"],
                        foreground=C["text_dark"], font=FONT, relief="flat")
        style.configure("Treeview", background=C["white"],
                        fieldbackground=C["white"], foreground=C["text_dark"],
                        font=FONT, rowheight=26)
        style.configure("Treeview.Heading",
                        background=C["navy"], foreground=C["white"],
                        font=FONT_BOLD, relief="flat")
        style.map("Treeview", background=[("selected", C["light_bg"])],
                  foreground=[("selected", C["navy"])])

        self._container = ttk.Frame(self._root)
        self._container.pack(fill="both", expand=True)

    def _clear(self):
        for w in self._container.winfo_children():
            w.destroy()

    # ── Header ────────────────────────────────────────────────────────────────

    def _add_header(self, parent, subtitle: str = ""):
        hf = ttk.Frame(parent, style="Header.TFrame")
        hf.pack(fill="x")
        ttk.Label(hf, text="✦  SignFlow", style="Header.TLabel",
                  padding=(20, 14, 0, 2)).pack(side="left")
        if subtitle:
            ttk.Label(hf, text=subtitle,
                      background=C["navy"], foreground=C["light_bg"],
                      font=FONT_SM, padding=(0, 14, 20, 2)).pack(side="right")

    # ── Login Screen ──────────────────────────────────────────────────────────

    def _show_login(self):
        self._clear()
        self._add_header(self._container)

        body = ttk.Frame(self._container)
        body.pack(expand=True)

        card = tk.Frame(body, bg=C["white"], bd=0,
                        highlightbackground=C["light_bg"], highlightthickness=1)
        card.pack(padx=40, pady=40, ipadx=30, ipady=28)

        tk.Label(card, text="Iniciar sesión", bg=C["white"],
                 fg=C["navy"], font=FONT_LG).grid(
                     row=0, column=0, columnspan=2, pady=(0, 18), sticky="w")

        for row, label in enumerate(["Nombre completo", "Contraseña"], start=1):
            tk.Label(card, text=label, bg=C["white"],
                     fg=C["text_mid"], font=FONT_SM).grid(
                         row=row*2-1, column=0, columnspan=2, sticky="w", pady=(4, 0))

        self._login_nombre = tk.Entry(card, font=FONT, width=34,
                                      bg=C["pale"], fg=C["text_dark"],
                                      relief="flat", bd=4)
        self._login_nombre.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        self._login_nombre.insert(0, "")

        self._login_pass = tk.Entry(card, font=FONT, width=34, show="●",
                                    bg=C["pale"], fg=C["text_dark"],
                                    relief="flat", bd=4)
        self._login_pass.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 14))

        self._login_msg = tk.Label(card, text="", bg=C["white"],
                                   fg=C["error"], font=FONT_SM)
        self._login_msg.grid(row=5, column=0, columnspan=2, sticky="w")

        ttk.Button(card, text="Entrar →", style="Primary.TButton",
                   command=self._do_login).grid(
                       row=6, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(card, text="Registrarse", style="Secondary.TButton",
                   command=self._show_register).grid(
                       row=6, column=1, sticky="ew", pady=(8, 0), padx=(8, 0))

        self._login_nombre.bind("<Return>", lambda _: self._do_login())
        self._login_pass.bind("<Return>", lambda _: self._do_login())
        self._login_nombre.focus()

    def _do_login(self):
        nombre = self._login_nombre.get().strip()
        password = self._login_pass.get()
        if not nombre or not password:
            self._login_msg.config(text="Completa todos los campos.")
            return
        repo = SQLiteUserRepository(self._db)
        uc   = AuthenticateUser(repo)
        ok, user = uc.execute(nombre, password)
        if ok:
            self._current_user = user
            self._show_dashboard()
        else:
            self._login_msg.config(text="Nombre o contraseña incorrectos.")

    # ── Register Screen ───────────────────────────────────────────────────────

    def _show_register(self):
        self._clear()
        self._add_header(self._container, "Registro de usuario")

        body = ttk.Frame(self._container)
        body.pack(expand=True)

        card = tk.Frame(body, bg=C["white"], bd=0,
                        highlightbackground=C["light_bg"], highlightthickness=1)
        card.pack(padx=40, pady=40, ipadx=30, ipady=28)

        tk.Label(card, text="Nuevo usuario", bg=C["white"],
                 fg=C["navy"], font=FONT_LG).grid(
                     row=0, column=0, columnspan=2, pady=(0, 18), sticky="w")

        fields_cfg = [
            ("Nombre completo", False),
            ("Cargo / Puesto", False),
            ("Contraseña", True),
        ]
        self._reg_entries = []
        for i, (label, secret) in enumerate(fields_cfg):
            tk.Label(card, text=label, bg=C["white"],
                     fg=C["text_mid"], font=FONT_SM).grid(
                         row=i*2+1, column=0, columnspan=2, sticky="w", pady=(4, 0))
            e = tk.Entry(card, font=FONT, width=34, bg=C["pale"],
                         fg=C["text_dark"], relief="flat", bd=4,
                         show="●" if secret else "")
            e.grid(row=i*2+2, column=0, columnspan=2, sticky="ew", pady=(0, 6))
            self._reg_entries.append(e)

        self._reg_msg = tk.Label(card, text="", bg=C["white"],
                                 fg=C["error"], font=FONT_SM)
        self._reg_msg.grid(row=7, column=0, columnspan=2, sticky="w")

        ttk.Button(card, text="Crear cuenta", style="Primary.TButton",
                   command=self._do_register).grid(row=8, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(card, text="← Volver", style="Secondary.TButton",
                   command=self._show_login).grid(
                       row=8, column=1, sticky="ew", pady=(8, 0), padx=(8, 0))

    def _do_register(self):
        nombre, puesto, password = [e.get().strip() for e in self._reg_entries]
        if not all([nombre, puesto, password]):
            self._reg_msg.config(text="Todos los campos son obligatorios.")
            return
        repo = SQLiteUserRepository(self._db)
        uc   = RegisterUser(repo)
        try:
            uc.execute(nombre, puesto, password)
            messagebox.showinfo("Registro exitoso",
                                f"Usuario '{nombre}' creado.\nYa puedes iniciar sesión.")
            self._show_login()
        except ValueError as e:
            self._reg_msg.config(text=str(e))

    # ── Dashboard ─────────────────────────────────────────────────────────────

    def _show_dashboard(self):
        self._clear()
        user = self._current_user
        self._add_header(self._container, f"{user.nombre_completo} · {user.nombre_puesto}")

        # Tab bar
        tab_bar = tk.Frame(self._container, bg=C["navy"], height=40)
        tab_bar.pack(fill="x")

        content = ttk.Frame(self._container)
        content.pack(fill="both", expand=True, padx=20, pady=16)

        self._tab_frames = {}
        self._tab_btns   = {}

        def make_tab(name: str, label: str):
            frame = ttk.Frame(content)
            self._tab_frames[name] = frame
            btn = tk.Button(
                tab_bar, text=label, bg=C["navy"], fg=C["light_bg"],
                font=FONT_BOLD, relief="flat", bd=0,
                activebackground=C["mid"], activeforeground=C["white"],
                padx=18, pady=10,
                command=lambda n=name: self._switch_tab(n),
            )
            btn.pack(side="left")
            self._tab_btns[name] = btn

        make_tab("sign",    "Firmar documento")
        make_tab("history", "Historial de firmas")

        # Logout
        tk.Button(tab_bar, text="Cerrar sesión", bg=C["navy"],
                  fg=C["light_bg"], font=FONT_SM, relief="flat", bd=0,
                  activebackground=C["mid"], activeforeground=C["white"],
                  padx=12, pady=10,
                  command=self._logout).pack(side="right")

        self._build_sign_tab(self._tab_frames["sign"])
        self._build_history_tab(self._tab_frames["history"])
        self._switch_tab("sign")

    def _switch_tab(self, name: str):
        for n, f in self._tab_frames.items():
            f.pack_forget()
            self._tab_btns[n].config(bg=C["navy"], fg=C["light_bg"])
        self._tab_frames[name].pack(fill="both", expand=True)
        self._tab_btns[name].config(bg=C["mid"], fg=C["white"])
        if name == "history":
            self._refresh_history()

    # ── Sign Tab ──────────────────────────────────────────────────────────────

    def _build_sign_tab(self, parent):
        tk.Label(parent, text="Selecciona un documento para firmar",
                 bg=C["pale"], fg=C["text_mid"], font=FONT_SM).pack(anchor="w")

        row1 = ttk.Frame(parent)
        row1.pack(fill="x", pady=(6, 0))

        self._doc_path_var = tk.StringVar()
        path_entry = tk.Entry(row1, textvariable=self._doc_path_var,
                              font=FONT, bg=C["white"], fg=C["text_dark"],
                              relief="flat", bd=4, width=56)
        path_entry.pack(side="left", fill="x", expand=True)

        ttk.Button(row1, text="Examinar…", style="Secondary.TButton",
                   command=self._browse_doc).pack(side="left", padx=(8, 0))

        self._sign_info = tk.Label(parent, text="", bg=C["pale"],
                                   fg=C["text_mid"], font=FONT_SM, wraplength=700,
                                   justify="left")
        self._sign_info.pack(anchor="w", pady=(6, 0))

        ttk.Button(parent, text="✦  Firmar documento", style="Primary.TButton",
                   command=self._do_sign).pack(anchor="w", pady=(14, 0))

        self._sign_result = tk.Label(parent, text="", bg=C["pale"],
                                     fg=C["success"], font=FONT_BOLD, wraplength=700,
                                     justify="left")
        self._sign_result.pack(anchor="w", pady=(10, 0))

    def _browse_doc(self):
        path = filedialog.askopenfilename(
            title="Seleccionar documento",
            filetypes=[
                ("Documentos Office / PDF",
                 "*.docx *.doc *.xlsx *.xls *.pptx *.ppt *.pdf"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if path:
            self._doc_path_var.set(path)
            self._sign_info.config(
                text=f"Archivo: {Path(path).name}  |  "
                     f"Tamaño: {Path(path).stat().st_size // 1024} KB"
            )
            self._sign_result.config(text="")

    def _do_sign(self):
        doc_path = self._doc_path_var.get().strip()
        if not doc_path or not Path(doc_path).exists():
            messagebox.showwarning("Sin archivo", "Selecciona un documento válido.")
            return

        p = Path(doc_path)
        output_path = str(p.parent / (p.stem + "_firmado" + p.suffix))

        sig_repo   = SQLiteSignatureRepository(self._db)
        dispatcher = DocumentSignerDispatcher()
        uc         = GenerateSignature(sig_repo, dispatcher)

        try:
            record = uc.execute(self._current_user, doc_path, output_path)
            self._sign_result.config(
                fg=C["success"],
                text=f"✔ Documento firmado con éxito\n"
                     f"Guardado en: {record.documento_path}\n"
                     f"Hash: {record.firma_hash[:32]}…"
            )
        except Exception as e:
            self._sign_result.config(fg=C["error"], text=f"✘ Error: {e}")

    # ── History Tab ───────────────────────────────────────────────────────────

    def _build_history_tab(self, parent):
        cols = ("id_firma", "fecha", "hora", "tipo", "hash", "documento")
        self._hist_tree = ttk.Treeview(parent, columns=cols,
                                        show="headings", selectmode="browse")
        headers = {
            "id_firma":  ("ID", 48),
            "fecha":     ("Fecha", 90),
            "hora":      ("Hora", 72),
            "tipo":      ("Tipo", 56),
            "hash":      ("Hash (primeros 24 chars)", 200),
            "documento": ("Documento", 260),
        }
        for col, (label, width) in headers.items():
            self._hist_tree.heading(col, text=label)
            self._hist_tree.column(col, width=width, anchor="w")

        scroll = ttk.Scrollbar(parent, orient="vertical",
                               command=self._hist_tree.yview)
        self._hist_tree.configure(yscrollcommand=scroll.set)
        self._hist_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _refresh_history(self):
        for row in self._hist_tree.get_children():
            self._hist_tree.delete(row)

        repo = SQLiteSignatureRepository(self._db)
        uc   = ListSignatureHistory(repo)
        records = uc.execute(id_user=self._current_user.id_user)

        for r in records:
            self._hist_tree.insert("", "end", values=(
                r.id_firma, r.fecha, r.hora, r.tipo_documento,
                r.firma_hash[:24] + "…",
                Path(r.documento_path).name,
            ))

    # ── Logout ────────────────────────────────────────────────────────────────

    def _logout(self):
        self._current_user = None
        self._show_login()
