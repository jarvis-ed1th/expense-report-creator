import os
import subprocess
import platform
from datetime import datetime

import jinja2
import pandas as pd

# Configuration des chemins
ROOT_DIR = os.getcwd()
ASSETS_DIR = os.path.join(ROOT_DIR, ".system", "assets")
OUTPUT_PDF_DIR = os.path.join(ROOT_DIR, "SORTIE_PDF")
OUTPUT_TEX_DIR = os.path.join(ROOT_DIR, "SORTIE_LATEX")
A_MODIFIER_DIR = os.path.join(ROOT_DIR, "A_MODIFIER")
DATA_FILE = os.path.join(A_MODIFIER_DIR, "data.xlsx")

# Créer le dossier output s'il n'existe pas
os.makedirs(OUTPUT_PDF_DIR, exist_ok=True)
os.makedirs(OUTPUT_TEX_DIR, exist_ok=True)

def load_data():
    """Enregistre les données de data.xlsx.

    Récupération des informations de l'association, du bénéficiaire et du trésorier
    dans un dataframe, ainsi que des lignes de frais dans une liste de dictionnaires.

    Returns:
        data_dict (dict): Informations sur l'association, le bénéficiaire et le
            trésorier.
        items (list of dict): Liste de dictionnaire contenant les champs des colonnes
            et les valeurs associées, pour chacune des lignes de la note de frais.
        final_price (float): Montant du remboursement final.
    """

    # Lecture des informations du Tableau de bord (Colonnes F et G).
    df_data = pd.read_excel(
        DATA_FILE, sheet_name="Tableau de bord", usecols="F:G", names=["key", "value"]
    )

    # Création du dictionnaire en utilisant les clés non-vides.
    data_dict = {}
    for _, row in df_data.iterrows():
        if pd.notna(row["key"]):
            # Utilisation de strip pour supprimer les espaces involontaires.
            key = str(row["key"]).strip()
            val = row["value"] if pd.notna(row["value"]) else ""
            data_dict[key] = val

    # Lecture des lignes de frais et enregistrement dans une liste lorsque "Référence"
    # non vide.
    df_items = pd.read_excel(DATA_FILE, sheet_name="Tableau de bord", usecols="A:D")

    items = []
    final_price = 0.0

    for _, row in df_items.iterrows():
        if pd.notna(row["Référence"]):
            quantity = row["Quantité"] if pd.notna(row["Quantité"]) else 0
            unit_price = row["Prix unitaire"] if pd.notna(row["Prix unitaire"]) else 0
            total_price = row["Prix total"] if pd.notna(row["Prix total"]) else 0

            items.append(
                {
                    "quantity": int(quantity),
                    "reference": row["Référence"],
                    # :.2f permet le formatage d'un float (f) de 2 caractères (2) après la virgule (.)
                    "unit_price": f"{unit_price:.2f}",
                    "total_price": f"{total_price:.2f}",
                }
            )

            final_price += float(total_price)

    return data_dict, items, final_price


def load_receipts():
    """Sauvegarde les chemins d'accès aux justificatifs.

    Returns:
        receipt_file_paths (list of str): Liste des chemins des fichiers
            justificatifs à inclure dans le rapport LaTeX.
    """
    RECEIPT_DIR = os.path.join(A_MODIFIER_DIR, "justificatifs")
    receipt_file_paths = []

    for file in os.listdir(RECEIPT_DIR):
        path = os.path.join(RECEIPT_DIR, file)
        if os.path.isfile(path):
            receipt_file_paths.append(path.replace('\\', '/'))

    return receipt_file_paths


def generate_latex(data_dict, items, final_price, receipt_file_paths):
    """Création d'un fichier latex à partir des données fournies.

    Cette fonction utilise le moteur de template Jinja2 pour injecter les données
    fournies (détails de l'association, bénéficiaire, items de dépenses, etc.) dans un
    template LaTeX prédéfini ('export-report-template.tex').

    Args:
        data_dict (dict): Informations sur l'association, le bénéficiaire et le
            trésorier.
        items (list of dict): Liste de dictionnaire contenant les champs des colonnes
            et les valeurs associées, pour chacune des lignes de la note de frais.
        final_price (float): Montant du remboursement final.
        receipt_file_paths (list of str): Liste des chemins des fichiers
            justificatifs à inclure dans le rapport LaTeX.

    Returns:
        str: La note de frais complète rendue au format code LaTeX, prête à
            être enregistrée dans un fichier .tex.
    """

    # Configuration de Jinja pour LaTeX (syntaxe personnalisée pour éviter les conflits avec {})
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(ASSETS_DIR),
        block_start_string=r"\BLOCK{",
        block_end_string="}",
        variable_start_string=r"\VAR{",
        variable_end_string="}",
        comment_start_string=r"\#{",
        comment_end_string="}",
        trim_blocks=True,
        autoescape=False,
    )

    template = env.get_template("export-report-template.tex")

    # Création d'un dictionnaire pour récupérer les valeurs du dictionnaire contenant
    # les clés en français, les items et les chemins des justificatifs, et les
    # enregistrer avec leur valeur utilisable et des clés conventionnelles.
    context = {
        "association_adress_1": data_dict.get("Adresse de l'association (partie 1)"),
        "association_adress_2": data_dict.get("Adresse de l'association (partie 2)"),
        "signature_location": data_dict.get("Fait à", "Toulouse"),
        "association_name": data_dict.get("Nom de l'association"),
        "association_email": data_dict.get("Email de l'association"),
        "mandate": data_dict.get("Mandat"),
        "treasurer": data_dict.get("Trésorier"),
        "beneficiary_name": data_dict.get(
            "Bénéficiaire (à remplir sur la feuille suivante)"
        ),
        "refund_mod": data_dict.get("Mode de remboursement"),
        "attachment_list": data_dict.get(
            "Noms pièces jointes (séparées par une virgule)"
        ),
        "ER_number": data_dict.get("Numéro de la note de frais"),
        "beneficiary_adress_1": data_dict.get("Adresse (partie 1)"),
        "beneficiary_adress_2": data_dict.get("Adresse (partie 2)"),
        "beneficiary_phone": data_dict.get("Téléphone"),
        "beneficiary_iban": data_dict.get(
            "IBAN (remplissage auto à partir du bénéficiaire)", ""
        ),
        "items": items,
        "final_price": f"{final_price:.2f}",
        "receipt_files": receipt_file_paths,
        "date": datetime.now().strftime("%d/%m/%Y"),
    }

    # Chemin de la signature si le nom est renseigné
    if data_dict.get("Nom du fichier signature (vide si pas)") != "":
        context["signature_path"] = os.path.join(
            A_MODIFIER_DIR, data_dict.get("Nom du fichier signature (vide si pas)")
        ).replace('\\', '/')
    else:
        context["signature_path"] = ""

    # Chemin du logo si le nom est renseigné
    if data_dict.get("Nom du fichier logo (vide si pas)") != "":
        context["logo_path"] = os.path.join(
            A_MODIFIER_DIR, data_dict.get("Nom du fichier logo (vide si pas)")
        ).replace('\\', '/')
    else:
        context["logo_path"] = ""

    return template.render(context)


def export_tex_pdf(tex_content, ER_number, beneficiary_name):
    """Créer un fichier LaTeX à partir du contenu, et le compile en PDF.

    Création de 2 fichiers dans des répertoires différents, un pour le PDF compilé
    en version finale via tectonic, et un pour le fichier LaTeX source permettant de
    modifier facilement la note de frais via un outil externe comme overleaf.

    Args:
        tex_content (str): La note de frais complète au format code LaTeX.
        ER_number (int): Numéro unique de la note de frais.
        beneficiary_name (str): Nom du bénéficiaire (utilisé pour le nom
            du fichier).
    """

    generated_tex = os.path.join(OUTPUT_TEX_DIR, "temp.tex")
    generated_pdf = os.path.join(OUTPUT_PDF_DIR, "temp.pdf")
    output_PDF_filename = f"{ER_number:03d} - Note de frais ({beneficiary_name}).pdf"
    output_TEX_filename = f"{ER_number:03d} - Note de frais ({beneficiary_name}).tex"
    # padding de 3 caractère, remplissage avec "0", sur des nombres décimaux (d)
    final_pdf = os.path.join(OUTPUT_PDF_DIR, output_PDF_filename)
    final_tex = os.path.join(OUTPUT_TEX_DIR, output_TEX_filename)

    # Écriture du fichier .tex temporaire
    with open(generated_tex, "w", encoding="utf-8") as file:
        file.write(tex_content)

    # Vérifie le système d'exploitation et adapte le chemin en fonction.
    if platform.system() == "Windows":
        TECTONIC_PATH = os.path.join(ROOT_DIR, ".venv", "Scripts", "tectonic.exe")
    else:
        TECTONIC_PATH = os.path.join(ROOT_DIR, ".venv", "bin", "tectonic")

    try:
        subprocess.run(
            [TECTONIC_PATH, "-o", OUTPUT_PDF_DIR, generated_tex],
            check=True,  # Lève une erreur si le script plante
            capture_output=True,  # Rend tectonic silencieux
            text=True,  # Permet de lire la sortie comme du texte (string)
        )

        if os.path.exists(generated_pdf):
            if os.path.exists(final_pdf):
                os.remove(final_pdf)
            os.rename(generated_pdf, final_pdf)

        if os.path.exists(generated_tex):
            if os.path.exists(final_tex):
                os.remove(final_tex)
            os.rename(generated_tex, final_tex)

        # Nettoyage des fichiers temporaires (.aux, .log)
        for ext in [".aux", ".log"]:
            f = os.path.join(OUTPUT_TEX_DIR, f"temp{ext}")
            if os.path.exists(f):
                os.remove(f)

    except Exception as e:
        print(f"Erreur: {e}")
        input("\nAppuyez sur Entrée pour quitter...")


if __name__ == "__main__":
    try:
        data_dict, items, final_price = load_data()
        receipt_files_path = load_receipts()
        latex_code = generate_latex(data_dict, items, final_price, receipt_files_path)

        beneficiary_name = data_dict.get(
            "Bénéficiaire (à remplir sur la feuille suivante)"
        )
        ER_number = data_dict.get("Numéro de la note de frais")
        export_tex_pdf(latex_code, ER_number, beneficiary_name)

    except Exception as e:
        print(f"Une erreur est survenue : {e}")
        input("\nAppuyez sur Entrée pour quitter...")
