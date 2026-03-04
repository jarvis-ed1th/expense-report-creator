{
  description = "Environnement natif Nix pour Expense Report Creator";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    in
    {
      # 1. ENVIRONNEMENT DE DÉVELOPPEMENT (nix develop)
      devShells = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          # On crée un Python avec tout (prod + dev)
          devPython = pkgs.python312.withPackages (ps: with ps; [
            # Dépendances principales
            jinja2
            openpyxl
            pandas
            pillow
            pypdf

            # Outils de développement
            black
            flake8
            isort
          ]);
        in {
          default = pkgs.mkShell {
            buildInputs = with pkgs; [ devPython tectonic pre-commit];
          };
        }
      );

      # 2. APPLICATION DE PRODUCTION (nix run .)
      packages = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          prodPython = pkgs.python312.withPackages (ps: with ps; [
            jinja2
            openpyxl
            pandas
            pillow
            pypdf
          ]);
        in {
          default = pkgs.writeShellApplication {
            name = "expense-report-creator";
            runtimeInputs = [ prodPython pkgs.tectonic ];
            text = ''
              # Nix va remplacer ${./.} par le chemin immuable dans le store
              SCRIPT_PY="${./.}/src/expense-report-creator/main.py"

              # On appelle python avec le script figé, et on lui passe le dossier cible ($@)
              python3 "$SCRIPT_PY" "$@"
            '';
          };
        }
      );
    };
}
