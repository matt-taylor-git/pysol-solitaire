#!/usr/bin/env bash
# PySol launcher script
# This script attempts to find and execute the PySol application with appropriate Python environment

# Exit immediately if a command exits with a non-zero status
set -euo pipefail

# Change to the directory where this script is located
cd "$(dirname "$0")"

# Try using the virtual environment's Python (if it exists and is executable)
if [[ -x "pysol_venv/bin/python" ]]; then
  exec pysol_venv/bin/python main.py "$@"
fi

# Try using system's python3 if PySide6 is already installed
if python3 -c "import PySide6" >/dev/null 2>&1; then
  exec python3 main.py "$@"
fi

# Try using pyenv to set Python 3.13.0 if available
if command -v pyenv >/dev/null 2>&1 && pyenv versions --bare | grep -qx "3.13.0"; then
  export PYENV_VERSION=3.13.0
  export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}pysol_venv/lib/python3.13/site-packages"
  exec python3.13 main.py "$@"
fi

# If none of the above methods work, display an error message
cat >&2 <<'EOF'
Unable to find a Python environment with PySide6.

Try one of these:
  python3 -m venv pysol_venv
  pysol_venv/bin/python -m pip install -r requirements.txt
  ./run.sh
EOF
exit 1
