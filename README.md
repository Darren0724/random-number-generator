# Poker RNG Manager

A small desktop dashboard for online poker multi-tabling. Spawn lightweight, semi-transparent, always-on-top RNG widgets — one per table — and roll a random number (default **1–100**) on each. The dashboard itself looks like a tiny VPN client: one window with a list of "active" RNGs and a button to add more.

---

## Features

- **Dashboard** (small, always-visible window) lists all active RNGs with their last roll, and lets you spawn or close instances.
- **Floating RNG widgets** — borderless `Toplevel` windows, semi-transparent, **always on top** so they sit over your poker tables without stealing focus.
- **Drag anywhere** by the window header; positions are remembered.
- **Per-session range** (default 1–100) and **adjustable opacity** (default 85%).
- **Recent-roll history** (last 6) shown under each widget.
- **Cryptographically-strong RNG** via `secrets.randbelow` — uniform, unbiased, not a seeded `random` module.
- **State is persisted** to `~/.poker_rng_state.json` — close and reopen and your tables come back where you left them.
- **Zero dependencies**: pure Python standard library (`tkinter`, ships with Python on Windows).

## Requirements

- Python 3.8+ (Windows / macOS / Linux). On Windows, the official installer from [python.org](https://www.python.org/) includes Tkinter by default.

## Run

**Windows** — double-click `poker_rng.pyw`. (`.pyw` is associated with `pythonw.exe` by the official Python installer, so it launches without an extra console window.)

**macOS / Linux**:

```bash
python3 poker_rng.pyw
```

## Usage

1. Launch the app — the dashboard appears.
2. Click **+ New RNG** for each poker table. A small widget pops up.
3. Drag each widget over the corresponding table.
4. Click **Roll** (or double-click the widget body) to generate a number.
5. Adjust the global **Range** and **Opacity** in the dashboard at any time.
6. Close a widget with `×` on its header, or remove it from the dashboard list.
7. **Close All** clears every active widget at once.

Window positions, names, last rolls, range, and opacity are saved between runs.

## Project layout

```
random-number-generator/
├── poker_rng.pyw    # entire application (single file, stdlib only)
└── README.md
```

## Notes & limitations

- The dashboard is a normal OS window; the RNG widgets are borderless and rely on `wm_attributes("-topmost", True)` to float. If a poker client runs in exclusive fullscreen, you may need to switch it to windowed/borderless mode for the overlay to appear above it.
- Transparency uses Tk's `-alpha`. This works on Windows and macOS; on some Linux window managers it may be ignored.
- State is stored as plain JSON at `~/.poker_rng_state.json`. Delete that file to start fresh.

## License

No license specified — treat as personal use unless you add one.
