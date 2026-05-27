#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  AlcanceMax — Instalador (macOS / Linux)
#  Uso: curl -fsSL URL_DESTE_SCRIPT | bash
# ═══════════════════════════════════════════════════════════════

set -e

APP_NAME="AlcanceMax"
APP_DIR="$HOME/$APP_NAME"

# ⚠️ Substitua pelo link direto do seu ZIP no GitHub Releases / Google Drive
ZIP_URL="https://github.com/allan180903-pixel/alcancemax/releases/latest/download/alcancemax.zip"

# ── Cores ──────────────────────────────────────────────────────
R='\033[0;31m'; G='\033[0;32m'; Y='\033[1;33m'
B='\033[0;34m'; C='\033[0;36m'; N='\033[0m'

banner() {
  echo ""
  echo -e "${C}╔════════════════════════════════════════╗${N}"
  echo -e "${C}║        AlcanceMax  Instalador          ║${N}"
  echo -e "${C}╚════════════════════════════════════════╝${N}"
  echo ""
}

ok()   { echo -e "      ${G}✓ $1${N}"; }
fail() { echo -e "      ${R}✗ $1${N}"; echo ""; exit 1; }
step() { echo -e "${Y}[$1/5] $2...${N}"; }

banner

# ── [1/5] Python ───────────────────────────────────────────────
step 1 "Verificando Python 3"
PYTHON=""
for cmd in python3 python; do
  if command -v "$cmd" &>/dev/null; then
    ver=$("$cmd" -c 'import sys; print(sys.version_info.major)' 2>/dev/null || echo 0)
    if [ "$ver" = "3" ]; then
      PYTHON="$cmd"
      full=$("$cmd" --version 2>&1)
      ok "$full encontrado"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  echo ""
  echo -e "  ${R}Python 3 não encontrado.${N}"
  if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "  Instale com Homebrew:  brew install python3"
    echo "  Ou baixe em:           https://www.python.org/downloads/"
  else
    echo "  Ubuntu/Debian:  sudo apt-get install python3 python3-pip python3-venv"
    echo "  Fedora/CentOS:  sudo dnf install python3 python3-pip"
    echo "  Ou baixe em:    https://www.python.org/downloads/"
  fi
  echo ""
  exit 1
fi

# ── [2/5] Download ─────────────────────────────────────────────
step 2 "Baixando AlcanceMax"
TMP_ZIP="/tmp/alcancemax_install.zip"

if command -v curl &>/dev/null; then
  curl -fsSL "$ZIP_URL" -o "$TMP_ZIP" || fail "Falha no download. Verifique sua internet."
elif command -v wget &>/dev/null; then
  wget -q "$ZIP_URL" -O "$TMP_ZIP" || fail "Falha no download. Verifique sua internet."
else
  fail "curl ou wget não encontrado. Instale um deles e tente novamente."
fi
ok "Download concluído"

# ── [3/5] Extrair ──────────────────────────────────────────────
step 3 "Instalando arquivos"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR"

if command -v unzip &>/dev/null; then
  unzip -q "$TMP_ZIP" -d "$APP_DIR"
else
  $PYTHON -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "$TMP_ZIP" "$APP_DIR"
fi
rm -f "$TMP_ZIP"

# Se o zip veio com uma subpasta única, move tudo para cima
INNER=$(ls "$APP_DIR" 2>/dev/null | head -1)
if [ -n "$INNER" ] && [ -d "$APP_DIR/$INNER" ] && [ "$(ls "$APP_DIR" | wc -l)" -eq 1 ]; then
  mv "$APP_DIR/$INNER"/* "$APP_DIR/" 2>/dev/null || true
  mv "$APP_DIR/$INNER"/.[!.]* "$APP_DIR/" 2>/dev/null || true
  rmdir "$APP_DIR/$INNER" 2>/dev/null || true
fi

mkdir -p "$APP_DIR/dados/tmp"
ok "Arquivos em $APP_DIR"

# ── [4/5] Ambiente virtual ─────────────────────────────────────
step 4 "Instalando dependências Python"
$PYTHON -m venv "$APP_DIR/venv" || fail "Erro ao criar ambiente virtual."
"$APP_DIR/venv/bin/pip" install --upgrade pip --quiet
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt" --quiet || \
  fail "Erro ao instalar dependências. Verifique requirements.txt."
ok "Dependências instaladas"

# ── [5/5] Atalho na Área de Trabalho ──────────────────────────
step 5 "Criando atalho"

# Encontra a Área de Trabalho (multi-idioma)
DESKTOP=""
for d in "$HOME/Desktop" "$HOME/Área de Trabalho" "$HOME/Bureau" "$HOME/Escritorio"; do
  [ -d "$d" ] && DESKTOP="$d" && break
done
[ -z "$DESKTOP" ] && DESKTOP="$HOME"

LAUNCHER="$DESKTOP/AlcanceMax.command"
cat > "$LAUNCHER" << 'SCRIPT'
#!/usr/bin/env bash
cd "$HOME/AlcanceMax"
source venv/bin/activate
echo ""
echo "  Iniciando AlcanceMax..."
echo "  Acesse no navegador: http://localhost:8501"
echo "  Para fechar: pressione Ctrl+C nesta janela"
echo ""
streamlit run app.py --server.headless true --server.port 8501
SCRIPT
chmod +x "$LAUNCHER"

# macOS: remove flag de quarentena para permitir execução sem popup
if [[ "$OSTYPE" == "darwin"* ]]; then
  xattr -d com.apple.quarantine "$LAUNCHER" 2>/dev/null || true
fi
ok "Atalho criado: AlcanceMax.command na Área de Trabalho"

# ── Conclusão ──────────────────────────────────────────────────
echo ""
echo -e "${G}╔════════════════════════════════════════╗${N}"
echo -e "${G}║   ✅  AlcanceMax instalado!            ║${N}"
echo -e "${G}╚════════════════════════════════════════╝${N}"
echo ""
echo "  Como abrir:"
echo "  → Dê dois cliques em 'AlcanceMax.command' na Área de Trabalho"
echo ""
echo "  O app abre no navegador em: http://localhost:8501"
echo ""
