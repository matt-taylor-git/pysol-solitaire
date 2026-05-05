#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ -x "pysol_venv/bin/python" ]]; then
  exec pysol_venv/bin/python main.py "$@"
fi

if python3 -c "import PySide6" >/dev/null 2>&1; then
  exec python3 main.py "$@"
fi

if command -v pyenv >/dev/null 2>&1 && pyenv versions --bare | grep -qx "3.13.0"; then
  export PYENV_VERSION=3.13.0
  export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}pysol_venv/lib/python3.13/site-packages"
  exec python3.13 main.py "$@"
fi

cat >&2 <<'EOF'
Unable to find a Python environment with PySide6.

Try one of these:
  python3 -m venv pysol_venv
  pysol_venv/bin/python -m pip install -r requirements.txt
  ./run.sh
EOF
exit 1
