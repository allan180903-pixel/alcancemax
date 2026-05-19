import urllib.parse
import subprocess
import tempfile
import time
import json
import os
import pyautogui

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def clean_phone(phone):
    digits = ''.join(filter(str.isdigit, str(phone)))
    if not digits:
        return None
    if len(digits) <= 11:
        digits = '55' + digits
    return digits


def personalize(text, nome, empresa=""):
    import re
    nome_strip = nome.strip() if nome else ''
    empresa_strip = empresa.strip() if empresa else ''

    if nome_strip:
        text = re.sub(r'\{[Nn]ome\}|\{NOME\}', nome_strip, text)
    else:
        text = re.sub(r'\{[Nn]ome\}|\{NOME\}', '', text)
        text = re.sub(r'\s+,', ',', text)
        text = re.sub(r' {2,}', ' ', text)

    if empresa_strip:
        text = re.sub(r'\{[Ee]mpresa\}|\{EMPRESA\}', empresa_strip, text)
    else:
        text = re.sub(r'\{[Ee]mpresa\}|\{EMPRESA\}', '', text)
        text = re.sub(r'\s+,', ',', text)
        text = re.sub(r'\s+\.', '.', text)
        text = re.sub(r' {2,}', ' ', text)

    return text.strip()


def get_whatsapp_link(phone, message, nome="", empresa=""):
    phone_clean = clean_phone(phone)
    if not phone_clean:
        return None
    message_final = personalize(message, nome, empresa)
    encoded = urllib.parse.quote(message_final)
    return f"https://wa.me/{phone_clean}?text={encoded}"


def get_whatsapp_web_link(phone, message, nome="", empresa=""):
    phone_clean = clean_phone(phone)
    if not phone_clean:
        return None
    message_final = personalize(message, nome, empresa)
    encoded = urllib.parse.quote(message_final)
    return f"https://web.whatsapp.com/send?phone={phone_clean}&text={encoded}"


def _close_whatsapp_tab():
    """Fecha o tab do WhatsApp Web. Tenta AppleScript direto; se aparecer
    diálogo 'Sair do site?', clica no botão de confirmação."""
    # 1) Ativa o tab correto
    _run_applescript('''tell application "Google Chrome"
    repeat with w in windows
        repeat with t in tabs of w
            if URL of t contains "web.whatsapp.com" then
                set active tab index of w to (get index of t)
                set index of w to 1
                exit repeat
            end if
        end repeat
    end repeat
end tell
tell application "Google Chrome" to activate''')
    time.sleep(0.4)
    # 2) Cmd+W via pyautogui (hardware keystroke, não passa pelo AppleEvent)
    pyautogui.hotkey('command', 'w')
    time.sleep(0.8)
    # 3) Se aparecer diálogo "Sair do site?", clica no botão "Sair"
    r = _run_applescript('''tell application "System Events"
    tell process "Google Chrome"
        if exists (sheet 1 of front window) then
            try
                click button "Sair" of sheet 1 of front window
            on error
                try
                    click button "Leave" of sheet 1 of front window
                on error
                    key code 36  -- Enter como fallback
                end try
            end try
        end if
    end tell
end tell''')


def _run_applescript(script):
    """Executa um AppleScript e retorna o resultado."""
    fd, tmp = tempfile.mkstemp(suffix='.applescript')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(script)
        return subprocess.run(['osascript', tmp], capture_output=True, text=True)
    finally:
        try:
            os.unlink(tmp)
        except Exception:
            pass


def send_whatsapp_auto(phone, message, nome="", empresa="", wait_time=18, file_path=None, close_tab=True):
    """
    Envia mensagem (+ arquivo opcional) via WhatsApp Web.
    Reutiliza o tab existente para evitar 'WhatsApp aberto em outra janela'.
    Usa pyautogui para cliques de hardware (evita timeout -1712 do System Events).
    """
    phone_clean = clean_phone(phone)
    if not phone_clean:
        return False, "Número de telefone inválido."

    msg = personalize(message, nome, empresa)
    encoded = urllib.parse.quote(msg)
    url = f"https://web.whatsapp.com/send?phone={phone_clean}&text={encoded}"
    safe_url = url.replace('"', '\\"')

    ATTACH_X_OFFSET = 535
    ATTACH_Y_BOTTOM = 39
    DOC_Y_ABOVE     = 297   # "Documento"  — posição calibrada
    FOTOS_Y_ABOVE   = 263   # "Fotos e vídeos" — 34px acima do Documento no menu

    # Detecta o tipo de arquivo para escolher o item correto do menu
    _MEDIA_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff',
                   '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.m4v', '.3gp'}
    _file_ext = os.path.splitext(file_path)[1].lower() if file_path else ''
    _is_media  = _file_ext in _MEDIA_EXTS

    # close_block não é mais embutido nos scripts AppleScript;
    # o fechamento é feito em Python após o envio.

    # ── Parte 1: abre/navega o tab, espera carregar, envia mensagem ───────────
    script1 = f'''tell application "Google Chrome"
    set wazTab to missing value
    set wazWin to missing value
    set wazIdx to 0
    repeat with w in windows
        set tabIdx to 0
        repeat with t in tabs of w
            set tabIdx to tabIdx + 1
            if URL of t contains "web.whatsapp.com" then
                set wazTab to t
                set wazWin to w
                set wazIdx to tabIdx
                exit repeat
            end if
        end repeat
        if wazTab is not missing value then exit repeat
    end repeat
    if wazTab is not missing value then
        set URL of wazTab to "{safe_url}"
        set active tab index of wazWin to wazIdx
        set index of wazWin to 1
    else
        open location "{safe_url}"
    end if
end tell
tell application "Google Chrome" to activate
delay {wait_time}

tell application "Google Chrome"
    repeat with w in windows
        set tabIdx to 0
        repeat with t in tabs of w
            set tabIdx to tabIdx + 1
            if URL of t contains "web.whatsapp.com" then
                set active tab index of w to tabIdx
                set index of w to 1
                exit repeat
            end if
        end repeat
    end repeat
end tell
tell application "Google Chrome" to activate
delay 1

tell application "System Events"
    tell process "Google Chrome"
        keystroke return
    end tell
end tell'''

    r1 = _run_applescript(script1)
    if r1.returncode != 0:
        err = r1.stderr.strip() or r1.stdout.strip() or "erro desconhecido"
        return False, f"Erro AppleScript: {err}"

    # Sem arquivo: só fecha o tab e retorna
    if not file_path:
        if close_tab:
            _close_whatsapp_tab()
        return True, "Mensagem enviada com sucesso."

    # ── Parte 2: cliques de hardware via pyautogui (sem System Events) ────────
    abs_path = os.path.abspath(file_path)
    safe_path = abs_path.replace('\\', '\\\\').replace('"', '\\"')

    # Pega posição da janela do Chrome para calcular coordenadas
    r_pos = _run_applescript('''tell application "System Events"
    tell process "Google Chrome"
        set p to position of front window
        set s to size of front window
    end tell
end tell
return ((item 1 of p) as string) & "," & ((item 2 of p) as string) & "," & ((item 1 of s) as string) & "," & ((item 2 of s) as string)''')

    try:
        wx, wy, ww, wh = [int(x) for x in r_pos.stdout.strip().split(',')]
    except Exception:
        wx, wy, ww, wh = 0, 25, 1440, 788  # fallback calibrado

    attach_x  = wx + ATTACH_X_OFFSET
    attach_y  = wy + wh - ATTACH_Y_BOTTOM
    menu_x    = attach_x
    menu_y    = attach_y - (FOTOS_Y_ABOVE if _is_media else DOC_Y_ABOVE)

    # Garante que o Chrome com o tab do WhatsApp está em frente
    # (quando roda pelo Streamlit o foco pode ter voltado para outro tab)
    _run_applescript('''tell application "Google Chrome"
    repeat with w in windows
        repeat with t in tabs of w
            if URL of t contains "web.whatsapp.com" then
                set active tab index of w to (get index of t)
                set index of w to 1
                exit repeat
            end if
        end repeat
    end repeat
end tell
tell application "Google Chrome" to activate''')
    time.sleep(1)   # aguarda foco estabilizar

    menu_label = "Fotos e vídeos" if _is_media else "Documento"
    time.sleep(3)
    pyautogui.click(attach_x, attach_y)   # clica no "+"
    time.sleep(2)
    pyautogui.click(menu_x, menu_y)       # clica em "Fotos e vídeos" ou "Documento"
    time.sleep(6)   # aguarda NSOpenPanel abrir antes do Cmd+Shift+G

    # ── Parte 3: navega no painel de arquivo e envia ──────────────────────────
    script3 = f'''set the clipboard to "{safe_path}"
delay 1
tell application "System Events"
    keystroke "g" using {{command down, shift down}}
    delay 2
    keystroke "a" using {{command down}}
    delay 0.3
    keystroke "v" using {{command down}}
    delay 1
    key code 36
    delay 2.5
    key code 36
    delay 6
end tell
tell application "System Events"
    tell process "Google Chrome"
        keystroke return
    end tell
end tell
delay 2'''

    r3 = _run_applescript(script3)
    if r3.returncode != 0:
        err = r3.stderr.strip() or r3.stdout.strip() or "erro desconhecido"
        return False, f"Erro AppleScript (arquivo): {err}"

    if close_tab:
        _close_whatsapp_tab()
    return True, f"Mensagem e {menu_label.lower()} enviados com sucesso."


def send_whatsapp_file_auto(phone, file_path, wait_time=18):
    """
    Envia um arquivo via app nativo do WhatsApp (macOS).
    Usa URL scheme whatsapp:// para abrir a conversa, depois abre o seletor
    de arquivo nativo (NSOpenPanel) via menu de anexo — sem interferência do Chrome.

    Requer: App WhatsApp instalado e logado.
    """
    phone_clean = clean_phone(phone)
    if not phone_clean:
        return False, "Número de telefone inválido."

    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        return False, f"Arquivo não encontrado: {abs_path}"

    safe_path = abs_path.replace('\\', '\\\\').replace('"', '\\"')

    # Número sem código do país "55" — WhatsApp busca pelo número local
    search_phone = phone_clean[2:] if phone_clean.startswith('55') and len(phone_clean) >= 12 else phone_clean
    safe_search = search_phone.replace('"', '\\"')

    # Traz o WhatsApp para frente e fecha Chrome para liberar o foco
    subprocess.run(['open', '-a', 'WhatsApp'], check=True)
    time.sleep(4)

    script = f'''-- Garante WhatsApp em frente (hardware clicks exigem foco)
tell application "WhatsApp" to activate
delay 2

set thePath to "{safe_path}"

-- Posição e tamanho da janela
tell application "System Events"
    tell process "WhatsApp"
        set winPos to position of front window
        set winSz  to size of front window
    end tell
end tell
set winX to item 1 of winPos
set winY to item 2 of winPos
set winW to item 1 of winSz
set winH to item 2 of winSz

-- Reativa o WhatsApp (garante foco antes dos hardware clicks)
tell application "WhatsApp" to activate
delay 0.5

-- Aba Conversas via hardware click
set tabX to winX + 33
set tabY to winY + 45
tell application "System Events"
    click at {{tabX, tabY}}
end tell
delay 1.5

-- Reativa para garantir foco antes do click na busca
tell application "WhatsApp" to activate
delay 0.3

-- Barra de busca via hardware click
set searchBarX to winX + 244
set searchBarY to winY + 65
tell application "System Events"
    click at {{searchBarX, searchBarY}}
end tell
delay 0.5
-- Digita o número via AX (digitação funciona com tell process)
tell application "System Events"
    tell process "WhatsApp"
        keystroke "{safe_search}"
    end tell
end tell
delay 2.5

-- Clica no primeiro resultado via hardware click
tell application "WhatsApp" to activate
delay 0.3
set resultX to winX + 240
set resultY to winY + 167
tell application "System Events"
    click at {{resultX, resultY}}
end tell
delay 1.5

-- Botão "+" (hardware click — WhatsApp em frente)
tell application "WhatsApp" to activate
delay 0.3
set attachX to winX + 444
set attachY to winY + winH - 55
tell application "System Events"
    click at {{attachX, attachY}}
end tell
delay 1.5

-- "Arquivo" (224px acima do "+")
set arquivoX to winX + 510
set arquivoY to attachY - 224
tell application "System Events"
    click at {{arquivoX, arquivoY}}
end tell
delay 3

-- Painel de arquivo nativo (NSOpenPanel) aberto — usa Cmd+Shift+G
set the clipboard to thePath
tell application "System Events"
    keystroke "g" using {{command down, shift down}}
    delay 1.5
    keystroke "a" using {{command down}}
    delay 0.3
    keystroke "v" using {{command down}}
    delay 1
    key code 36
    delay 2
    key code 36
    delay 5
end tell

-- Envia o arquivo
tell application "System Events"
    tell process "WhatsApp"
        keystroke return
    end tell
end tell
delay 2'''

    fd, tmp_script = tempfile.mkstemp(suffix='.applescript')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(script)
        result = subprocess.run(['osascript', tmp_script], capture_output=True, text=True)
    finally:
        try:
            os.unlink(tmp_script)
        except Exception:
            pass

    if result.returncode != 0:
        return False, f"Erro AppleScript: {result.stderr.strip()}"
    return True, "Arquivo enviado com sucesso."
