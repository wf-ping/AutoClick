# intervalClickGui.py Development Guide (English)

## Overview

- **Goal**: provide a visible “target circle” and repeatedly left-click at the circle center using a configurable interval.
- **Windows**:
  - **CircleWindow**: the small circle window; its center is the click target; draggable.
  - **ControlPanel**: the control panel for interval/count and start/stop/reset/close.

## Detailed behavior

### 1) Drag UX (CircleWindow)

- While dragging:
  - the circle becomes lighter
  - a crosshair is drawn at the center
  - a floating bubble (`CoordHintWindow`) shows `X=, Y=`
- Bubble placement avoids going off-screen:
  - tries NE/NW/SE/SW relative positions around the center
  - picks the position with the smallest “overflow penalty”, then clamps to visible area
- Sticker mode (while running):
  - the circle becomes translucent and mouse-transparent (does not block clicks)

### 2) Clicking loop (ControlPanel)

- Each tick:
  - hides the circle window
  - performs `pyautogui.moveTo` + `pyautogui.click`
  - shows the circle window again
  - this ensures the click lands on the underlying app rather than the circle overlay
- Auto stop:
  - if the mouse moves outside radius `R` from the center, the loop stops
- Parameters:
  - minimum interval: `MIN_INTERVAL_SEC`
  - count: `0` means unlimited

### 3) Circle initial/reset placement

- All placement is unified in `ControlPanel._place_circle_relative_to_panel()`.
- Coordinate system uses the panel’s **top-left** as origin (pixels):
  - `CIRCLE_OFFSET_X`: positive to the right
  - `CIRCLE_OFFSET_Y`: positive downward
- The function clamps to the screen’s visible area to avoid placing the circle off-screen.

### 4) Always-on-top pin (📌)

- A pin toggle (`PinToggle`) is shown on the panel’s top-right:
  - **Pinned**: upright
  - **Unpinned**: tilted
  - Tooltip reflects the current state
- Toggling applies `WindowStaysOnTopHint` at runtime.

## Development notes

```bash
python3 intervalClickGui.py
```

## Key symbols

- `CoordHintWindow`
- `CircleWindow.get_center_screen()`
- `CircleWindow.set_sticker_mode()`
- `ControlPanel._start_click()` / `_stop_click()`
- `ControlPanel._place_circle_relative_to_panel()`
- `main()`

