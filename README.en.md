# Click

切换到中文README `/docs/README.en.md`

A small Python toolkit that helps you get mouse coordinates and automatically click a specified location at a fixed interval. It supports both CLI and GUI, and is suitable for repetitive clicking or precise targeting.

On macOS, follow the prompt and enable permissions for the runtime host (Terminal/IDE) in **System Settings → Privacy & Security → Accessibility**, so the application is allowed to control the computer.

The project development and document translation work were assisted by cursor.

---

## Feature overview

| Tool | Description |
|------|-------------|
| **mousePos.py** | Get the current mouse coordinates, supports live watching; includes interactive Yes/No guidance. |
| **intervalClickGui.py** | GUI: drag a circle to mark the click position, auto-click at an interval; supports click count and “move out to stop”. |

---

## Requirements

- Python 3.8+
- Dependencies: `requirements.txt`

### Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**macOS note**: auto-clicking requires Accessibility permission. If clicking does not work, enable it for **Terminal** or the **IDE that runs this script** in **System Settings → Privacy & Security → Accessibility**; otherwise you may see two issues:
1. After clicking the Start button, the mouse cannot automatically move to the circle center, so the pre-click mouse-position check detects the mouse is not inside the circle and stops automatically.
2. The click action cannot be triggered.

---

## 1) mousePos.py — Mouse position

Get the current mouse coordinates `(x, y)` on the screen, and optionally enter live watching mode.

### Features

- **Single read**: prints the current coordinates on run.
- **Live watching**: optionally refreshes coordinates continuously (default interval: 0.1s).
- **Interactive guidance**: asks “enter live watching?” by default, supports `[Y/n]` (Enter selects default).
- **Restore terminal cursor on exit**: after `Ctrl+C` exits watching mode, restores the terminal cursor.

### Usage

```bash
# Print once, then ask whether to watch
python mousePos.py

# Enter watch mode after prompt
python mousePos.py -w

# Print only, no prompt
python mousePos.py -y

# Watch directly, no prompt (good for scripting)
python mousePos.py -w -y

# Watch interval = 0.5 seconds
python mousePos.py -w -i 0.5

# Quiet mode, less output
python mousePos.py -q

# Full help
python mousePos.py -h
```

### Arguments

| Argument | Description |
|----------|-------------|
| `-w`, `--watch` | Enter live watching mode. |
| `-i`, `--interval SEC` | Refresh interval (seconds) while watching, default 0.1. |
| `-y`, `--yes` | Skip all prompts and run directly. |
| `-q`, `--quiet` | Do not print usage hints, only output results. |

---

## 2) intervalClickGui.py — Interval click (GUI)

Use a circle on the screen to mark the click position, then left-click at the configured interval; supports click count and stopping automatically when the mouse moves out of the circle.

### Features

- **Circle + control panel separated**
  - **Circle**: a small window; the center is the click target; draggable anywhere.
  - **Control panel**: interval/count, start/stop/close; drag the top title bar to move.
- **Click logic**
  - Before each click, the circle is **hidden briefly** and then the click is executed, ensuring the click lands on the underlying window (e.g., a button) rather than on the circle.
  - The click interval has a **minimum of 50ms** to avoid being set too small.
- **“Sticker” circle while running**
  - After starting, the circle becomes lighter and mouse-transparent; it is only a position indicator. After stopping, it becomes draggable again with normal color.
- **Move mouse out to stop**
  - While running, the program checks whether the mouse is still inside the circle at an interval; the **check interval is automatically smaller than the click interval** (about 1/3 of it, clamped to 20–100ms), so you can move the mouse away between clicks to stop.
- **Interval and count**
  - **Interval (seconds)**: numeric input with +/- buttons, range 0.05–3600s.
  - **Click count**: numeric input with +/- buttons; **0 means unlimited** until you stop manually or move the mouse out.
- **UI details**
  - The inputs use **+/- buttons** on the right (green + / red -) with a short divider line; symbols are bold.
  - The number color matches the circle center coordinate color (orange).
  - Uses the Fusion style so the up/down buttons render consistently across platforms.
- **Initial positions**
  - On first show, the panel and circle have default positions; both can be moved independently.
- **Always on top**
  - The control panel supports toggling always-on-top vs. normal.

### Usage

```bash
python intervalClickGui.py
```

### Detailed development/interaction notes

See: `docs/intervalClickGui.devguide.en.md`

## Files

```
click/
├── README.md            # This document
├── README.en.md        # This document (English)
├── requirements.txt    # Python dependencies
├── mousePos.py         # Mouse position (CLI)
├── intervalClickGui.py # Interval click (GUI)
└── docs/
    ├── intervalClickGui.devguide.zh-CN.md # Dev guide (Chinese)
    └── intervalClickGui.devguide.en.md    # Dev guide (English)
```

### requirements.txt

- `pyautogui`: mouse position and simulated clicking.
- `PyQt6`: GUI (only required by intervalClickGui).

---

