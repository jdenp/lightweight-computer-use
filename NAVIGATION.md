# Navigation learnings

Machine-specific notes for driving this desktop: window locations, coordinates, quirks, dead ends.

## PLCnext Engineer: open project, connect, write + start

1. Launch: `start "" "C:\Program Files\Phoenix Contact\PLCnext Engineer 2026.0\PLCNENG64.exe"`.
   Startup takes ~30s here (a few minutes on the laptop). Poll for the window title
   "PLCnext Engineer" before touching anything.
2. Open the project via File > Open Project (Ctrl+O), then TYPE the full path into
   the file dialog's filename bar and press Enter, e.g.
   `C:\Repos\gutenberg\alpha-GUT-<ticket>\plc\gutenberg.pcwef`.
   Worktrees are `C:\Repos\gutenberg\alpha-GUT-*`. The start page's recent list
   truncates paths (full path only on hover), so the file dialog is the reliable route.
   Loaded = title bar becomes "PLCnext Engineer - <path>\gutenberg.pcwef".
3. Check the MESSAGES window first: yellow warnings are OK, red errors block the
   write. Double-click an error to expand it and jump to the relevant line; in
   windowed mode the pane may not be fully expanded or scrolled into view.
4. PLANT tree: click the expand arrow left of "Project", then right-click the PLC
   node "axc-f-2152-1 : AXC F 2152". Context menus are separate popup windows:
   they do not appear in PrintWindow captures of the main window. Find them with
   list_windows (PLCNENG64 HwndWrapper, small rect near the cursor) and capture the
   popup hwnd.
5. Click "Connect / Disconnect" (first item). A "SECURE DEVICE LOGIN" dialog opens:
   user admin and the password are pre-filled from the Password Manager, so just
   click OK.
6. Right-click the PLC node again and click "Write and Start Project" (F5). It is
   greyed out while the PLC is offline.
7. The menu row directly above "Write and Start Project" is "Change Password...":
   a click ~20px too high opens a "SECURE DEVICE CHANGE PASSWORD" dialog (old / new
   password for admin). That password lives in the user's Password Manager and is
   not readable here. Writing itself does not prompt for a password. Measure the
   target row's y from the captured menu image pixels before clicking.
8. The write runs without a progress dialog (finishes in a few seconds). Verify
   afterwards: the PLC node icon shows the play symbol (running) and the messages
   window has no new red errors.

Coordinates: always derive from client_rect of the current window plus image
offsets; window position changes between sessions.
