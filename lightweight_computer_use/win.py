"""Win32 helpers: monitors, window rects, SendInput mouse and keyboard."""
import ctypes
import time
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)

ULONG_PTR = ctypes.c_uint64 if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_uint32

# fixed gap between consecutive input actions; pairs inside one call (double-click, key chord) stay tight
STEP_DELAY_S = 0.2


def settle():
    time.sleep(STEP_DELAY_S)


MONITORENUMPROC = ctypes.WINFUNCTYPE(
    wintypes.BOOL, wintypes.HDC, wintypes.HANDLE, ctypes.POINTER(wintypes.RECT), wintypes.LPARAM
)

ENUMWINPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def list_monitors():
    """Monitors as {left, top, right, bottom, primary}, sorted left to right."""
    # python 3.13 ctypes swaps the first two callback params, so the
    # hmon slot is unusable: geometry comes from lprcMonitor, and the
    # primary display is always the one at the virtual screen origin
    out = []

    def cb(hdc, hmon, lprc, lparam):
        r = lprc.contents
        out.append(
            {
                "left": r.left,
                "top": r.top,
                "right": r.right,
                "bottom": r.bottom,
                "primary": r.left == 0 and r.top == 0,
            }
        )
        return True

    user32.EnumDisplayMonitors(None, None, MONITORENUMPROC(cb), 0)
    out.sort(key=lambda m: (m["left"], m["top"]))
    return out


def window_title(hwnd):
    n = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value


def find_window(window):
    """hwnd + title for a decimal hwnd string, or first visible window whose title contains window (case-insensitive)."""
    if window.isdigit():
        hwnd = int(window)
        if not user32.IsWindow(hwnd):
            raise ValueError(f"not a window: hwnd {hwnd}")
        return hwnd, window_title(hwnd)

    found = []

    def cb(hwnd, lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        t = window_title(hwnd)
        if t and window.lower() in t.lower():
            found.append((hwnd, t))
            return False
        return True

    user32.EnumWindows(ENUMWINPROC(cb), 0)
    if not found:
        raise ValueError(f"no visible window with title containing {window!r}")
    return found[0]


def list_windows():
    """All visible top-level windows: [(hwnd, class, (left, top, w, h), title), ...] sorted top to bottom. Includes popups (menus, dialogs)."""
    out = []

    def cb(hwnd, lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        r = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(r))
        w = r.right - r.left
        h = r.bottom - r.top
        if w > 50 and h > 20:
            cls = ctypes.create_unicode_buffer(64)
            user32.GetClassNameW(hwnd, cls, 64)
            out.append((hwnd, cls.value[:40], (r.left, r.top, w, h), window_title(hwnd)[:80]))
        return True

    user32.EnumWindows(ENUMWINPROC(cb), 0)
    out.sort(key=lambda t: (t[2][1], t[2][0]))
    return out


def client_rect(hwnd):
    """Client area as (x, y, w, h) in virtual-desktop px."""
    r = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(r))
    pt = wintypes.POINT(r.left, r.top)
    user32.ClientToScreen(hwnd, ctypes.byref(pt))
    return (pt.x, pt.y, r.right - r.left, r.bottom - r.top)


def get_cursor_pos():
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return (pt.x, pt.y)


def set_cursor_pos(x, y):
    if not user32.SetCursorPos(x, y):
        raise ctypes.WinError(ctypes.get_last_error())


# --- SendInput ---

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x1000

BUTTONS = {
    "left": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP),
    "right": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP),
    "middle": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP),
}

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class _INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUT_UNION)]


INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(_INPUT), ctypes.c_int]
user32.SendInput.restype = wintypes.UINT


def send_inputs(inputs):
    arr = (_INPUT * len(inputs))(*inputs)
    sent = user32.SendInput(len(inputs), arr, ctypes.sizeof(_INPUT))
    if sent != len(inputs):
        raise ctypes.WinError(ctypes.get_last_error())


def _mouse(flags, data=0):
    i = _INPUT(type=INPUT_MOUSE)
    i.u.mi.dwFlags = flags
    # wheel deltas are signed, the struct field is not
    i.u.mi.mouseData = data & 0xFFFFFFFF
    return i


def _key(vk, up=False, char=None):
    i = _INPUT(type=INPUT_KEYBOARD)
    i.u.ki.wVk = vk
    i.u.ki.dwFlags = KEYEVENTF_KEYUP if up else 0
    if char:
        i.u.ki.dwFlags |= KEYEVENTF_UNICODE
        i.u.ki.wScan = ord(char)
    return i


def click(x, y, button="left", clicks=1):
    """Move then press at (x, y); returns the final cursor position."""
    settle()
    set_cursor_pos(x, y)
    down, up = BUTTONS[button]
    send_inputs([_mouse(down) for _ in range(clicks)] + [_mouse(up) for _ in range(clicks)])
    return get_cursor_pos()


def scroll(dx=0, dy=0):
    """Wheel units: 120 = one notch, dy>0 up, dx>0 right."""
    if dx == 0 and dy == 0:
        raise ValueError("dx and dy are both zero")
    settle()
    inputs = []
    if dy:
        inputs.append(_mouse(MOUSEEVENTF_WHEEL, dy))
    if dx:
        inputs.append(_mouse(MOUSEEVENTF_HWHEEL, dx))
    send_inputs(inputs)


def type_text(text):
    """Unicode input: any script, no layout dependency."""
    settle()
    send_inputs([c for ch in text for c in (_key(0, char=ch), _key(0, up=True, char=ch))])


VK = {
    "backspace": 0x08,
    "tab": 0x09,
    "enter": 0x0D,
    "return": 0x0D,
    "shift": 0x10,
    "ctrl": 0x11,
    "control": 0x11,
    "alt": 0x12,
    "menu": 0x12,
    "capslock": 0x14,
    "esc": 0x1B,
    "escape": 0x1B,
    "space": 0x20,
    "pageup": 0x21,
    "pgup": 0x21,
    "pagedown": 0x22,
    "pgdn": 0x22,
    "end": 0x23,
    "home": 0x24,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
    "insert": 0x2D,
    "delete": 0x2E,
    "del": 0x2E,
    "win": 0x5B,
    "windows": 0x5B,
}
VK.update({f"f{i}": 0x6F + i for i in range(1, 25)})
VK.update({c: 0x40 + i for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")})
VK.update({d: 0x30 + int(d) for d in "0123456789"})


def hotkey(names):
    """Press each key, release in reverse order."""
    vks = []
    for n in names:
        vk = VK.get(n.lower())
        if vk is None:
            raise ValueError(f"unknown key: {n!r}")
        vks.append(vk)
    settle()
    send_inputs([_key(v) for v in vks] + [_key(v, up=True) for v in reversed(vks)])
