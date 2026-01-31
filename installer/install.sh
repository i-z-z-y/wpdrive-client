#!/usr/bin/env bash
set -euo pipefail

REPO_OWNER="i-z-z-y"
REPO_NAME="wpdrive-client"
REPO_ZIP_MAIN="https://github.com/$REPO_OWNER/$REPO_NAME/archive/refs/heads/main.zip"
REPO_API_LATEST="https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/releases/latest"

REPO_URL="${WPDRIVE_REPO_URL:-}"

PY_CMD=${WPDRIVE_PY_CMD:-python3}

if ! command -v "$PY_CMD" >/dev/null 2>&1; then
  echo "Python not found. Install Python 3.9+ and retry."
  exit 1
fi

if [[ -z "$REPO_URL" ]]; then
  REPO_URL=$("$PY_CMD" - <<'PY'
import json
import urllib.request

api = "https://api.github.com/repos/i-z-z-y/wpdrive-client/releases/latest"
req = urllib.request.Request(api, headers={"Accept": "application/vnd.github+json"})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = resp.read()
    obj = json.loads(data)
    print(obj.get("zipball_url", ""))
except Exception:
    print("")
PY
)
  if [[ -z "$REPO_URL" ]]; then
    echo "Warning: could not resolve latest release; falling back to main branch zip."
    REPO_URL="$REPO_ZIP_MAIN"
  fi
fi

"$PY_CMD" -m pip install --upgrade "$REPO_URL"

USER_BASE=$($PY_CMD -c "import site; print(site.USER_BASE)")
BIN="$USER_BASE/bin"

if [[ ":$PATH:" != *":$BIN:"* ]]; then
  echo "Add this to your shell profile to use wpdrive globally:"
  echo "  export PATH=\"$BIN:$PATH\""
fi

cat <<EOF

Next steps:
  1) wpdrive init --root /path/to/sync --url http://localhost --user your-user --app-password "your app password"
  2) wpdrive sync --root /path/to/sync
  3) Daemon: wpdrive daemon --interval 10 --root /path/to/sync
EOF
