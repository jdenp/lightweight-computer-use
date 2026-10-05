# PLCnext Engineer: open project, connect, write + start

All coordinates below are image-relative for the 1024x704 Engineer window.
Always derive virtual coords from client_rect of the current window; the window
opens at a different position each session (seen: (-1800,100), (-1610,152)).
The app sits on the left display: capture with the window parameter (PrintWindow).

## Steps

1. Check the app is open: window title "PLCnext Engineer" (no project loaded yet).
   If absent, launch: `start "" "C:\Program Files\Phoenix Contact\PLCnext Engineer 2026.0\PLCNENG64.exe"`.
   Startup takes ~30s here (a few minutes on the laptop). Poll for the title.
2. File menu is at image (28,37). Its popup is a separate window (248x283);
   "Open Project..." is the second row, ~y=31 in the popup (Ctrl+O).
3. The Open file dialog (#32770, 960x540, opens over the main window) has the
   filename bar focused. TYPE the full path and press Enter:
   `C:\Repos\gutenberg\alpha-GUT-<ticket>\plc\gutenberg.pcwef`
   Worktrees are `C:\Repos\gutenberg\alpha-GUT-*`. The start page's recent list
   truncates paths (full path only on hover), so the file dialog is the reliable route.
   Loaded = title bar becomes "PLCnext Engineer - <path>\gutenberg.pcwef".
4. Check MESSAGES (bottom-center pane) and the status bar (bottom right,
   "N errors, N warnings"): yellow warnings are OK, red errors block the write.
   Double-click an error to expand it and jump to the relevant line; in windowed
   mode the pane may not be fully expanded or scrolled into view.
   GUT-305 baseline: 0 errors, 10 warnings (SEM2001 'Enable' ambiguous,
   SEM2019 global FB, SEM2004 HAL.TcStabilityName, SEM2005 Service.FB_Ala* /
   Domain.TFF.FB*).
5. PLANT tree (left pane): "Project" node at image (75,172), expand arrow at
   (24,172). PLC node "axc-f-2152-1 : AXC F 2152" at (110,186), one row below.
   Right-click it. Context menus are separate popup windows (PLCNENG64
   HwndWrapper, 415x325, at the cursor): they do not appear in PrintWindow
   captures of the main window. Find with list_windows, capture the popup hwnd.
6. PLC context menu rows (popup-relative y, measured from pixels):
   - 14  Connect / Disconnect
   - 58  Debug On / Off
   - 80  Logon / Logoff
   - 102 Change Password...
   - 125 Write and Start Project (F5)
   - 147 Write and Start Project (with Sources) (Ctrl+F5)
   - 169 Write and Start Project Changes (Shift+F5)
   - 192 Write and Start Project Changes (with Sources)
   - 283 Replace (Ctrl+Shift+R)
   - 323 Delete (Del)
   Greyed rows (do not target): Redundancy Role, both "incl. Safety" items,
   Confirm Safety Device.
7. Click "Connect / Disconnect" (y=14). A "SECURE DEVICE LOGIN" dialog opens
   (480x487): user admin and the password are pre-filled from the Password
   Manager, so just click OK at popup-relative (350,466).
8. Right-click the PLC node again, click "Write and Start Project" (y=125).
   It is greyed out while the PLC is offline.
9. Verify: the write runs without a progress dialog (a few seconds). The node
   icon shows the play symbol (running) and the status bar has no new red errors.

## Node icon states (right of the node text)

- grey shield: offline
- teal shield: connected, stopped
- teal shield + play triangle: connected, running

## Gotchas

- "Change Password..." (y=102) sits directly above "Write and Start Project"
  (y=125): a click ~20px too high opens "SECURE DEVICE CHANGE PASSWORD"
  (420x282, Cancel at popup-relative (365,262)). Its old/new password lives in
  the user's Password Manager and is not readable here. Writing itself never
  prompts for a password. Measure the target row from the captured menu image
  before clicking.
- "Connect / Disconnect" is a TOGGLE: clicking it while connected disconnects
  (write items go grey). Check the icon state before clicking.
- Menu row positions are only as good as the last capture: re-measure from
  pixels if the menu layout ever changes.
- The window can vanish between sessions (user closed the app): re-run step 1.
