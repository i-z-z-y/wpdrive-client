# WPDrive Sync Client

WPDrive CLI for syncing WordPress via the WPDrive Sync plugin.

## Install as a CLI (recommended: pipx)
Pipx is a tool for installing Python CLI applications into isolated virtual environments.
Each CLI gets its own environment, so dependencies do not conflict.
This keeps your system Python and other projects clean.
Pipx still exposes the CLI command on your PATH.
That means you can run the command from any terminal without activating a venv.
It works on macOS, Linux, and Windows.
Pipx uses pip under the hood but manages environments for you.
Upgrades are simple because pipx tracks what it installed.
Uninstalls are clean because the environment is removed entirely.
You can install from PyPI, a local path, or a Git URL.
Using a release tag makes installs reproducible across machines.
For day-to-day use, pipx is the most reliable way to run this CLI.

### Install pipx (macOS/Linux)
```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

### Install pipx (Windows PowerShell)
```powershell
py -m pip install --user pipx
py -m pipx ensurepath
```

### Install this CLI (stable release tag, preferred)
```bash
pipx install "git+https://github.com/i-z-z-y/wpdrive-client.git@<TAG>"
```

### Install this CLI (main branch, dev/testing)
```bash
pipx install "git+https://github.com/i-z-z-y/wpdrive-client.git@main"
```

### Verify the install
```bash
wpdrive --help
```

### Upgrade
```bash
pipx upgrade wpdrive
```

### Uninstall
```bash
pipx uninstall wpdrive
```

### Optional extras
If you need the daemon support (watchdog), install with the `daemon` extra:
```bash
pipx install "git+https://github.com/i-z-z-y/wpdrive-client.git@<TAG>#egg=wpdrive[daemon]"
```
For a local checkout:
```bash
pipx install "C:\path\to\wpdrive-client[daemon]"
```

### Windows note about .exe launchers
- Windows often shows a `.exe` next to the CLI command.
- That file is usually a small launcher generated for Python console scripts.
- The launcher simply points to the Python environment created by pipx.
- It is not necessarily a compiled binary of this project.
- The actual Python code still lives in the pipx venv.
- You can inspect the venv with `pipx list`.
- Removing the tool with pipx removes the launcher too.
- Upgrading with pipx refreshes the environment behind the launcher.
- The launcher exists so the command works on PATH like any other app.
- Seeing an `.exe` is normal for Python CLI tools on Windows.
- If you prefer, you can still run the module with Python directly.
- For most users, treat the `.exe` as the standard entrypoint.

## Repeat this setup on other machines / share with friends
Export your pipx tools and restore them on another machine:
```bash
pipx list --json > pipx-tools.json
```
```bash
pipx install-all pipx-tools.json
```
This lets you replicate your installed Python CLI tools on another machine.

## Alternative installs
If you prefer not to use pipx, the options below are alternatives.

### Quick install (Windows, one-click)
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

### Quick install (macOS/Linux)
```bash
bash installer/install.sh
```

### Pip install (direct)
```bash
py -3.14 -m pip install --upgrade https://github.com/i-z-z-y/wpdrive-client/archive/refs/heads/main.zip
```

### Download Windows EXE
Latest release asset:
```
https://github.com/i-z-z-y/wpdrive-client/releases/latest/download/WPDrive-Install.exe
```

### Build Windows EXE installer
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

## License
Proprietary. Internal use only. Not licensed for public redistribution.

## Release helpers
- Checklist: `RELEASE_CHECKLIST.md`
- Version bump: `scripts\bump-version.ps1`
- CI: `.github\workflows\release.yml` builds and attaches the EXE on tag pushes
