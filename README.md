# WPDrive Sync Client

WPDrive CLI for syncing WordPress via the WPDrive Sync plugin.

## Quick install (Windows, one-click)
1) The installer is pinned to the latest release by default (v1.0.1).
   To use the bleeding-edge `main` branch, change `REPO_URL` in `installer\install.ps1` to:
   ```
   https://github.com/i-z-z-y/wpdrive-client/archive/refs/heads/main.zip
   ```
2) Double-click `installer\install.cmd` (or run it in PowerShell).

Optional env vars:
- WPDRIVE_REPO_URL  (override repo URL)
- WPDRIVE_PY_EXE    (full path to python.exe)
- WPDRIVE_PY_CMD    (example: "py -3.14")
- WPDRIVE_SCOPE     (auto|user|system)

Note: If you run as Admin, the installer will add the scripts path to the machine PATH. Otherwise it adds it to your user PATH.

## Quick install (macOS/Linux)
```bash
export WPDRIVE_REPO_URL="https://github.com/i-z-z-y/wpdrive-client/archive/refs/tags/v1.0.1.zip"
bash installer/install.sh
```

## Pip install (direct)
```bash
py -3.14 -m pip install --upgrade https://github.com/i-z-z-y/wpdrive-client/archive/refs/tags/v1.0.1.zip
```

## Download Windows EXE
Release asset (pinned to v1.0.0):
```
https://github.com/i-z-z-y/wpdrive-client/releases/download/v1.0.1/WPDrive-Install.exe
```

## Build Windows EXE installer
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File installer\build-exe.ps1
```
Output:
`installer\dist\WPDrive-Install.exe`

Note: The EXE still expects Python to be installed on the target machine.

## Usage
Initialize a sync folder:
```bash
wpdrive init --root "C:\path\to\sync_root" --url "http://localhost" --user "wpdrive-sync" --app-password "xxxx xxxx xxxx xxxx"
```

One-shot sync:
```bash
wpdrive sync --root "C:\path\to\sync_root"
```

Daemon mode (polling):
```bash
wpdrive daemon --interval 10 --root "C:\path\to\sync_root"
```

## Notes
- Uses WordPress Application Passwords (Basic Auth).
- Chunked uploads with auto-backoff on 413/timeouts.
- Pull-first then push, to reduce conflicts.
- Optional watchdog dependency: `pip install .[daemon]`.
