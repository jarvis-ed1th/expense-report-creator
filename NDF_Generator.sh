#!/bin/bash

# Configuration des chemins
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
SYSTEM_DIR="$BASE_DIR/.system"
VENV_DIR="$BASE_DIR/.venv"
REQ_FILE="$SYSTEM_DIR/requirements.txt"
SCRIPT_PY="$SYSTEM_DIR/src/expense-report-creator/main.py"

# Chemin de destination du programme tectonic pour exporter le LaTeX en PDF
TECTONIC_BIN="$VENV_DIR/bin/tectonic"

# Fonction pour gérer l'arrêt du prompt en cas d'erreur
fermer_sur_erreur() {
    echo ""
    echo "[Erreur] $1"
    echo ""
    read -p "Appuyez sur entrée pour fermer la fenêtre"
    exit 1
}

# Présence de python3
if ! command -v python3 &> /dev/null; then
    fermer_sur_erreur "Python 3 n'est pas installé."
fi

# Configuration de l'environnement virtuel s'il n'existe pas
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install -r "$REQ_FILE"
fi

# Installation de tectonic si non-installé
if [ ! -f "$TECTONIC_BIN" ]; then

    # Vérifier que curl est installé pour pouvoir installer tectonic
    if ! command -v curl &> /dev/null; then
        fermer_sur_erreur "curl n'est pas installé"
    fi

    echo "[INFO] Installation du moteur LaTeX (Tectonic)..."
    echo "Cela peut prendre quelques secondes..."

    # Script officiel d'installation de Tectonic
    curl --proto '=https' --tlsv1.2 -fsSL https://drop-sh.fullyjustified.net |sh

    if [ $? -eq 0 ]; then
        mv tectonic $VENV_DIR/bin/
        echo "Moteur LaTeX installé avec succès."
    else
        fermer_sur_erreur "Échec du téléchargement de Tectonic."
    fi
fi

# Lancement du programme
"$VENV_DIR/bin/python3" "$SCRIPT_PY"
