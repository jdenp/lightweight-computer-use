# lightweight-computer-use - notes for agents

## Design rules (do not revisit)

- Vision only. No UIA, no accessibility tree, no DOM, no element labels, no
  OCR, no auto-resize-to-context logic. Do not add any of these.
- The only settings are the three env vars: LWCU_SCREENSHOT_SCALE,
  LWCU_MAX_WIDTH, LWCU_JPEG_QUALITY. Do not add more.
- Coordinates are native virtual-desktop px; negative x is the left display.
  Displays are indexed left to right, 0 = leftmost.
- A screenshot response without its own coordinate math (display geometry +
  original capture size + returned image size + scale factor) is a bug. Keep
  all four in every response.
- JPEG by default (screens are photos; PNG is 3x). Scale is applied only when
  the capture width exceeds MAX_WIDTH; otherwise 1:1. The response states the
  scale actually used.

## Implementation notes

- Win32 via ctypes (user32 only): EnumDisplayMonitors for display geometry,
  GetClientRect + ClientToScreen for window client areas, SendInput for all
  input. No deps beyond fastmcp + Pillow.
- Window capture is the client-area rectangle as seen on screen; an occluded
  window captures whatever is in that region.
- type uses KEYEVENTF_UNICODE (any script, no layout dependency); hotkey uses
  VK codes.
- No absolute SendInput mouse coordinates: move with SetCursorPos, then plain
  down/up events. Absolute coords would need 0-65535 normalization across the
  virtual screen.
- Input actions start with a 200 ms settle (win.STEP_DELAY_S) so consecutive
  tool calls don't land mid-UI-update; pairs inside one call are unsleeped.
- Machine-level keypresses reach whatever window has focus: an esc sent to
  close the Start menu aborts a focused pi TUI (app.interrupt).
- Pillow ImageGrab.grab takes a virtual-screen bbox; negative left is fine
  (Pillow >= 9.2).
- Server instructions repeat the coordinate-space note (fastmcp instructions
  field), same wording family as the README.

## Conventions

- One-line code comments only.
- Do not commit or push without the user's go-ahead.
