@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:: ═══════════════════════════════════════════════════════════════
::  AlcanceMax — Instalador (Windows)
::  Clique duas vezes para instalar
:: ═══════════════════════════════════════════════════════════════

:: ⚠️ Substitua pelo link direto do seu ZIP no GitHub Releases / Google Drive
set "ZIP_URL=https://github.com/allan180903-pixel/alcancemax/releases/latest/download/alcancemax.zip"

set "APP_DIR=%USERPROFILE%\AlcanceMax"
set "TMP_ZIP=%TEMP%\alcancemax_install.zip"
set "DESKTOP=%USERPROFILE%\Desktop"

echo.
echo  ╔════════════════════════════════════════╗
echo  ║        AlcanceMax  Instalador          ║
echo  ╚════════════════════════════════════════╝
echo.

:: ── [1/5] Verificar Python ─────────────────────────────────────
echo  [1/5] Verificando Python 3...
python --version >nul 2>&1
if errorlevel 1 goto :install_python
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
if "!PY_VER:~0,1!" == "3" goto :python_ok

:install_python
echo        Python nao encontrado. Tentando instalar via winget...
winget install -e --id Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
:: Atualiza o PATH na sessão atual
for /f "tokens=*" %%p in ('where python 2^>nul') do set "PYTHON_EXE=%%p"
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERRO: Python 3 nao encontrado.
    echo.
    echo  Por favor, instale manualmente:
    echo  1. Acesse https://www.python.org/downloads/
    echo  2. Baixe a versao mais recente
    echo  3. IMPORTANTE: marque "Add Python to PATH" durante a instalacao
    echo  4. Feche este instalador e abra novamente
    echo.
    pause
    exit /b 1
)

:python_ok
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
echo        OK: Python !PY_VER! encontrado

:: ── [2/5] Download ─────────────────────────────────────────────
echo  [2/5] Baixando AlcanceMax...
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri '%ZIP_URL%' -OutFile '%TMP_ZIP%' -UseBasicParsing } catch { Write-Host $_.Exception.Message; exit 1 }"
if not exist "%TMP_ZIP%" (
    echo.
    echo  ERRO: Falha no download.
    echo  Verifique sua conexao com a internet e tente novamente.
    echo.
    pause
    exit /b 1
)
echo        OK: Download concluido

:: ── [3/5] Extrair arquivos ─────────────────────────────────────
echo  [3/5] Instalando arquivos...
if exist "%APP_DIR%" (
    echo        Atualizando instalacao existente...
    :: Preserva config.json e dados/ se existirem
    if exist "%APP_DIR%\config.json" copy /y "%APP_DIR%\config.json" "%TEMP%\alcancemax_config_backup.json" >nul
)
if exist "%APP_DIR%" rmdir /s /q "%APP_DIR%"
mkdir "%APP_DIR%"

powershell -NoProfile -Command "Expand-Archive -Path '%TMP_ZIP%' -DestinationPath '%APP_DIR%' -Force"
del "%TMP_ZIP%" >nul 2>&1

:: Se o zip veio com subpasta, move conteudo para cima
for /d %%d in ("%APP_DIR%\*") do (
    set "INNER=%%d"
    if exist "%%d\app.py" (
        xcopy /s /e /y "%%d\*" "%APP_DIR%\" >nul
        rmdir /s /q "%%d"
    )
)

:: Restaura config.json se havia backup
if exist "%TEMP%\alcancemax_config_backup.json" (
    copy /y "%TEMP%\alcancemax_config_backup.json" "%APP_DIR%\config.json" >nul
    del "%TEMP%\alcancemax_config_backup.json" >nul
)

if not exist "%APP_DIR%\dados" mkdir "%APP_DIR%\dados"
if not exist "%APP_DIR%\dados\tmp" mkdir "%APP_DIR%\dados\tmp"
echo        OK: Arquivos em %APP_DIR%

:: ── [4/5] Ambiente virtual ─────────────────────────────────────
echo  [4/5] Instalando dependencias Python...
python -m venv "%APP_DIR%\venv"
if errorlevel 1 (
    echo  ERRO: Falha ao criar ambiente virtual.
    pause
    exit /b 1
)
"%APP_DIR%\venv\Scripts\pip.exe" install --upgrade pip --quiet
"%APP_DIR%\venv\Scripts\pip.exe" install -r "%APP_DIR%\requirements.txt" --quiet
if errorlevel 1 (
    echo  ERRO: Falha ao instalar dependencias.
    pause
    exit /b 1
)
echo        OK: Dependencias instaladas

:: ── [5/5] Atalho na Area de Trabalho ───────────────────────────
echo  [5/5] Criando atalho...

:: Cria o .bat de inicializacao
set "LAUNCHER_BAT=%APP_DIR%\Iniciar.bat"
(
    echo @echo off
    echo chcp 65001 ^>nul
    echo cd /d "%APP_DIR%"
    echo call venv\Scripts\activate.bat
    echo echo.
    echo echo   Iniciando AlcanceMax...
    echo echo   Acesse no navegador: http://localhost:8501
    echo echo   Para fechar: pressione Ctrl+C nesta janela
    echo echo.
    echo streamlit run app.py --server.headless true --server.port 8501
    echo pause
) > "%LAUNCHER_BAT%"

:: Cria atalho .lnk na Area de Trabalho via PowerShell
powershell -NoProfile -Command ^
  "$s = (New-Object -ComObject WScript.Shell).CreateShortcut('%DESKTOP%\AlcanceMax.lnk');" ^
  "$s.TargetPath = '%LAUNCHER_BAT%';" ^
  "$s.WorkingDirectory = '%APP_DIR%';" ^
  "$s.WindowStyle = 1;" ^
  "$s.Description = 'AlcanceMax - Ferramenta de Prospeccao';" ^
  "$s.Save()"

echo        OK: Atalho criado na Area de Trabalho

:: ── Conclusao ──────────────────────────────────────────────────
echo.
echo  ╔════════════════════════════════════════╗
echo  ║   AlcanceMax instalado com sucesso!    ║
echo  ╚════════════════════════════════════════╝
echo.
echo  Como abrir:
echo  - Clique duas vezes em "AlcanceMax" na Area de Trabalho
echo.
echo  O app abre automaticamente no navegador em:
echo  http://localhost:8501
echo.
pause
