# WPDrive Sync Client

WPDrive CLI for syncing WordPress via the WPDrive Sync plugin.

## Quick install (Windows, one-click)
1) The installer resolves the latest GitHub release automatically.
   To use the bleeding-edge `main` branch, set `WPDRIVE_REPO_URL` to:
   ```
   https://github.com/i-z-z-y/wpdrive-client/archive/refs/heads/main.zip
   ```
2) Double-click `installer\install.cmd` (or run it in PowerShell).
   You can also run `installer\install-latest.ps1` to explicitly fetch the newest release.

Optional env vars:
- WPDRIVE_REPO_URL  (override repo URL)
- WPDRIVE_PY_EXE    (full path to python.exe)
- WPDRIVE_PY_CMD    (example: "py -3.14")
- WPDRIVE_SCOPE     (auto|user|system)

Note: If you run as Admin, the installer will add the scripts path to the machine PATH. Otherwise it adds it to your user PATH.

## Quick install (macOS/Linux)
```bash
bash installer/install.sh
```

## Pip install (direct)
```bash
py -3.14 -m pip install --upgrade https://github.com/i-z-z-y/wpdrive-client/archive/refs/heads/main.zip
```

## Download Windows EXE
Latest release asset:
```
https://github.com/i-z-z-y/wpdrive-client/releases/latest/download/WPDrive-Install.exe
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

## Release helpers
- Checklist: `RELEASE_CHECKLIST.md`
- Version bump: `scripts\bump-version.ps1`
- CI: `.github\workflows\release.yml` builds and attaches the EXE on tag pushes
