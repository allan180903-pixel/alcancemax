# AlcanceMax - Atualizador rápido (Windows)
# Baixa os arquivos novos, instala dependências e limpa o cache.
$ErrorActionPreference = "Continue"
$APP_DIR = "$env:USERPROFILE\AlcanceMax"
$BASE = "https://raw.githubusercontent.com/allan180903-pixel/alcancemax/main"

Write-Host ""
Write-Host "  Atualizando AlcanceMax..." -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $APP_DIR)) {
    Write-Host "ERRO: AlcanceMax nao encontrado em $APP_DIR" -ForegroundColor Red
    Write-Host "Rode o instalador completo primeiro." -ForegroundColor Red
    Read-Host "Pressione Enter para sair"
    exit 1
}

# 1) Baixa os arquivos atualizados
$arquivos = @("app.py", "whatsapp_helper.py", "email_sender.py", "ai_helper.py", "requirements.txt")
foreach ($f in $arquivos) {
    try {
        Invoke-WebRequest -Uri "$BASE/$f" -OutFile "$APP_DIR\$f" -UseBasicParsing
        Write-Host "OK: $f" -ForegroundColor Green
    } catch {
        Write-Host "Falha ao baixar $f" -ForegroundColor Yellow
    }
}

# 2) Instala a dependencia nova (IA - anthropic)
Write-Host "Instalando dependencias (pode demorar 1 min)..." -ForegroundColor Yellow
if (Test-Path "$APP_DIR\venv\Scripts\pip.exe") {
    & "$APP_DIR\venv\Scripts\pip.exe" install anthropic --quiet 2>$null
    & "$APP_DIR\venv\Scripts\pip.exe" install -r "$APP_DIR\requirements.txt" --quiet 2>$null
}

# 3) Limpa o cache do Python (garante que o codigo novo seja usado)
Remove-Item "$APP_DIR\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "  ==================================" -ForegroundColor Cyan
Write-Host "  AlcanceMax atualizado com sucesso!" -ForegroundColor Cyan
Write-Host "  ==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "FECHE o AlcanceMax (a janela preta) e abra de novo pelo atalho." -ForegroundColor White
Write-Host ""
Read-Host "Pressione Enter para sair"
