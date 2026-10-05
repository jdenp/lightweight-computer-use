"""lightweight-computer-use: screenshot-only computer-use MCP server for Windows."""
import base64
import ctypes
import io
import os
from ctypes import wintypes

from fastmcp import FastMCP
from mcp.types import ImageContent, TextContent
from PIL import Image, ImageGrab

from . import win

SCALE = float(os.environ.get("LWCU_SCREENSHOT_SCALE", "0.5"))
MAX_WIDTH = int(os.environ.get("LWCU_MAX_WIDTH", "1600"))
JPEG_QUALITY = int(os.environ.get("LWCU_JPEG_QUALITY", "80"))

INSTRUCTIONS = (
    "Screenshot-only computer-use server for this Windows machine. Vision by design: "
    "no UIA, no accessibility tree, no DOM, no element labels, no OCR. "
    "All coordinates are native virtual-desktop pixels. Virtual desktop is 3840x1080 at "
    "(-1920,0): primary display is (0,0)-(1920,1080), the secondary is on the left at "
    "(-1920,0)-(0,1080), so negative x is the left display. Displays are indexed left to "
    "right, 0 = leftmost (here 0 = secondary, 1 = primary). "
    "Input is not acknowledged by the OS: a keypress can be dropped, so after a click or "
    "hotkey that should change the screen, take a screenshot and verify before continuing. "
    "Keystrokes go to the focused window: check the foreground before type/hotkey, and avoid "
    "esc (it can abort the focused app). Windows with empty titles (taskbar) cannot be found "
    "by title: use hwnd. The Win key toggles the Start menu. Screen and region captures of the "
    "left display come back black on this machine: use the window parameter (PrintWindow) for "
    "windows there."
)

mcp = FastMCP("lightweight-computer-use", instructions=INSTRUCTIONS)


def _monitors_line(monitors):
    parts = []
    for i, m in enumerate(monitors):
        w = m["right"] - m["left"]
        h = m["bottom"] - m["top"]
        tag = " [primary]" if m["primary"] else ""
        parts.append(f"[{i}] {w}x{h} at ({m['left']},{m['top']}){tag}")
    return "Displays: " + "; ".join(parts)


def _loc(loc):
    if not (isinstance(loc, (list, tuple)) and len(loc) == 2
            and all(isinstance(v, int) for v in loc)):
        raise ValueError("loc must be [x, y] in virtual-desktop px")
    return int(loc[0]), int(loc[1])


def _encode(img, fmt):
    buf = io.BytesIO()
    if fmt == "png":
        img.save(buf, "PNG")
        mime = "image/png"
        label = "PNG"
    else:
        img.convert("RGB").save(buf, "JPEG", quality=JPEG_QUALITY)
        mime = "image/jpeg"
        label = f"JPEG q{JPEG_QUALITY}"
    return base64.b64encode(buf.getvalue()).decode(), mime, label

gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)


class _BmpInfoHeader(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long), ("biHeight", ctypes.c_long),
        ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


def _print_window(hwnd, w, h):
    """Client pixels via PrintWindow: works on occluded windows and on displays whose screen DC is black."""
    src = win.user32.GetDC(hwnd)
    mem = gdi32.CreateCompatibleDC(src)
    bmp = gdi32.CreateCompatibleBitmap(src, w, h)
    gdi32.SelectObject(mem, bmp)
    win.user32.PrintWindow(hwnd, mem, 2)  # PW_RENDERFULLCONTENT
    hdr = _BmpInfoHeader()
    hdr.biSize = ctypes.sizeof(_BmpInfoHeader)
    hdr.biWidth, hdr.biHeight = w, -h
    hdr.biPlanes, hdr.biBitCount = 1, 32
    buf = ctypes.create_string_buffer(w * h * 4)
    rows = gdi32.GetDIBits(mem, bmp, 0, h, buf, ctypes.byref(hdr), 0)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mem)
    win.user32.ReleaseDC(hwnd, src)
    if not rows:
        raise ValueError(f"GetDIBits failed for hwnd {hwnd}")
    return Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")


@mcp.tool
def screenshot(display=None, window=None, region=None, scale=None, fmt="jpeg"):
    """Capture the screen. display: zero-based index or list, default all.
    window: title substring or hwnd; captures that window's client area via
    PrintWindow (works on occluded windows and on displays whose screen DC is
    black). region: [x, y, w, h] in virtual-desktop px. scale: 0.1-1.0, overrides
    config. fmt: jpeg (default) or png. The response text states the display
    geometry, original capture size, returned image size, and scale factor."""
    if window is not None and region is not None:
        raise ValueError("window and region are mutually exclusive")
    if scale is not None and not 0.1 <= scale <= 1.0:
        raise ValueError("scale must be 0.1-1.0")
    if fmt not in ("jpeg", "png"):
        raise ValueError("fmt must be jpeg or png")

    monitors = win.list_monitors()

    if window is not None:
        hwnd, title = win.find_window(window)
        x, y, w, h = win.client_rect(hwnd)
        cap_desc = f'window "{title}" (hwnd {hwnd}) client ({x},{y}) {w}x{h}, PrintWindow'
        img = _print_window(hwnd, w, h)
    elif region is not None:
        if len(region) != 4 or any(not isinstance(v, int) for v in region):
            raise ValueError("region must be [x, y, w, h] in virtual-desktop px")
        x, y, w, h = region
        if w <= 0 or h <= 0:
            raise ValueError("region w and h must be positive")
        cap_desc = f"region ({x},{y}) {w}x{h}"
    else:
        if display is None:
            idxs = list(range(len(monitors)))
        elif isinstance(display, int):
            idxs = [display]
        else:
            idxs = sorted(set(display))
        if any(not 0 <= i < len(monitors) for i in idxs):
            raise ValueError(f"display index out of range 0-{len(monitors) - 1}")
        x1 = min(monitors[i]["left"] for i in idxs)
        y1 = min(monitors[i]["top"] for i in idxs)
        x2 = max(monitors[i]["right"] for i in idxs)
        y2 = max(monitors[i]["bottom"] for i in idxs)
        x, y, w, h = x1, y1, x2 - x1, y2 - y1
        cap_desc = f"displays {idxs} ({x},{y}) {w}x{h}"

    if window is None:
        img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    orig_w, orig_h = img.size

    # scale only when the capture exceeds MAX_WIDTH
    applied = 1.0
    if scale is not None:
        requested = scale
    else:
        requested = SCALE
    if orig_w > MAX_WIDTH and requested < 1.0:
        applied = requested
        img = img.resize(
            (max(1, round(orig_w * applied)), max(1, round(orig_h * applied))),
            Image.LANCZOS,
        )

    data, mime, label = _encode(img, fmt)
    out_w, out_h = img.size

    text = (
        f"{_monitors_line(monitors)}\n"
        f"Capture: {cap_desc}\n"
        f"Original: {orig_w}x{orig_h} px\n"
        f"Returned: {out_w}x{out_h} px, scale {applied:.3f}, {label}\n"
        f"Virtual-desktop px = ({x},{y}) + image px / {applied:.3f}"
    )
    return [
        TextContent(type="text", text=text),
        ImageContent(type="image", data=data, mime_type=mime),
    ]


@mcp.tool
def move(loc):
    """Move the cursor to [x, y] in virtual-desktop px and report the actual position."""
    x, y = _loc(loc)
    win.settle()
    win.set_cursor_pos(x, y)
    cx, cy = win.get_cursor_pos()
    return f"cursor moved to ({x},{y}); actual cursor position: ({cx},{cy})"


@mcp.tool
def click(loc, button="left", clicks=1):
    """Move to [x, y] in virtual-desktop px and click. button: left, right, middle. clicks: 1 or 2."""
    x, y = _loc(loc)
    if button not in win.BUTTONS:
        raise ValueError(f"button must be one of {sorted(win.BUTTONS)}")
    if clicks not in (1, 2):
        raise ValueError("clicks must be 1 or 2")
    cx, cy = win.click(x, y, button, clicks)
    return f"{button}-clicked {clicks}x at ({x},{y}); cursor now at ({cx},{cy})"


@mcp.tool
def type(text):
    """Type text (unicode, layout independent)."""
    win.type_text(text)
    return f"typed {len(text)} chars"


@mcp.tool
def scroll(dx=0, dy=0):
    """Scroll at the cursor. Wheel units: 120 = one notch, dy>0 up, dx>0 right."""
    win.scroll(dx, dy)
    return f"scrolled dx={dx} dy={dy}"


@mcp.tool
def hotkey(keys):
    """Press key names in order, release in reverse, e.g. ["ctrl", "shift", "t"].
    Names: letters, digits, f1-f24, enter, tab, esc, space, backspace, delete, insert,
    home, end, pageup, pagedown, up, down, left, right, shift, ctrl, alt, win, capslock."""
    win.hotkey(keys)
    return f"pressed hotkey: {'+'.join(keys)}"


def main():
    mcp.run()
