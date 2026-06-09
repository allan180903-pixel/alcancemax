@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

set "ZIP_URL=https://github.com/allan180903-pixel/alcancemax/releases/latest/download/alcancemax.zip"
set "APP_DIR=%USERPROFILE%\AlcanceMax"
set "TMP_ZIP=%TEMP%\alcancemax_install.zip"
set "DESKTOP=%USERPROFILE%\Desktop"

echo.
echo  AlcanceMax - Instalador
echo  ========================
echo.

echo [1/5] Verificando Python 3...
python --version >nul 2>&1
if errorlevel 1 goto :instalar_python
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
if "!PY_VER:~0,1!" == "3" goto :python_ok

:instalar_python
echo Python nao encontrado. Tentando instalar via winget...
winget install -e --id Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERRO: Python 3 nao encontrado.
    echo Instale em: https://www.python.org/downloads/
    echo IMPORTANTE: marque "Add Python to PATH" na instalacao
    echo Depois feche e abra este instalador novamente.
    echo.
    pause
    exit /b 1
)

:python_ok
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
echo OK: Python !PY_VER! encontrado

echo [2/5] Baixando AlcanceMax...
powershell -NoProfile -Command "Invoke-WebRequest -Uri '%ZIP_URL%' -OutFile '%TMP_ZIP%' -UseBasicParsing"
if not exist "%TMP_ZIP%" (
    echo.
    echo ERRO: Falha no download. Verifique sua conexao.
    echo.
    pause
    exit /b 1
)
echo OK: Download concluido

echo [3/5] Instalando arquivos...
if exist "%APP_DIR%" (
    if exist "%APP_DIR%\config.json" copy /y "%APP_DIR%\config.json" "%TEMP%\alcancemax_config_backup.json" >nul
    rmdir /s /q "%APP_DIR%"
)
mkdir "%APP_DIR%"
powershell -NoProfile -Command "Expand-Archive -Path '%TMP_ZIP%' -DestinationPath '%APP_DIR%' -Force"
del "%TMP_ZIP%" >nul 2>&1
for /d %%d in ("%APP_DIR%\*") do (
    if exist "%%d\app.py" (
        xcopy /s /e /y "%%d\*" "%APP_DIR%\" >nul
        rmdir /s /q "%%d"
    )
)
if exist "%TEMP%\alcancemax_config_backup.json" (
    copy /y "%TEMP%\alcancemax_config_backup.json" "%APP_DIR%\config.json" >nul
    del "%TEMP%\alcancemax_config_backup.json" >nul
)
if not exist "%APP_DIR%\dados" mkdir "%APP_DIR%\dados"
if not exist "%APP_DIR%\dados\tmp" mkdir "%APP_DIR%\dados\tmp"
echo OK: Arquivos em %APP_DIR%

echo [4/5] Instalando dependencias Python...
python -m venv "%APP_DIR%\venv"
if errorlevel 1 (
    echo ERRO: Falha ao criar ambiente virtual.
    pause
    exit /b 1
)
"%APP_DIR%\venv\Scripts\pip.exe" install --upgrade pip --quiet
"%APP_DIR%\venv\Scripts\pip.exe" install -r "%APP_DIR%\requirements.txt" --quiet
if errorlevel 1 (
    echo ERRO: Falha ao instalar dependencias.
    pause
    exit /b 1
)
echo OK: Dependencias instaladas

echo [5/5] Criando atalho...
set "LAUNCHER_BAT=%APP_DIR%\Iniciar.bat"
(
    echo @echo off
    echo chcp 65001 ^>nul
    echo cd /d "%APP_DIR%"
    echo call venv\Scripts\activate.bat
    echo echo Iniciando AlcanceMax...
    echo echo Acesse: http://localhost:8501
    echo streamlit run app.py --server.headless true --server.port 8501
    echo pause
) > "%LAUNCHER_BAT%"

powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%DESKTOP%\AlcanceMax.lnk');$s.TargetPath='%LAUNCHER_BAT%';$s.WorkingDirectory='%APP_DIR%';$s.WindowStyle=1;$s.Save()"
echo OK: Atalho criado

echo.
echo ========================
echo AlcanceMax instalado!
echo ========================
echo.
echo Clique duas vezes em "AlcanceMax" na Area de Trabalho para abrir.
echo.
pause
