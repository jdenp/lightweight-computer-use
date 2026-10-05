# lightweight-computer-use

Annoyed at accessibility trees and giant JSON UI dumps? This is for you.
Simple and efficient vision-based computer use: an MCP server that navigates
with scaled screenshots and zooms.

Screenshot-only, Windows, vision by design: no UIA, no accessibility tree, no
DOM, no element labels, no OCR.

Replaces computer-use-mcp (hardcoded downscale, no config, huge images) and
Windows-MCP (UIA tree is empty for web-rendered apps, element labels invisible
in text output, multi-monitor coordinates ambiguous).

## Coordinate space

All coordinates are native virtual-desktop pixels. This machine: two 1920x1080
displays, virtual desktop 3840x1080 at (-1920,0); the secondary is on the left,
so negative x is the left display. Displays are indexed left to right,
0 = leftmost (here 0 = secondary, 1 = primary).

## Install

```
C:\Python313\python.exe -m pip install -e .
```

Deps: fastmcp + Pillow, nothing else.

## Config (env vars)

| var                   | default | meaning                                          |
|-----------------------|---------|--------------------------------------------------|
| `LWCU_SCREENSHOT_SCALE` | 0.5   | scale 0.1-1.0, applied only if capture width > `LWCU_MAX_WIDTH` |
| `LWCU_MAX_WIDTH`      | 1600    | capture width (px) above which scaling kicks in  |
| `LWCU_JPEG_QUALITY`   | 80      | JPEG quality (images are JPEG; PNG via `fmt` arg) |

## Tools

- `screenshot` - `display` (zero-based index or list, default all), `window`
  (title substring or hwnd; captures the client area), `region` [x,y,w,h]
  (virtual-desktop px), `scale`, `fmt` (jpeg/png)
- `move` [x,y] - move cursor
- `click` [x,y] - `button` left/right/middle, `clicks` 1/2
- `type` text - unicode, layout independent
- `scroll` dx,dy - wheel units, 120 = one notch, dy>0 up, dx>0 right
- `hotkey` [keys] - e.g. `["ctrl","shift","t"]`

Every screenshot response states the display geometry, original capture size,
returned image size, and scale factor, so the image's coordinate math is in
the response. Move/click report the actual cursor position.

Input actions are spaced by a fixed 200 ms settle delay; key chords and
double-clicks inside one call stay tight.

## MCP

`C:\Users\short\.pi\agent\mcp.json`:

```json
{
  "mcpServers": {
    "lightweight-computer-use": {
      "command": "C:\\Python313\\python.exe",
      "args": ["-m", "lightweight_computer_use", "serve"],
      "exposure": "direct"
    }
  }
}
```

`exposure: direct` declares the six tools to the model as first-class tools
(one call per step); without it pi routes MCP calls through codemode scripts.

Run it standalone: `C:\Python313\python.exe -m lightweight_computer_use serve`
