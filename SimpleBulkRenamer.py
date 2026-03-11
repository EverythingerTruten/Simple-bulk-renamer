"""
SBR — Simple Batch Renamer
Human-defined source + target pattern approach.
"""
import os, re, tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ── Palette ──────────────────────────────────────────────────────────────────
BG      = "#0d0d12"
PANEL   = "#13131a"
CARD    = "#1a1a24"
CARD2   = "#20202e"
BORDER  = "#2c2c3e"
ACCENT  = "#6c63ff"
ACCENT2 = "#ff6b9d"
TEXT    = "#e8e6f5"
MUTED   = "#5a5870"
SUCCESS = "#50fa7b"
WARNING = "#ffb86c"
ERROR   = "#ff5555"
DYN_CLR = "#ff6b9d"

MONO  = ("Courier New", 11)
MONO_S= ("Courier New", 10)
UI    = ("Segoe UI",    10)
UI_B  = ("Segoe UI",   10, "bold")
H1    = ("Segoe UI",   13, "bold")
SM    = ("Segoe UI",    9)

# ── Core logic ────────────────────────────────────────────────────────────────

def pattern_to_regex(pattern: str) -> tuple:
    """
    Convert  '[CBM]_{SHOW}_-_{EP}_-_{TITLE}_[720p]_[{HASH}].mkv'
    into a compiled regex and ordered list of variable names.
    """
    if not pattern.strip():
        raise ValueError("Pattern is empty.")
    var_names = []
    regex_parts = []
    tokens = re.split(r'(\{[^{}]+\})', pattern)
    for tok in tokens:
        m = re.fullmatch(r'\{([^{}]+)\}', tok)
        if m:
            name = m.group(1).strip()
            if not name:
                raise ValueError("Empty variable name {} found.")
            var_names.append(name)
            regex_parts.append("(.*?)")
        else:
            regex_parts.append(re.escape(tok))
    regex_str = "^" + "".join(regex_parts) + "$"
    try:
        compiled = re.compile(regex_str, re.DOTALL)
    except re.error as e:
        raise ValueError(f"Regex compile error: {e}")
    return compiled, var_names


def match_file(filename: str, regex, var_names: list) -> dict:
    m = regex.match(filename)
    if not m:
        return None
    return dict(zip(var_names, m.groups()))


def apply_int_transform(value: str, min_digits: int) -> str:
    try:
        return str(int(value)).zfill(min_digits)
    except ValueError:
        return value


def apply_str_transform(value: str, sep_from: str, sep_to: str, cap_mode: str) -> str:
    if sep_from:
        value = value.replace(sep_from, sep_to if sep_to is not None else sep_from)
    if cap_mode == "UPPER":
        value = value.upper()
    elif cap_mode == "lower":
        value = value.lower()
    elif cap_mode == "Title":
        sep = sep_to if sep_to else " "
        value = sep.join(w.capitalize() for w in value.split(sep))
    elif cap_mode == "Sentence":
        sep = sep_to if sep_to else " "
        parts = value.split(sep)
        value = sep.join(
            parts[i].capitalize() if i == 0 else parts[i].lower()
            for i in range(len(parts))
        )
    return value


def build_output(captures: dict, out_pattern: str, var_configs: dict) -> str:
    result = out_pattern
    for name, raw in captures.items():
        cfg = var_configs.get(name, {})
        if cfg.get("type") == "Integer":
            val = apply_int_transform(raw, cfg.get("min_digits", 1))
        else:
            val = apply_str_transform(
                raw,
                cfg.get("sep_from", ""),
                cfg.get("sep_to", ""),
                cfg.get("cap_mode", "Keep"),
            )
        result = result.replace("{" + name + "}", val)
    return result


# ── Widgets ───────────────────────────────────────────────────────────────────

def styled_entry(parent, textvariable=None, width=None, font=MONO):
    kw = dict(bg=PANEL, fg=TEXT, font=font,
              insertbackground=ACCENT, relief="flat",
              highlightthickness=1, highlightbackground=BORDER,
              highlightcolor=ACCENT, bd=4)
    if textvariable:
        kw["textvariable"] = textvariable
    if width:
        kw["width"] = width
    return tk.Entry(parent, **kw)


def styled_btn(parent, text, cmd, primary=False, small=False):
    bg  = ACCENT if primary else CARD2
    fnt = UI_B if primary else UI
    b = tk.Button(parent, text=text, command=cmd,
                  bg=bg, fg="white", font=fnt, relief="flat", bd=0,
                  cursor="hand2", activebackground=ACCENT2,
                  activeforeground="white",
                  padx=10 if small else 16, pady=5 if small else 7)
    b.bind("<Enter>", lambda e: b.config(bg=ACCENT2))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


def styled_combo(parent, var, values, width=12):
    s = ttk.Style()
    s.theme_use("default")
    s.configure("D.TCombobox",
                fieldbackground=CARD2,
                background=CARD2,
                foreground=TEXT,
                selectbackground=ACCENT,
                selectforeground="white",
                insertcolor=TEXT,
                arrowcolor=TEXT,
                arrowsize=12,
                borderwidth=1,
                relief="flat",
                lightcolor=BORDER,
                darkcolor=BORDER,
                bordercolor=BORDER,
                focuscolor=ACCENT)
    s.map("D.TCombobox",
          fieldbackground=[("readonly", CARD2), ("focus", CARD2)],
          foreground=[("readonly", TEXT), ("focus", TEXT)],
          background=[("readonly", CARD2), ("active", ACCENT2)],
          bordercolor=[("focus", ACCENT), ("!focus", BORDER)])
    cb = ttk.Combobox(parent, textvariable=var, values=values,
                      width=width, style="D.TCombobox", state="readonly")
    # Style the dropdown listbox when it opens
    cb.bind("<Map>", lambda e: _style_combo_popup(cb))
    return cb


def _style_combo_popup(cb):
    """Style the dropdown popup list when it appears."""
    try:
        popdown = cb.tk.eval(f"ttk::combobox::PopdownWindow {cb}")
        listbox = f"{popdown}.f.l"
        cb.tk.eval(f"{listbox} configure -background {CARD2} "
                   f"-foreground {TEXT} "
                   f"-selectbackground {ACCENT} "
                   f"-selectforeground white "
                   f"-font {{Segoe UI 10}}")
    except Exception:
        pass


def card_frame(parent, title="", **grid_kw):
    outer = tk.Frame(parent, bg=BORDER)
    outer.grid(**grid_kw, sticky="nsew", padx=6, pady=4)
    inner = tk.Frame(outer, bg=CARD)
    inner.pack(fill="both", expand=True, padx=1, pady=1)
    if title:
        tk.Label(inner, text=title, font=H1, bg=CARD, fg=TEXT,
                 anchor="w").pack(fill="x", padx=14, pady=(11, 4))
        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", padx=14, pady=(0, 6))
    return inner


# ── Variable config row ────────────────────────────────────────────────────────

class VarConfigRow(tk.Frame):
    def __init__(self, parent, name: str, sample: str, on_change, **kw):
        super().__init__(parent, bg=CARD, **kw)
        self.name = name
        self.on_change = on_change

        tk.Frame(self, bg=DYN_CLR, width=3).pack(side="left", fill="y", padx=(0, 10))

        body = tk.Frame(self, bg=CARD)
        body.pack(fill="x", expand=True, pady=6)

        hdr = tk.Frame(body, bg=CARD)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"{{{name}}}", font=("Courier New", 11, "bold"),
                 bg=CARD, fg=DYN_CLR).pack(side="left")
        self.sample_lbl = tk.Label(hdr, text=f'  sample: "{sample}"',
                                   font=SM, bg=CARD, fg=MUTED)
        self.sample_lbl.pack(side="left", pady=(1, 0))

        ctrl = tk.Frame(body, bg=CARD)
        ctrl.pack(fill="x", pady=(5, 0))

        tk.Label(ctrl, text="Type:", font=UI, bg=CARD, fg=TEXT).pack(side="left")
        self.type_var = tk.StringVar(value="String")
        self.type_var.trace_add("write", self._on_type)
        styled_combo(ctrl, self.type_var, ["String", "Integer"],
                     width=8).pack(side="left", padx=(4, 14))

        # Integer controls
        self.int_frame = tk.Frame(ctrl, bg=CARD)
        tk.Label(self.int_frame, text="Min digits:", font=UI,
                 bg=CARD, fg=TEXT).pack(side="left")
        self.min_dig = tk.IntVar(value=2)
        self.min_dig.trace_add("write", lambda *_: on_change())
        tk.Spinbox(self.int_frame, from_=1, to=10, textvariable=self.min_dig,
                   width=3, bg=PANEL, fg=TEXT, font=UI,
                   buttonbackground=CARD2, relief="flat",
                   insertbackground=ACCENT,
                   highlightthickness=1, highlightbackground=BORDER,
                   highlightcolor=ACCENT).pack(side="left", padx=(4, 0))

        # String controls
        self.str_frame = tk.Frame(ctrl, bg=CARD)
        for lbl, attr, default, w in [
            ("Sep from:", "sep_from_var", "_", 3),
            ("Sep to:",   "sep_to_var",   " ", 3),
        ]:
            tk.Label(self.str_frame, text=lbl, font=UI,
                     bg=CARD, fg=TEXT).pack(side="left", padx=(0, 3))
            v = tk.StringVar(value=default)
            setattr(self, attr, v)
            v.trace_add("write", lambda *_: on_change())
            styled_entry(self.str_frame, v, width=w,
                         font=MONO_S).pack(side="left", padx=(0, 10))

        tk.Label(self.str_frame, text="Case:", font=UI,
                 bg=CARD, fg=TEXT).pack(side="left", padx=(0, 3))
        self.cap_var = tk.StringVar(value="Keep")
        self.cap_var.trace_add("write", lambda *_: on_change())
        styled_combo(self.str_frame, self.cap_var,
                     ["Keep", "UPPER", "lower", "Title", "Sentence"],
                     width=9).pack(side="left")

        self._on_type()

    def _on_type(self, *_):
        if self.type_var.get() == "Integer":
            self.str_frame.pack_forget()
            self.int_frame.pack(side="left")
        else:
            self.int_frame.pack_forget()
            self.str_frame.pack(side="left")
        self.on_change()

    def update_sample(self, sample: str):
        self.sample_lbl.config(text=f'  sample: "{sample}"')

    def get_config(self) -> dict:
        if self.type_var.get() == "Integer":
            return {"type": "Integer", "min_digits": self.min_dig.get()}
        return {
            "type":     "String",
            "sep_from": self.sep_from_var.get(),
            "sep_to":   self.sep_to_var.get(),
            "cap_mode": self.cap_var.get(),
        }

    def set_config(self, cfg: dict):
        self.type_var.set(cfg.get("type", "String"))
        if cfg.get("type") == "Integer":
            try:
                self.min_dig.set(cfg.get("min_digits", 2))
            except Exception:
                pass
        else:
            self.sep_from_var.set(cfg.get("sep_from", "_"))
            self.sep_to_var.set(cfg.get("sep_to", " "))
            self.cap_var.set(cfg.get("cap_mode", "Keep"))


# ── Main App ──────────────────────────────────────────────────────────────────

class FileRenamerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SBR — Simple Batch Renamer")
        self.configure(bg=BG)
        self.geometry("1140x880")
        self.minsize(920, 700)

        self.folder_path = ""
        self.filenames: list = []
        self.src_var = tk.StringVar()
        self.dst_var = tk.StringVar()
        self.src_regex = None
        self.src_vars:  list = []
        self.var_rows:  dict = {}   # name -> VarConfigRow

        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=22, pady=(18, 0))
        tk.Label(hdr, text="⬡ SBR", font=("Segoe UI", 19, "bold"),
                 bg=BG, fg=ACCENT).pack(side="left")
        tk.Label(hdr, text="  simple batch renamer", font=("Segoe UI", 12),
                 bg=BG, fg=MUTED).pack(side="left", pady=3)
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=22, pady=(8, 0))

        # Bottom bar — packed BEFORE body so it's always visible when resizing
        bar = tk.Frame(self, bg=PANEL)
        bar.pack(fill="x", side="bottom")
        tk.Frame(bar, bg=BORDER, height=1).pack(fill="x")
        inn = tk.Frame(bar, bg=PANEL)
        inn.pack(fill="x", padx=22, pady=10)
        self.status = tk.Label(inn, text="Load a folder to begin.",
                               font=SM, bg=PANEL, fg=MUTED, anchor="w")
        self.status.pack(side="left")
        styled_btn(inn, "✦  Rename All Files", self._do_rename,
                   primary=True).pack(side="right")
        styled_btn(inn, "↺  Refresh", self._refresh_preview
                   ).pack(side="right", padx=(0, 10))

        # Body — packed last so it fills all remaining space between header and bar
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=12, pady=6)
        body.columnconfigure(0, weight=1, minsize=220)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        self._build_left(body)
        self._build_right(body)

    def _build_left(self, parent):
        c = card_frame(parent, "📁  Files", row=0, column=0)
        pick = tk.Frame(c, bg=CARD)
        pick.pack(fill="x", padx=14, pady=(0, 8))
        styled_btn(pick, "Choose Folder", self._pick_folder,
                   primary=True, small=True).pack(side="left")
        self.folder_lbl = tk.Label(pick, text="", font=SM,
                                   bg=CARD, fg=MUTED, wraplength=160, anchor="w")
        self.folder_lbl.pack(side="left", padx=8)

        lf = tk.Frame(c, bg=CARD)
        lf.pack(fill="both", expand=True, padx=14, pady=(0, 8))
        sb = tk.Scrollbar(lf, bg=PANEL, troughcolor=PANEL,
                          activebackground=ACCENT, relief="flat", width=7)
        self.file_lb = tk.Listbox(lf, bg=PANEL, fg=TEXT, font=MONO_S,
                                  selectbackground=ACCENT, selectforeground="white",
                                  activestyle="none", relief="flat", bd=0,
                                  highlightthickness=0, yscrollcommand=sb.set)
        sb.config(command=self.file_lb.yview)
        sb.pack(side="right", fill="y")
        self.file_lb.pack(fill="both", expand=True)

        self.file_count = tk.Label(c, text="No files loaded", font=SM,
                                   bg=CARD, fg=MUTED, anchor="w")
        self.file_count.pack(fill="x", padx=14, pady=(0, 10))

    def _build_right(self, parent):
        right = tk.Frame(parent, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(2, weight=1)
        right.rowconfigure(3, weight=2)
        right.columnconfigure(0, weight=1)

        # ① Source pattern
        sc = card_frame(right, "①  Source Pattern  —  replace each varying part with {NAME}", row=0, column=0)
        tk.Label(sc, text="Pre-filled with your first filename. Edit it to mark variables, e.g. replace '19' with {EP}.",
                 font=SM, bg=CARD, fg=MUTED, anchor="w", wraplength=700,
                 justify="left").pack(fill="x", padx=14, pady=(0, 6))
        src_row = tk.Frame(sc, bg=CARD)
        src_row.pack(fill="x", padx=14, pady=(0, 4))
        self.src_entry = styled_entry(src_row, self.src_var)
        self.src_entry.pack(side="left", fill="x", expand=True)
        self.src_var.trace_add("write", lambda *_: self._on_src_change())
        self.src_status = tk.Label(sc, text="", font=SM, bg=CARD, fg=MUTED, anchor="w")
        self.src_status.pack(fill="x", padx=14, pady=(0, 8))

        # ② Target pattern
        dc = card_frame(right, "②  Target Pattern  —  use the same {NAME} placeholders", row=1, column=0)
        tk.Label(dc, text="Build your desired filename using the same variable names.",
                 font=SM, bg=CARD, fg=MUTED, anchor="w").pack(fill="x", padx=14, pady=(0, 6))
        dst_row = tk.Frame(dc, bg=CARD)
        dst_row.pack(fill="x", padx=14, pady=(0, 8))
        self.dst_entry = styled_entry(dst_row, self.dst_var)
        self.dst_entry.pack(side="left", fill="x", expand=True)
        self.dst_var.trace_add("write", lambda *_: self._refresh_preview())

        # ③ Variable settings
        vc = card_frame(right, "③  Variable Settings", row=2, column=0)
        sw = tk.Frame(vc, bg=CARD)
        sw.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        vsb = tk.Scrollbar(sw, bg=PANEL, troughcolor=PANEL,
                           activebackground=ACCENT, relief="flat", width=7)
        self.var_canvas = tk.Canvas(sw, bg=CARD, highlightthickness=0,
                                    yscrollcommand=vsb.set)
        vsb.config(command=self.var_canvas.yview)
        vsb.pack(side="right", fill="y")
        self.var_canvas.pack(fill="both", expand=True)
        self.var_inner = tk.Frame(self.var_canvas, bg=CARD)
        self._var_win = self.var_canvas.create_window(
            (0, 0), window=self.var_inner, anchor="nw")
        self.var_inner.bind("<Configure>", self._on_var_cfg)
        self.var_canvas.bind("<Configure>", self._on_canvas_cfg)
        self.no_vars_lbl = tk.Label(self.var_inner,
            text="Define {VARIABLES} in the source pattern above to configure them here.",
            font=SM, bg=CARD, fg=MUTED)
        self.no_vars_lbl.pack(padx=14, pady=14)

        # ④ Preview
        pc = card_frame(right, "④  Preview", row=3, column=0)
        self.preview = tk.Text(pc, bg=PANEL, fg=TEXT, font=MONO_S,
                               relief="flat", bd=0, state="disabled",
                               wrap="none", highlightthickness=0, height=8)
        self.preview.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        self.preview.tag_config("old",  foreground=MUTED)
        self.preview.tag_config("arr",  foreground=ACCENT)
        self.preview.tag_config("new",  foreground=SUCCESS)
        self.preview.tag_config("err",  foreground=WARNING)
        self.preview.tag_config("miss", foreground=ERROR)

    def _on_var_cfg(self, e):
        self.var_canvas.configure(scrollregion=self.var_canvas.bbox("all"))
        self.var_canvas.itemconfig(self._var_win, width=self.var_canvas.winfo_width())

    def _on_canvas_cfg(self, e):
        self.var_canvas.itemconfig(self._var_win, width=e.width)

    # ── Folder loading ────────────────────────────────────────────────────────

    def _pick_folder(self):
        path = filedialog.askdirectory(title="Choose folder")
        if not path:
            return
        self.folder_path = path
        self.folder_lbl.config(text=os.path.basename(path) or path)
        files = sorted(f for f in os.listdir(path)
                       if os.path.isfile(os.path.join(path, f)))
        if not files:
            messagebox.showinfo("Empty", "No files found in that folder.")
            return
        self.filenames = files
        self.file_lb.delete(0, "end")
        for f in files:
            self.file_lb.insert("end", f)
        self.file_count.config(text=f"{len(files)} file(s)")
        self.src_var.set(files[0])
        self._set_status(f"Loaded {len(files)} file(s).  Edit the source pattern to mark variables.")

    # ── Source pattern ────────────────────────────────────────────────────────

    def _on_src_change(self):
        pat = self.src_var.get()
        if not pat:
            self.src_regex = None
            self.src_vars  = []
            self._rebuild_var_rows({})
            self.src_status.config(text="", fg=MUTED)
            self._refresh_preview()
            return

        try:
            regex, var_names = pattern_to_regex(pat)
        except ValueError as e:
            self.src_regex = None
            self.src_vars  = []
            self.src_status.config(text=f"✗  {e}", fg=ERROR)
            self._rebuild_var_rows({})
            self._refresh_preview()
            return

        if not var_names:
            self.src_regex = None
            self.src_vars  = []
            self.src_status.config(
                text="No {VARIABLES} found. Replace varying parts with {NAME} tokens.",
                fg=WARNING)
            self._rebuild_var_rows({})
            self._refresh_preview()
            return

        self.src_regex = regex
        self.src_vars  = var_names

        matched = sum(1 for f in self.filenames
                      if match_file(f, regex, var_names) is not None)
        total = len(self.filenames)

        if total == 0:
            self.src_status.config(
                text=f"✓  {len(var_names)} variable(s): "
                     + ", ".join(f"{{{n}}}" for n in var_names),
                fg=SUCCESS)
        elif matched == 0:
            self.src_status.config(
                text=f"✗  Matches 0 / {total} files — check your pattern.", fg=ERROR)
        elif matched < total:
            self.src_status.config(
                text=f"⚠  Matches {matched} / {total} files.", fg=WARNING)
        else:
            self.src_status.config(
                text=f"✓  Matches all {total} file(s) — variables: "
                     + ", ".join(f"{{{n}}}" for n in var_names),
                fg=SUCCESS)

        # Find sample values from first matching file
        samples = {}
        for f in self.filenames:
            cap = match_file(f, regex, var_names)
            if cap:
                samples = cap
                break

        self._rebuild_var_rows(samples)
        self._refresh_preview()

    def _rebuild_var_rows(self, samples: dict):
        new_names = list(self.src_vars)
        new_set   = set(new_names)

        # Save configs of existing rows
        saved = {n: row.get_config() for n, row in self.var_rows.items()}

        # Destroy all current rows and separators
        for w in self.var_inner.winfo_children():
            if w is not self.no_vars_lbl:
                w.destroy()
        self.var_rows.clear()

        if not new_names:
            self.no_vars_lbl.pack(padx=14, pady=14)
            self._update_canvas()
            return

        self.no_vars_lbl.pack_forget()

        for i, name in enumerate(new_names):
            sample = samples.get(name, "")
            row = VarConfigRow(self.var_inner, name, sample, self._refresh_preview)
            row.pack(fill="x", pady=(4 if i == 0 else 0, 0))
            if name in saved:
                row.set_config(saved[name])
            self.var_rows[name] = row
            tk.Frame(self.var_inner, bg=BORDER, height=1).pack(
                fill="x", padx=10, pady=(4, 0))

        self._update_canvas()

    def _update_canvas(self):
        self.var_canvas.update_idletasks()
        self.var_canvas.configure(scrollregion=self.var_canvas.bbox("all"))

    # ── Preview ───────────────────────────────────────────────────────────────

    def _get_var_configs(self) -> dict:
        return {n: row.get_config() for n, row in self.var_rows.items()}

    def _build_new_name(self, filename: str):
        if not self.src_regex or not self.src_vars:
            return None
        cap = match_file(filename, self.src_regex, self.src_vars)
        if cap is None:
            return None
        dst = self.dst_var.get()
        if not dst:
            return None
        try:
            return build_output(cap, dst, self._get_var_configs())
        except Exception as e:
            return f"ERROR: {e}"

    def _refresh_preview(self):
        pt = self.preview
        pt.config(state="normal")
        pt.delete("1.0", "end")

        if not self.filenames:
            pt.insert("end", "Load a folder first.\n", "err")
            pt.config(state="disabled")
            return

        shown = 0
        for fn in self.filenames:
            if shown >= 6:
                rest = len(self.filenames) - shown
                pt.insert("end", f"  … and {rest} more file(s)\n", "old")
                break
            new = self._build_new_name(fn)
            if new is None:
                if self.src_regex:
                    pt.insert("end", fn + "  ✗ no match\n", "miss")
                    shown += 1
                continue
            pt.insert("end", fn, "old")
            pt.insert("end", "  →  ", "arr")
            pt.insert("end", new + "\n",
                       "err" if new.startswith("ERROR:") else "new")
            shown += 1

        if shown == 0 and self.filenames:
            pt.insert("end", "Pattern does not match any files yet.\n", "miss")

        pt.config(state="disabled")

    # ── Rename ────────────────────────────────────────────────────────────────

    def _do_rename(self):
        if not self.filenames:
            messagebox.showwarning("No files", "Load a folder first.")
            return
        if not self.src_regex:
            messagebox.showwarning("No pattern", "Define a valid source pattern first.")
            return
        if not self.dst_var.get().strip():
            messagebox.showwarning("No target", "Enter a target pattern.")
            return

        pairs, skipped = [], []
        for fn in self.filenames:
            new = self._build_new_name(fn)
            if new is None or new.startswith("ERROR:"):
                skipped.append(fn)
            elif new != fn:
                pairs.append((fn, new))

        if not pairs:
            messagebox.showinfo("Nothing to do",
                                "No files matched or all names are already correct.")
            return

        lines = "\n".join(f"  {a}  →  {b}" for a, b in pairs[:8])
        if len(pairs) > 8:
            lines += f"\n  … and {len(pairs) - 8} more"
        if skipped:
            lines += f"\n\n  ({len(skipped)} file(s) skipped — no match)"

        if not messagebox.askyesno("Confirm rename",
                                   f"Rename {len(pairs)} file(s)?\n\n{lines}"):
            return

        errors, renamed = [], 0
        for old, new in pairs:
            try:
                os.rename(os.path.join(self.folder_path, old),
                          os.path.join(self.folder_path, new))
                renamed += 1
            except Exception as e:
                errors.append(f"{old}: {e}")

        if errors:
            messagebox.showerror("Errors",
                                 f"Renamed {renamed}.  Errors:\n" + "\n".join(errors))
        else:
            messagebox.showinfo("Done ✓", f"Successfully renamed {renamed} file(s).")

        # Reload folder
        files = sorted(f for f in os.listdir(self.folder_path)
                       if os.path.isfile(os.path.join(self.folder_path, f)))
        self.filenames = files
        self.file_lb.delete(0, "end")
        for f in files:
            self.file_lb.insert("end", f)
        self.file_count.config(text=f"{len(files)} file(s)")
        if files:
            self.src_var.set(files[0])
        self._set_status(f"Renamed {renamed} file(s).")

    def _set_status(self, msg):
        self.status.config(text=msg)


if __name__ == "__main__":
    app = FileRenamerApp()
    app.mainloop()
