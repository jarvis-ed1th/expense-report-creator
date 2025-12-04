#!/bin/bash

# --- 1. CONFIGURATION DES CHEMINS ---
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
SYSTEM_DIR="$BASE_DIR/.system"
VENV_DIR="$BASE_DIR/.venv"
REQ_FILE="$SYSTEM_DIR/requirements.txt"
SCRIPT_PY="$SYSTEM_DIR/src/expense_report_creator/main.py"
source $VENV_DIR/bin/activate


# On définit où on veut installer Tectonic (dans le dossier bin du venv)
TECTONIC_BIN="$VENV_DIR/bin/tectonic"

# --- 2. VÉRIFICATIONS PRÉLIMINAIRES ---
if ! command -v python3 &> /dev/null; then
    echo "[ERREUR] Python 3 n'est pas installé."
    exit 1
fi

if ! command -v curl &> /dev/null; then
    echo "[ERREUR] 'curl' est nécessaire pour télécharger les composants."
    exit 1
fi

# --- 3. CRÉATION DE L'ENVIRONNEMENT VIRTUEL ---
if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] Premier lancement détecté. Configuration en cours..."
    python3 -m venv "$VENV_DIR"

    echo "Installation des dépendances Python..."
    "$VENV_DIR/bin/pip" install -r "$REQ_FILE"
fi

# --- 4. INSTALLATION / VÉRIFICATION DE TECTONIC ---
# Si le fichier tectonic n'existe pas dans notre venv, on l'installe
if [ ! -f "$TECTONIC_BIN" ]; then
    echo "[INFO] Installation du moteur LaTeX (Tectonic)..."
    echo "Cela peut prendre quelques secondes..."

    # Script officiel d'installation de Tectonic
    # --install-dir force l'installation dans le dossier bin de notre venv
    curl --proto '=https' --tlsv1.2 -fsSL https://drop-sh.fullyjustified.net |sh

    if [ $? -eq 0 ]; then
        mv tectonic $VENV_DIR/bin/
        echo "Moteur LaTeX installé avec succès."
    else
        echo "[ERREUR] Échec du téléchargement de Tectonic."
        exit 1
    fi
fi

# --- 5. LANCEMENT DU PROGRAMME ---
echo "Lancement du générateur..."

# Note : Comme tectonic est dans le dossier bin du venv, Python pourra le trouver
# s'il cherche dans le PATH de l'environnement actif, ou on peut passer le chemin.
"$VENV_DIR/bin/python3" "$SCRIPT_PY"
