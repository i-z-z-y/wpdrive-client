#!/usr/bin/env bash
set -euo pipefail

REPO_URL_DEFAULT="https://github.com/i-z-z-y/wpdrive-client/archive/refs/heads/main.zip"
REPO_URL="${WPDRIVE_REPO_URL:-$REPO_URL_DEFAULT}"

if [[ "$REPO_URL" == *"YOUR_GITHUB_USER"* ]]; then
  echo "Set WPDRIVE_REPO_URL or edit installer/install.sh before running."
  exit 1
fi

PY_CMD=${WPDRIVE_PY_CMD:-python3}

if ! command -v "$PY_CMD" >/dev/null 2>&1; then
  echo "Python not found. Install Python 3.9+ and retry."
  exit 1
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
