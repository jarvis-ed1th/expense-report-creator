# Chemins relatifs
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
SYSTEM_DIR="$BASE_DIR/.system"
VENV_DIR="$BASE_DIR/.venv"
REQ_FILE="$SYSTEM_DIR/requirements.txt"
SCRIPT_PY="$SYSTEM_DIR/src/expense_report_creator/main.py"

echo "Lancement du générateur..."
"$VENV_DIR/bin/python3" "$SCRIPT_PY"
