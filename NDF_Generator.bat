@echo off
setlocal EnableDelayedExpansion

:: --- 1. CONFIGURATION GENERALE ---
set "BASE_DIR=%~dp0"
set "BASE_DIR=%BASE_DIR:~0,-1%"

set "SYSTEM_DIR=%BASE_DIR%\.system"
set "VENV_DIR=%BASE_DIR%\.venv"
set "REQ_FILE=%SYSTEM_DIR%\requirements.txt"
set "SCRIPT_PY=%SYSTEM_DIR%\src\expense-report-creator\main.py"

:: Chemins Python
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "PIP_EXE=%VENV_DIR%\Scripts\pip.exe"
set "TECTONIC_EXE=%VENV_DIR%\Scripts\tectonic.exe"

:: --- CONFIGURATION TECTONIC (Moteur PDF) ---
:: On definit les liens AVANT de commencer pour eviter les erreurs de variables vides
set "DL_URL=https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic@0.14.1/tectonic-0.14.1-x86_64-pc-windows-msvc.zip"
set "ZIP_PATH=%VENV_DIR%\tectonic.zip"
set "DEST_DIR=%VENV_DIR%\Scripts"

:: --- 2. VERIFICATION PYTHON SYSTEME ---
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [Erreur] Python n'est pas installe ou n'est pas dans le PATH.
    echo Veuillez installer Python depuis python.org.
    echo.
    pause
    exit /b 1
)

:: --- 3. CREATION ENVIRONNEMENT VIRTUEL ---
if not exist "%VENV_DIR%" (
    echo [INFO] Creation de l'environnement virtuel...
    python -m venv "%VENV_DIR%"
    
    if exist "%REQ_FILE%" (
        echo [INFO] Installation des dependances Python...
        "%PIP_EXE%" install -r "%REQ_FILE%"
    )
)

:: --- 4. INSTALLATION TECTONIC ---
if not exist "%TECTONIC_EXE%" (
    echo [INFO] Tectonic non trouve. Telechargement...
    
    :: La commande PowerShell utilise maintenant les variables definies tout en haut
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Write-Host 'Telechargement...' -NoNewline; Invoke-WebRequest -Uri '%DL_URL%' -OutFile '%ZIP_PATH%'; Write-Host ' Fait.'; Write-Host 'Extraction...' -NoNewline; Expand-Archive -Path '%ZIP_PATH%' -DestinationPath '%DEST_DIR%' -Force; Write-Host ' Fait.'"
    
    :: Nettoyage
    if exist "%ZIP_PATH%" del "%ZIP_PATH%"

    :: Verification
    if exist "%TECTONIC_EXE%" (
        echo [INFO] Moteur LaTeX installe avec succes.
    ) else (
        echo.
        echo [ERREUR CRITIQUE] Le telechargement automatique a echoue.
        echo.
        echo --- SOLUTION MANUELLE OBLIGATOIRE ---
        echo 1. Telechargez ce fichier ZIP :
        echo %DL_URL%
        echo.
        echo 2. Ouvrez le ZIP et copiez le fichier "tectonic.exe"
        echo.
        echo 3. Collez "tectonic.exe" dans ce dossier exact :
        echo %DEST_DIR%
        echo.
        echo Une fois fait, relancez simplement ce programme.
        pause
        exit /b 1
    )
)

:: --- 5. LANCEMENT DU PROGRAMME ---
echo [INFO] Lancement du generateur...
"%PYTHON_EXE%" "%SCRIPT_PY%"

if %errorlevel% neq 0 (
    echo.
    echo [ERREUR] Le programme s'est arrete avec une erreur.
    pause
) else (
    echo.
    echo Programme termine.
    timeout /t 3 >nul
)

endlocal