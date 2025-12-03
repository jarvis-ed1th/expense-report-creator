import os
import subprocess
from datetime import datetime

import jinja2
import pandas as pd

# Configuration des chemins
ROOT_DIR = os.getcwd()
ASSETS_DIR = os.path.join(ROOT_DIR, ".system", "assets")
OUTPUT_DIR = os.path.join(ROOT_DIR, "SORTIE_PDF")
A_MODIFIER_DIR = os.path.join(ROOT_DIR, "A_MODIFIER")
RECEIPT_DIR = os.path.join(A_MODIFIER_DIR, "justificatifs")
DATA_FILE = os.path.join(A_MODIFIER_DIR, "data.xlsx")

# Créer le dossier output s'il n'existe pas
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_data():
    """Lit le fichier Excel et sépare les items des métadonnées."""

    # 1. Lire les métadonnées (Colonnes F et G - Index 5 et 6)
    # On suppose que les données clés/valeurs commencent ligne 2 (index 1)
    df_data = pd.read_excel(
        DATA_FILE,
        sheet_name="Tableau de bord",
        usecols="F:G",
    )

    df_data.columns = ["key", "value"]

    # Nettoyage des métadonnées pour en faire un dictionnaire
    data_dict = {}
    for _, row in df_data.iterrows():
        if pd.notna(row["key"]):
            # Nettoyage des clés pour qu'elles soient utilisables en variable
            key = str(row["key"]).strip()
            val = row["value"] if pd.notna(row["value"]) else ""
            data_dict[key] = val

    # 2. Lire les lignes de frais (Colonnes A à D)
    df_items = pd.read_excel(DATA_FILE, sheet_name="Tableau de bord", usecols="A:D")

    # On ne garde que les lignes où "Référence" n'est pas vide
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

            receipt_files_path = []

            for file in os.listdir(RECEIPT_DIR):
                path = os.path.join(RECEIPT_DIR, file)
                if os.path.isfile(path):
                    receipt_files_path.append(path)

    return data_dict, items, final_price, receipt_files_path


def generate_latex(data_dict, items, final_price, receipt_files):
    """Injecte les données dans le template LaTeX."""

    # Configuration de Jinja pour LaTeX (syntaxe personnalisée pour éviter les conflits avec {})
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(ASSETS_DIR),
        block_start_string=r"\BLOCK{",
        block_end_string="}",
        variable_start_string=r"\VAR{",
        variable_end_string="}",
        comment_start_string=r"\#{",
        comment_end_string="}",
        line_statement_prefix="%%",
        line_comment_prefix="%#",
        trim_blocks=True,
        autoescape=False,
    )

    template = env.get_template("export-report-template.tex")

    # Mapping des clés Excel (français classique) dans un dictionnaire utilisable par
    # jinja (variable snake_case)
    context = {
        # Mapping des métadonnées
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
        # Mapping des items
        "items": items,
        "final_price": f"{final_price:.2f}",
        # Mapping des justificatifs
        "receipt_files": receipt_files,
        # Mapping de la date du jour
        "date": datetime.now().strftime("%d/%m/%Y"),
    }

    # Adresse de la signature si le nom est renseigné
    if data_dict.get("Nom du fichier signature (vide si pas)") != "":
        context["signature_path"] = os.path.join(
            A_MODIFIER_DIR, data_dict.get("Nom du fichier signature (vide si pas)")
        )
    else:
        context["signature_path"] = ""

    # Adresse du logo si le nom est renseigné
    if data_dict.get("Nom du fichier logo (vide si pas)") != "":
        context["logo_path"] = os.path.join(
            A_MODIFIER_DIR, data_dict.get("Nom du fichier logo (vide si pas)")
        )
    else:
        context["logo_path"] = ""

    return template.render(context)


def compile_pdf(tex_content, ER_number, beneficiary_name):
    """Compile le code LaTeX en PDF via pdflatex."""

    tex_file_path = os.path.join(OUTPUT_DIR, "temp.tex")
    output_filename = f"{ER_number:03d} - Note de frais ({beneficiary_name}).pdf"
    # padding de 3 caractère, remplissage avec "0", sur des nombres décimaux (d)

    # Écriture du fichier .tex temporaire
    with open(tex_file_path, "w", encoding="utf-8") as f:
        f.write(tex_content)

    print(f"Compilation de {output_filename}...")

    try:
        subprocess.run(
            ["tectonic", "-o", OUTPUT_DIR, tex_file_path],
            check=True,
        )

        # Renommer le fichier de sortie
        final_pdf = os.path.join(OUTPUT_DIR, output_filename)
        generated_pdf = os.path.join(OUTPUT_DIR, "temp.pdf")

        if os.path.exists(generated_pdf):
            if os.path.exists(final_pdf):
                os.remove(final_pdf)
            os.rename(generated_pdf, final_pdf)
            print(f"Succès ! Fichier généré : {final_pdf}")

        # Nettoyage des fichiers temporaires (.aux, .log, .tex)
        for ext in [".aux", ".log", ".tex"]:
            f = os.path.join(OUTPUT_DIR, f"temp{ext}")
            if os.path.exists(f):
                os.remove(f)

    except subprocess.CalledProcessError as e:
        print(f"Erreur: {e}")
        # En cas d'erreur, on peut regarder temp.log dans output/


if __name__ == "__main__":
    try:
        data, items, final_price, receipt_files_path = load_data()
        latex_code = generate_latex(data, items, final_price, receipt_files_path)

        beneficiary_name = data.get("Bénéficiaire (à remplir sur la feuille suivante)")
        ER_number = data.get("Numéro de la note de frais")
        compile_pdf(latex_code, ER_number, beneficiary_name)

    except Exception as e:
        print(f"Une erreur est survenue : {e}")
