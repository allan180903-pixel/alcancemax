# AlcanceMax - Instalador PowerShell
$ErrorActionPreference = "Stop"
$APP_DIR = "$env:USERPROFILE\AlcanceMax"
$ZIP_URL = "https://raw.githubusercontent.com/allan180903-pixel/alcancemax/main/alcancemax.zip"
$TMP_ZIP = "$env:TEMP\alcancemax_install.zip"
$DESKTOP = [Environment]::GetFolderPath("Desktop")

Write-Host ""
Write-Host "  AlcanceMax - Instalador" -ForegroundColor Cyan
Write-Host "  ========================" -ForegroundColor Cyan
Write-Host ""

# [1/6] Python
Write-Host "[1/6] Verificando Python 3..." -ForegroundColor Yellow
$python = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python 3") { $python = $cmd; break }
    } catch {}
}

if (-not $python) {
    Write-Host "Python nao encontrado. Instalando via winget..." -ForegroundColor Yellow
    try {
        winget install -e --id Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")
        $python = "python"
    } catch {
        Write-Host ""
        Write-Host "ERRO: Nao foi possivel instalar Python automaticamente." -ForegroundColor Red
        Write-Host "Instale manualmente em: https://www.python.org/downloads/" -ForegroundColor Red
        Write-Host "IMPORTANTE: marque 'Add Python to PATH' durante a instalacao" -ForegroundColor Red
        Write-Host ""
        Read-Host "Pressione Enter para sair"
        exit 1
    }
}
Write-Host "OK: $( & $python --version 2>&1 )" -ForegroundColor Green

# [2/6] Download
Write-Host "[2/6] Baixando AlcanceMax..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $ZIP_URL -OutFile $TMP_ZIP -UseBasicParsing
} catch {
    Write-Host ""
    Write-Host "ERRO: Falha no download." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Read-Host "Pressione Enter para sair"
    exit 1
}
Write-Host "OK: Download concluido" -ForegroundColor Green

# [3/6] Extrair
Write-Host "[3/6] Instalando arquivos..." -ForegroundColor Yellow
if (Test-Path $APP_DIR) {
    if (Test-Path "$APP_DIR\config.json") {
        Copy-Item "$APP_DIR\config.json" "$env:TEMP\alcancemax_config_backup.json" -Force
    }
    Remove-Item $APP_DIR -Recurse -Force
}
New-Item -ItemType Directory -Path $APP_DIR -Force | Out-Null
Expand-Archive -Path $TMP_ZIP -DestinationPath $APP_DIR -Force
Remove-Item $TMP_ZIP -Force -ErrorAction SilentlyContinue

# Move subpasta se existir
Get-ChildItem $APP_DIR -Directory | ForEach-Object {
    if (Test-Path "$($_.FullName)\app.py") {
        Copy-Item "$($_.FullName)\*" $APP_DIR -Recurse -Force
        Remove-Item $_.FullName -Recurse -Force
    }
}

if (-not (Test-Path "$APP_DIR\dados")) { New-Item -ItemType Directory "$APP_DIR\dados" | Out-Null }
if (-not (Test-Path "$APP_DIR\dados\tmp")) { New-Item -ItemType Directory "$APP_DIR\dados\tmp" | Out-Null }

if (Test-Path "$env:TEMP\alcancemax_config_backup.json") {
    Copy-Item "$env:TEMP\alcancemax_config_backup.json" "$APP_DIR\config.json" -Force
    Remove-Item "$env:TEMP\alcancemax_config_backup.json" -Force
}

# Baixa arquivos principais direto do GitHub (garante versao mais recente)
$BASE_URL = "https://raw.githubusercontent.com/allan180903-pixel/alcancemax/main"
foreach ($arquivo in @("whatsapp_helper.py", "app.py", "email_sender.py", "ai_helper.py", "requirements.txt")) {
    try {
        Invoke-WebRequest -Uri "$BASE_URL/$arquivo" -OutFile "$APP_DIR\$arquivo" -UseBasicParsing
    } catch {}
}

# Limpa cache Python
Remove-Item "$APP_DIR\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "OK: Arquivos em $APP_DIR" -ForegroundColor Green

# [4/6] Dependencias
Write-Host "[4/6] Instalando dependencias Python (pode demorar 2-3 min)..." -ForegroundColor Yellow
& $python -m venv "$APP_DIR\venv"
& "$APP_DIR\venv\Scripts\pip.exe" install --upgrade pip --quiet
& "$APP_DIR\venv\Scripts\pip.exe" install -r "$APP_DIR\requirements.txt" --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Falha ao instalar dependencias." -ForegroundColor Red
    Read-Host "Pressione Enter para sair"
    exit 1
}
Write-Host "OK: Dependencias instaladas" -ForegroundColor Green

# [5/6] Atalho
Write-Host "[5/6] Criando atalho na Area de Trabalho..." -ForegroundColor Yellow
$launcher = "$APP_DIR\Iniciar.bat"
@"
@echo off
chcp 65001 >nul 2>&1
cd /d "$APP_DIR"
echo Iniciando AlcanceMax...
echo Acesse no navegador: http://localhost:8501
echo Para fechar: pressione Ctrl+C nesta janela
venv\Scripts\python.exe -m streamlit run app.py --server.headless true --server.port 8501
pause
"@ | Set-Content $launcher -Encoding UTF8

try {
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut("$DESKTOP\AlcanceMax.lnk")
    $shortcut.TargetPath = $launcher
    $shortcut.WorkingDirectory = $APP_DIR
    $shortcut.WindowStyle = 1
    $shortcut.Save()
    Write-Host "OK: Atalho criado em $DESKTOP" -ForegroundColor Green
} catch {
    Write-Host "Aviso: nao foi possivel criar atalho automaticamente." -ForegroundColor Yellow
    Write-Host "Para abrir o app, execute: $launcher" -ForegroundColor Yellow
}

# [6/6] Pronto
Write-Host ""
Write-Host "  ========================" -ForegroundColor Cyan
Write-Host "  AlcanceMax instalado!"    -ForegroundColor Cyan
Write-Host "  ========================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Clique duas vezes em 'AlcanceMax' na Area de Trabalho para abrir." -ForegroundColor White
Write-Host ""

$iniciar = Read-Host "Deseja abrir o AlcanceMax agora? (S/N)"
if ($iniciar -match "^[Ss]") {
    Start-Process $launcher
}
