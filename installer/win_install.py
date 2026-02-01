# Windows EXE installer entrypoint (build with PyInstaller)
import json
import os
import subprocess
import sys
import urllib.request

REPO_OWNER = "i-z-z-y"
REPO_NAME = "wpdrive-client"
REPO_ZIP_MAIN = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/archive/refs/heads/main.zip"
REPO_API_LATEST = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"


def resolve_repo_url() -> str:
    override = os.environ.get("WPDRIVE_REPO_URL")
    if override:
        return override
    try:
        req = urllib.request.Request(
            REPO_API_LATEST,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "wpdrive-installer",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        url = data.get("zipball_url")
        if url:
            return url
    except Exception:
        pass
    print("[wpdrive-installer] Warning: could not resolve latest release; using main branch zip.")
    return REPO_ZIP_MAIN


REPO_URL = resolve_repo_url()

# Resolve python command for install (prefer py -3.14)
if os.environ.get("WPDRIVE_PY_EXE"):
    py_cmd = [os.environ["WPDRIVE_PY_EXE"]]
elif os.environ.get("WPDRIVE_PY_CMD"):
    py_cmd = os.environ["WPDRIVE_PY_CMD"].split()
else:
    try:
        subprocess.run(["py", "-3.14", "-V"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        py_cmd = ["py", "-3.14"]
    except Exception:
        py_cmd = ["python"]

scope = os.environ.get("WPDRIVE_SCOPE", "auto").lower()
if scope not in {"auto", "user", "system"}:
    scope = "auto"

print(f"[wpdrive-installer] Installing from {REPO_URL}")
install_args = ["-m", "pip", "install", "--upgrade", REPO_URL]
if scope == "user":
    install_args = ["-m", "pip", "install", "--upgrade", "--user", REPO_URL]
elif scope == "system":
    try:
        import ctypes
        if not bool(ctypes.windll.shell32.IsUserAnAdmin()):
            print("[wpdrive-installer] System scope requested but not running as admin. Proceeding with default install.")
    except Exception:
        pass

subprocess.run(py_cmd + install_args, check=True)

# Determine scripts path
scripts_path = subprocess.check_output(
    py_cmd + ["-c", "import sysconfig; print(sysconfig.get_path('scripts'))"],
    text=True,
).strip()
user_base = subprocess.check_output(
    py_cmd + ["-c", "import site; print(site.USER_BASE)"],
    text=True,
).strip()
user_scripts = os.path.join(user_base, "Scripts")

script_dir = None
install_scope = "unknown"
if os.path.exists(os.path.join(scripts_path, "wpdrive.exe")):
    script_dir = scripts_path
    install_scope = "system"
elif os.path.exists(os.path.join(user_scripts, "wpdrive.exe")):
    script_dir = user_scripts
    install_scope = "user"

# Update PATH (user or machine if admin)
if script_dir:
    try:
        import ctypes
        import winreg

        is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
        target = winreg.HKEY_CURRENT_USER
        if install_scope == "system" and is_admin:
            target = winreg.HKEY_LOCAL_MACHINE

        key_path = r"Environment"
        with winreg.OpenKey(target, key_path, 0, winreg.KEY_READ) as k:
            current, _ = winreg.QueryValueEx(k, "Path")

        paths = [p for p in current.split(";") if p]
        if script_dir not in paths:
            new_value = current + (";" if current else "") + script_dir
            with winreg.OpenKey(target, key_path, 0, winreg.KEY_SET_VALUE) as k:
                winreg.SetValueEx(k, "Path", 0, winreg.REG_EXPAND_SZ, new_value)
            print("[wpdrive-installer] Added to PATH.")
    except Exception as e:
        print(f"[wpdrive-installer] PATH update skipped: {e}")

print("\nNext steps:")
print("  1) wpdrive init --root C:\\path\\to\\sync --url http://localhost --user your-user --app-password 'your app password'")
print("  2) wpdrive sync --root C:\\path\\to\\sync")
print("  3) Daemon: wpdrive daemon --interval 10 --root C:\\path\\to\\sync")
