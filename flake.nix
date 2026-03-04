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
            pre-commit 
          ]);
        in {
          default = pkgs.mkShell {
            buildInputs = [ devPython pkgs.tectonic ];
            shellHook = "echo 'Environnement de DEV Nix chargé";
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
              BASE_DIR="$PWD"
              SYSTEM_DIR="$BASE_DIR/.system"
              SCRIPT_PY="$SYSTEM_DIR/src/expense-report-creator/main.py"
              
              if [ ! -f "$SCRIPT_PY" ]; then
                echo "Erreur: main.py introuvable. Run doit être lancé à la racine du projet."
                exit 1
              fi

              # Lancement avec le Python léger, $@ transmet les arguments de nix run vers python
              python3 "$SCRIPT_PY" "$@"
            '';
          };
        }
      );
    };
}