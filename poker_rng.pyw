"""
Poker RNG Manager
A small desktop dashboard that spawns floating, semi-transparent RNG widgets
for multi-tabling online poker. Each widget rolls a random number (default 1-100),
stays on top of other windows, and can be dragged anywhere on screen.

Run:  double-click poker_rng.pyw  (or: pythonw poker_rng.pyw)
"""

import json
import secrets
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path

# ---------- Theme ----------
BG_DARK = "#161b26"
BG_PANEL = "#1c2230"
BG_HOVER = "#252c3d"
BG_INPUT = "#0f1218"
FG_TEXT = "#e7ebf3"
FG_MUTED = "#9aa3b2"
ACCENT = "#4f8cff"
ACCENT_HOVER = "#6a9eff"
DANGER = "#ff5d6c"
BORDER = "#2a3142"

STATE_FILE = Path.home() / ".poker_rng_state.json"


# ---------- Helpers ----------
def roll(lo: int, hi: int) -> int:
    """Cryptographically-strong random integer in [lo, hi]."""
    if lo > hi:
        lo, hi = hi, lo
    return lo + secrets.randbelow(hi - lo + 1)


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(data: dict) -> None:
    try:
        STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


# ---------- Custom flat button (tk.Button looks ugly on Windows) ----------
class FlatButton(tk.Frame):
    def __init__(self, parent, text, command, *, bg=ACCENT, hover=ACCENT_HOVER,
                 fg="white", padx=12, pady=8, font=None, **kwargs):
        super().__init__(parent, bg=bg, cursor="hand2", **kwargs)
        self._bg = bg
        self._hover = hover
        self._command = command
        self._label = tk.Label(self, text=text, bg=bg, fg=fg,
                               padx=padx, pady=pady, font=font, cursor="hand2")
        self._label.pack(fill="both", expand=True)
        for w in (self, self._label):
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)
            w.bind("<Button-1>", self._on_click)

    def _on_enter(self, _):
        self.configure(bg=self._hover)
        self._label.configure(bg=self._hover)

    def _on_leave(self, _):
        self.configure(bg=self._bg)
        self._label.configure(bg=self._bg)

    def _on_click(self, _):
        if self._command:
            self._command()

    def set_text(self, text):
        self._label.configure(text=text)


# ---------- RNG floating widget ----------
class RNGWindow:
    WIDTH = 180
    HEIGHT = 140

    def __init__(self, manager, inst_id: int, name: str, x: int, y: int,
                 alpha: float, last, history):
        self.manager = manager
        self.id = inst_id
        self.name = name
        self.alpha = alpha
        self.last = last
        self.history = list(history or [])

        win = tk.Toplevel(manager.root)
        self.win = win
        win.title(name)
        win.overrideredirect(True)        # no OS chrome
        win.attributes("-topmost", True)  # float over poker tables
        win.attributes("-alpha", alpha)
        win.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")
        win.configure(bg=BG_PANEL, highlightthickness=1,
                      highlightbackground=ACCENT, highlightcolor=ACCENT)

        # ---- Header (drag handle + close) ----
        header = tk.Frame(win, bg=BG_DARK, height=22)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        self.title_var = tk.StringVar(value=name)
        title_lbl = tk.Label(header, textvariable=self.title_var, bg=BG_DARK,
                             fg=FG_MUTED, font=("Segoe UI", 9), anchor="w",
                             padx=8, cursor="fleur")
        title_lbl.pack(side="left", fill="both", expand=True)

        close_btn = tk.Label(header, text="×", bg=BG_DARK, fg=FG_MUTED,
                             font=("Segoe UI", 12, "bold"), padx=8, cursor="hand2")
        close_btn.pack(side="right")
        close_btn.bind("<Enter>", lambda e: close_btn.configure(fg=DANGER))
        close_btn.bind("<Leave>", lambda e: close_btn.configure(fg=FG_MUTED))
        close_btn.bind("<Button-1>", lambda e: self.manager.remove_instance(self.id))

        # Drag bindings
        for w in (header, title_lbl):
            w.bind("<Button-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_motion)
            w.bind("<ButtonRelease-1>", self._drag_end)

        # ---- Result number ----
        self.result_var = tk.StringVar(value=str(last) if last is not None else "—")
        result_font = tkfont.Font(family="Segoe UI", size=34, weight="bold")
        self.result_lbl = tk.Label(win, textvariable=self.result_var, bg=BG_PANEL,
                                   fg=FG_TEXT, font=result_font)
        self.result_lbl.pack(pady=(8, 4))

        # ---- Roll button ----
        roll_btn = FlatButton(win, "Roll", self.do_roll,
                              bg=ACCENT, hover=ACCENT_HOVER,
                              font=("Segoe UI", 10, "bold"), padx=10, pady=4)
        roll_btn.pack(fill="x", padx=10)

        # ---- History strip ----
        self.history_var = tk.StringVar(value=self._fmt_history())
        hist_lbl = tk.Label(win, textvariable=self.history_var, bg=BG_PANEL,
                            fg=FG_MUTED, font=("Segoe UI", 8))
        hist_lbl.pack(pady=(4, 6))

        # Click anywhere on the body also rolls
        for w in (win, self.result_lbl):
            w.bind("<Double-Button-1>", lambda e: self.do_roll())

        self._drag_offset = (0, 0)

    # ----- dragging -----
    def _drag_start(self, e):
        self._drag_offset = (e.x_root - self.win.winfo_x(),
                             e.y_root - self.win.winfo_y())

    def _drag_motion(self, e):
        ox, oy = self._drag_offset
        self.win.geometry(f"+{e.x_root - ox}+{e.y_root - oy}")

    def _drag_end(self, _):
        self.manager.persist()

    # ----- actions -----
    def do_roll(self):
        n = roll(self.manager.range_min, self.manager.range_max)
        self.last = n
        self.history.insert(0, n)
        self.history = self.history[:6]
        self.result_var.set(str(n))
        self.history_var.set(self._fmt_history())
        self._flash()
        self.manager.refresh_list()
        self.manager.persist()

    def _flash(self):
        self.result_lbl.configure(fg=ACCENT)
        self.win.after(180, lambda: self.result_lbl.configure(fg=FG_TEXT))

    def _fmt_history(self):
        if not self.history:
            return ""
        return "  ".join(str(n) for n in self.history[1:])

    def set_alpha(self, a: float):
        self.alpha = a
        self.win.attributes("-alpha", a)

    def set_name(self, name: str):
        self.name = name
        self.title_var.set(name)
        self.win.title(name)

    def geometry(self):
        self.win.update_idletasks()
        return self.win.winfo_x(), self.win.winfo_y()

    def destroy(self):
        try:
            self.win.destroy()
        except Exception:
            pass


# ---------- Dashboard ----------
class Dashboard:
    DASH_W = 280
    DASH_H = 460

    def __init__(self, root: tk.Tk):
        self.root = root
        self.windows: dict[int, RNGWindow] = {}

        st = load_state()
        self.next_id = st.get("next_id", 1)
        self.range_min = st.get("range_min", 1)
        self.range_max = st.get("range_max", 100)
        self.default_alpha = st.get("default_alpha", 0.85)
        saved_instances = st.get("instances", [])

        root.title("Poker RNG")
        root.configure(bg=BG_DARK)
        root.geometry(f"{self.DASH_W}x{self.DASH_H}+80+80")
        root.minsize(self.DASH_W, 360)
        root.attributes("-topmost", True)
        try:
            # keep dashboard on top but not as aggressively as widgets
            root.attributes("-topmost", False)
        except Exception:
            pass

        self._build_ui()

        # Restore previous session
        for inst in saved_instances:
            self._spawn(
                inst_id=inst["id"],
                name=inst.get("name", f"Table {inst['id']}"),
                x=inst.get("x", 200),
                y=inst.get("y", 200),
                alpha=inst.get("alpha", self.default_alpha),
                last=inst.get("last"),
                history=inst.get("history", []),
            )
        self.refresh_list()

        root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ----- UI -----
    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg=BG_DARK, height=48)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="POKER  RNG", bg=BG_DARK, fg=FG_TEXT,
                 font=("Segoe UI", 12, "bold"), padx=14).pack(side="left",
                                                              fill="y")
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")

        # New button section
        new_section = tk.Frame(self.root, bg=BG_DARK, padx=14, pady=12)
        new_section.pack(fill="x")
        FlatButton(new_section, "+  New RNG", self.add_instance,
                   bg=ACCENT, hover=ACCENT_HOVER,
                   font=("Segoe UI", 11, "bold"), padx=10, pady=8).pack(fill="x")

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")

        # Range / opacity controls
        controls = tk.Frame(self.root, bg=BG_DARK, padx=14, pady=10)
        controls.pack(fill="x")

        tk.Label(controls, text="RANGE", bg=BG_DARK, fg=FG_MUTED,
                 font=("Segoe UI", 8, "bold")).grid(row=0, column=0, sticky="w")
        self.min_var = tk.StringVar(value=str(self.range_min))
        self.max_var = tk.StringVar(value=str(self.range_max))
        min_e = tk.Entry(controls, textvariable=self.min_var, width=6,
                         bg=BG_INPUT, fg=FG_TEXT, insertbackground=FG_TEXT,
                         relief="flat", justify="center")
        max_e = tk.Entry(controls, textvariable=self.max_var, width=6,
                         bg=BG_INPUT, fg=FG_TEXT, insertbackground=FG_TEXT,
                         relief="flat", justify="center")
        min_e.grid(row=0, column=1, padx=(8, 4))
        tk.Label(controls, text="–", bg=BG_DARK,
                 fg=FG_MUTED).grid(row=0, column=2)
        max_e.grid(row=0, column=3, padx=(4, 0))
        for w, var, attr in ((min_e, self.min_var, "range_min"),
                             (max_e, self.max_var, "range_max")):
            w.bind("<FocusOut>", lambda e, v=var, a=attr: self._update_range(v, a))
            w.bind("<Return>", lambda e, v=var, a=attr: self._update_range(v, a))

        tk.Label(controls, text="OPACITY", bg=BG_DARK, fg=FG_MUTED,
                 font=("Segoe UI", 8, "bold")).grid(row=1, column=0,
                                                    sticky="w", pady=(10, 0))
        self.alpha_var = tk.DoubleVar(value=self.default_alpha)
        alpha_scale = tk.Scale(controls, from_=0.2, to=1.0, resolution=0.05,
                               orient="horizontal", variable=self.alpha_var,
                               bg=BG_DARK, fg=FG_MUTED,
                               troughcolor=BG_INPUT, highlightthickness=0,
                               sliderrelief="flat", showvalue=False,
                               length=160, command=self._update_alpha)
        alpha_scale.grid(row=1, column=1, columnspan=3, sticky="we",
                         pady=(10, 0), padx=(8, 0))

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")

        # Active list
        list_header = tk.Frame(self.root, bg=BG_DARK, padx=14, pady=8)
        list_header.pack(fill="x")
        tk.Label(list_header, text="ACTIVE", bg=BG_DARK, fg=FG_MUTED,
                 font=("Segoe UI", 8, "bold")).pack(side="left")
        self.count_var = tk.StringVar(value="0")
        tk.Label(list_header, textvariable=self.count_var,
                 bg=BG_DARK, fg=ACCENT,
                 font=("Segoe UI", 8, "bold")).pack(side="right")

        self.list_frame = tk.Frame(self.root, bg=BG_DARK)
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Footer
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")
        footer = tk.Frame(self.root, bg=BG_DARK, padx=14, pady=10)
        footer.pack(fill="x")
        FlatButton(footer, "Close All", self.close_all,
                   bg=BG_PANEL, hover=BG_HOVER, fg=FG_MUTED,
                   font=("Segoe UI", 9), padx=10, pady=4).pack(fill="x")

    # ----- list rendering -----
    def refresh_list(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        self.count_var.set(str(len(self.windows)))

        if not self.windows:
            tk.Label(self.list_frame, text="No active windows.",
                     bg=BG_DARK, fg=FG_MUTED,
                     font=("Segoe UI", 9, "italic"),
                     pady=14).pack()
            return

        for inst_id, w in self.windows.items():
            self._render_row(w)

    def _render_row(self, w: RNGWindow):
        row = tk.Frame(self.list_frame, bg=BG_PANEL, cursor="hand2")
        row.pack(fill="x", pady=2, padx=4)

        dot = tk.Label(row, text="●", bg=BG_PANEL, fg=ACCENT,
                       font=("Segoe UI", 8))
        dot.pack(side="left", padx=(8, 4), pady=4)

        name_lbl = tk.Label(row, text=w.name, bg=BG_PANEL, fg=FG_TEXT,
                            font=("Segoe UI", 9), anchor="w")
        name_lbl.pack(side="left", fill="x", expand=True, pady=4)

        last_lbl = tk.Label(row, text=str(w.last) if w.last is not None else "—",
                            bg=BG_PANEL, fg=FG_MUTED,
                            font=("Segoe UI", 9, "bold"))
        last_lbl.pack(side="left", padx=6, pady=4)

        x_btn = tk.Label(row, text="×", bg=BG_PANEL, fg=FG_MUTED,
                         font=("Segoe UI", 11, "bold"),
                         padx=8, cursor="hand2")
        x_btn.pack(side="right")
        x_btn.bind("<Enter>", lambda e: x_btn.configure(fg=DANGER))
        x_btn.bind("<Leave>", lambda e: x_btn.configure(fg=FG_MUTED))
        x_btn.bind("<Button-1>", lambda e, i=w.id: self.remove_instance(i))

        # hover + focus
        def hover(_): row.configure(bg=BG_HOVER); name_lbl.configure(bg=BG_HOVER); dot.configure(bg=BG_HOVER); last_lbl.configure(bg=BG_HOVER); x_btn.configure(bg=BG_HOVER)
        def leave(_): row.configure(bg=BG_PANEL); name_lbl.configure(bg=BG_PANEL); dot.configure(bg=BG_PANEL); last_lbl.configure(bg=BG_PANEL); x_btn.configure(bg=BG_PANEL)
        for el in (row, dot, name_lbl, last_lbl):
            el.bind("<Enter>", hover)
            el.bind("<Leave>", leave)
            el.bind("<Button-1>", lambda e, ww=w: self._focus_window(ww))
            el.bind("<Double-Button-1>", lambda e, ww=w: ww.do_roll())

    def _focus_window(self, w: RNGWindow):
        w.win.lift()
        w.win.attributes("-topmost", False)
        w.win.attributes("-topmost", True)

    # ----- instance management -----
    def add_instance(self):
        inst_id = self.next_id
        self.next_id += 1
        # Stagger placement
        offset = (len(self.windows) * 30) % 240
        x = self.root.winfo_x() + self.DASH_W + 30 + offset
        y = self.root.winfo_y() + 60 + offset
        self._spawn(inst_id, f"Table {inst_id}", x, y,
                    self.default_alpha, None, [])
        self.refresh_list()
        self.persist()

    def _spawn(self, inst_id, name, x, y, alpha, last, history):
        w = RNGWindow(self, inst_id, name, x, y, alpha, last, history)
        self.windows[inst_id] = w

    def remove_instance(self, inst_id: int):
        w = self.windows.pop(inst_id, None)
        if w:
            w.destroy()
        self.refresh_list()
        self.persist()

    def close_all(self):
        if not self.windows:
            return
        for w in list(self.windows.values()):
            w.destroy()
        self.windows.clear()
        self.refresh_list()
        self.persist()

    # ----- settings updates -----
    def _update_range(self, var: tk.StringVar, attr: str):
        try:
            v = int(var.get())
        except ValueError:
            v = getattr(self, attr)
            var.set(str(v))
            return
        setattr(self, attr, v)
        self.persist()

    def _update_alpha(self, _val):
        a = float(self.alpha_var.get())
        self.default_alpha = a
        for w in self.windows.values():
            w.set_alpha(a)
        self.persist()

    # ----- persistence -----
    def persist(self):
        instances = []
        for w in self.windows.values():
            x, y = w.geometry()
            instances.append({
                "id": w.id, "name": w.name, "x": x, "y": y,
                "alpha": w.alpha, "last": w.last, "history": w.history,
            })
        save_state({
            "next_id": self.next_id,
            "range_min": self.range_min,
            "range_max": self.range_max,
            "default_alpha": self.default_alpha,
            "instances": instances,
        })

    def _on_close(self):
        self.persist()
        self.root.destroy()


def main():
    root = tk.Tk()
    Dashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
