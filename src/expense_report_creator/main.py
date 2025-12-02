import os
import subprocess
from datetime import datetime

import jinja2
import pandas as pd

# Configuration des chemins
ASSETS_DIR = os.path.join(os.getcwd(), "assets")
TEMPLATES_DIR = os.path.join(ASSETS_DIR, "templates")
OUTPUT_DIR = os.path.join(ASSETS_DIR, "output")
DATA_FILE = os.path.join(ASSETS_DIR, "data.xlsx")

# Créer le dossier output s'il n'existe pas
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_data():
    """Lit le fichier Excel et sépare les items des métadonnées."""

    # 1. Lire les métadonnées (Colonnes F et G - Index 5 et 6)
    # On suppose que les données clés/valeurs commencent ligne 2 (index 1)
    df_meta = pd.read_excel(
        DATA_FILE,
        sheet_name="Tableau de bord",
        usecols="F:G",
    )

    df_meta.columns = ["key", "value"]

    # Nettoyage des métadonnées pour en faire un dictionnaire
    meta_dict = {}
    for _, row in df_meta.iterrows():
        if pd.notna(row["key"]):
            # Nettoyage des clés pour qu'elles soient utilisables en variable
            key = str(row["key"]).strip()
            val = row["value"] if pd.notna(row["value"]) else ""
            meta_dict[key] = val

    # 2. Lire les lignes de frais (Colonnes A à D)
    df_items = pd.read_excel(DATA_FILE, sheet_name="Tableau de bord", usecols="A:D")

    # On ne garde que les lignes où "Référence" n'est pas vide
    items = []
    total_global = 0.0

    for _, row in df_items.iterrows():
        if pd.notna(row["Référence"]):
            qty = row["Quantité"] if pd.notna(row["Quantité"]) else 0
            prix_u = row["Prix unitaire"] if pd.notna(row["Prix unitaire"]) else 0
            prix_t = row["Prix total"] if pd.notna(row["Prix total"]) else 0

            items.append(
                {
                    "quantite": int(qty),
                    "reference": row["Référence"],
                    "prix_unitaire": f"{prix_u:.2f}",
                    "prix_total": f"{prix_t:.2f}",
                }
            )
            total_global += float(prix_t)

    return meta_dict, items, total_global


def generate_latex(meta_dict, items, total_global):
    """Injecte les données dans le template LaTeX."""

    # Configuration de Jinja pour LaTeX (syntaxe personnalisée pour éviter les conflits avec {})
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(TEMPLATES_DIR),
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

    template = env.get_template("main.tex")

    # Mapping des clés Excel (humaines) vers les variables Jinja (code)
    # Adapte ces clés selon le texte EXACT dans ton fichier Excel colonnes F
    context = {
        "logo_path": os.path.join(
            ASSETS_DIR, meta_dict.get("Nom du fichier logo (vide si pas)")
        ),
        "nom_asso": "Nom de ton Club",  # Peut être ajouté dans l'Excel ou hardcodé ici
        "adresse_asso_1": meta_dict.get("Adresse de l'Association (partie 1)", ""),
        "adresse_asso_2": meta_dict.get("Adresse de l'Association (partie 2)", ""),
        "email_asso": "contact@tonclub.fr",
        "numero_ndf": "2025-001",  # À automatiser selon tes besoins
        "date_jour": datetime.now().strftime("%d/%m/%Y"),
        "beneficiaire_nom": meta_dict.get(
            "Bénéficiaire (à remplir sur la feuille suivante)"
        ),
        "beneficiaire_adresse": f"{meta_dict.get('Adresse (partie 1)', '')} {meta_dict.get('Adresse (partie 2)', '')}",
        "beneficiaire_iban": meta_dict.get(
            "IBAN (remplissage auto à partir du bénéficiaire)"
        ),
        "mode_remboursement": meta_dict.get("Mode de remboursement"),
        "lieu_signature": meta_dict.get("Fait à", "Toulouse"),
        "signature_path": os.path.join(
            ASSETS_DIR, meta_dict.get("Nom du fichier signature (vide si pas)")
        ),
        "liste_pieces_jointes": meta_dict.get(
            "Noms pièces jointes (une par ligne vers le bas)", "Voir suite"
        ),
        "items": items,
        "total_global": f"{total_global:.2f}",
    }

    return template.render(context)


def compile_pdf(tex_content, output_filename="note_de_frais.pdf"):
    """Compile le code LaTeX en PDF via pdflatex."""

    tex_file_path = os.path.join(OUTPUT_DIR, "temp.tex")

    # Écriture du fichier .tex temporaire
    with open(tex_file_path, "w", encoding="utf-8") as f:
        f.write(tex_content)

    print(f"Compilation de {output_filename}...")

    # Appel système à pdflatex
    # -interaction=nonstopmode permet de ne pas bloquer en cas d'erreur mineure
    # -output-directory force la sortie dans le dossier output
    try:
        subprocess.run(
            ["tectonic", "-o", OUTPUT_DIR, tex_file_path],
            check=True,
            # stdout=subprocess.DEVNULL # Tu peux commenter ça au début pour voir s'il télécharge bien
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
        meta, items, total = load_data()
        latex_code = generate_latex(meta, items, total)
        compile_pdf(latex_code, "ma_note_de_frais.pdf")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
