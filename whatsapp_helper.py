import urllib.parse
import subprocess
import tempfile
import shutil
import time
import json
import sys
import os
import pyautogui

# Automação WhatsApp só funciona no macOS (requer osascript/AppleScript)
IS_MACOS = sys.platform == "darwin"

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


def _send_whatsapp_windows(phone, message, nome="", empresa="", wait_time=18, files=None):
    """Envio automático via WhatsApp Web no Windows (mensagem + imagens/vídeos).
    Documentos (PDF, etc.) não são suportados no automático do Windows."""
    import webbrowser

    files = [f for f in (files or []) if f]

    phone_clean = clean_phone(phone)
    if not phone_clean:
        return False, "Número de telefone inválido."

    msg = personalize(message, nome, empresa)
    url = f"https://web.whatsapp.com/send?phone={phone_clean}&text={urllib.parse.quote(msg)}"

    # Passo 1: abre o WhatsApp Web no navegador padrão (nova janela)
    try:
        webbrowser.open_new(url)
    except Exception as e:
        return False, f"Erro ao abrir o navegador: {e}"

    # Passo 2: aguarda a página carregar
    time.sleep(wait_time)

    # Passo 3: pressiona Enter via pyautogui
    # O navegador abre em foco, então pyautogui.press funciona direto
    try:
        pyautogui.press('return')
    except Exception as e:
        return False, f"Erro ao pressionar Enter: {e}"

    time.sleep(2)

    if not files:
        return True, "Mensagem enviada com sucesso."

    # Anexos: envia cada imagem/vídeo em sequência
    _MEDIA_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff',
                   '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.m4v', '.3gp'}
    enviadas = 0
    docs = 0
    for fp in files:
        if os.path.splitext(fp)[1].lower() not in _MEDIA_EXTS:
            docs += 1
            continue
        try:
            abs_path = os.path.abspath(fp)
            # Copia imagem para clipboard E traz a janela do browser para frente
            ps_copy = f'''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile("{abs_path.replace(chr(92), chr(92)+chr(92))}")
[System.Windows.Forms.Clipboard]::SetImage($img)
$img.Dispose()
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32Focus {{
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}}
"@
foreach ($name in @("chrome","msedge","firefox")) {{
    $procs = Get-Process $name -ErrorAction SilentlyContinue
    foreach ($p in $procs) {{
        if ($p.MainWindowHandle -ne [IntPtr]::Zero) {{
            [Win32Focus]::ShowWindow($p.MainWindowHandle, 9)
            [Win32Focus]::SetForegroundWindow($p.MainWindowHandle)
            break
        }}
    }}
}}
'''
            subprocess.run(
                ['powershell', '-WindowStyle', 'Hidden', '-Command', ps_copy],
                capture_output=True, timeout=10
            )
            time.sleep(1)
            # Clica no input do WhatsApp Web para garantir foco na aba correta
            screen_w, screen_h = pyautogui.size()
            pyautogui.click(int(screen_w * 0.65), screen_h - 80)
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(4)
            pyautogui.press('return')
            time.sleep(2)
            enviadas += 1
        except Exception:
            pass

    partes = ["Mensagem enviada"]
    if enviadas:
        partes.append(f"{enviadas} imagem(ns)")
    if docs:
        partes.append(f"{docs} documento(s) para anexar manualmente")
    return True, " + ".join(partes) + "."


def _attach_file_mac(file_path, wx, wy, ww, wh):
    """Anexa UM arquivo ao chat do WhatsApp Web já aberto e o envia.
    NÃO fecha o tab. Retorna (ok, mensagem). Usado em loop para vários anexos."""
    ATTACH_X_OFFSET = 535
    ATTACH_Y_BOTTOM = 39
    DOC_Y_ABOVE     = 297
    FOTOS_Y_ABOVE   = 263
    # IMAGENS vão pelo clipboard (colar). VÍDEOS vão por "Fotos e vídeos"
    # (enviados como vídeo que toca). DOCUMENTOS vão por "Documento".
    _IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'}
    _VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.m4v', '.3gp'}

    _file_ext = os.path.splitext(file_path)[1].lower()
    _is_image = _file_ext in _IMAGE_EXTS
    _is_video = _file_ext in _VIDEO_EXTS
    _menu_label = "Fotos e vídeos" if _is_video else "Documento"

    abs_path = os.path.abspath(file_path)
    tmp_dir  = tempfile.mkdtemp()
    safe_tmp = os.path.join(tmp_dir, f"attach{_file_ext}")
    shutil.copy2(abs_path, safe_tmp)
    safe_path = safe_tmp.replace('\\', '\\\\').replace('"', '\\"')

    attach_x = wx + ATTACH_X_OFFSET
    attach_y = wy + wh - ATTACH_Y_BOTTOM
    menu_x   = attach_x
    menu_y   = attach_y - (FOTOS_Y_ABOVE if _is_video else DOC_Y_ABOVE)

    # Garante que o tab do WhatsApp está em frente
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
    time.sleep(1)

    # ══ IMAGENS: clipboard PNG + Cmd+V ═══════════════════════════════════
    if _is_image:
        jxa_script = f'''
ObjC.import('AppKit');
var path = "{safe_tmp}";
var img = $.NSImage.alloc.initWithContentsOfFile(path);
if (img && img.isValid) {{
    var tiff = img.TIFFRepresentation;
    var rep  = $.NSBitmapImageRep.imageRepWithData(tiff);
    var png  = rep.representationUsingTypeProperties($.NSBitmapImageFileTypePNG, {{}});
    var pb   = $.NSPasteboard.generalPasteboard;
    pb.clearContents;
    pb.setDataForType(png, 'public.png');
    "ok";
}} else {{
    "error: imagem invalida";
}}
'''
        r_clip = subprocess.run(
            ['osascript', '-l', 'JavaScript', '-e', jxa_script],
            capture_output=True, text=True
        )
        shutil.rmtree(tmp_dir, ignore_errors=True)
        if r_clip.returncode != 0 or 'error' in r_clip.stdout.lower():
            err = r_clip.stderr.strip() or r_clip.stdout.strip() or "erro desconhecido"
            return False, f"Erro ao copiar imagem: {err}"

        chat_x = wx + (ww * 2 // 3)
        chat_y = wy + wh - 60
        paste_script = f'''tell application "Google Chrome"
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
tell application "Google Chrome" to activate
delay 0.8
tell application "System Events"
    tell process "Google Chrome"
        click at {{{chat_x}, {chat_y}}}
        delay 0.8
        keystroke "v" using command down
        delay 5
        key code 36
        delay 2
    end tell
end tell'''
        r_paste = _run_applescript(paste_script)
        if r_paste.returncode != 0:
            err = r_paste.stderr.strip() or r_paste.stdout.strip() or "erro desconhecido"
            return False, f"Erro ao colar imagem: {err}"
        return True, "ok"

    # ══ DOCUMENTOS: clica no "+" e encontra "Documento" no DOM ══════════════════
    time.sleep(2)
    js_attach = (
        'var btn=null;'
        'document.querySelectorAll("button").forEach(function(b){'
        '  if(!btn && b.querySelector("[data-icon=\\"attach-menu-plus\\"]")) btn=b;'
        '});'
        'if(btn){btn.click();"ok";}else{"not found";}'
    )
    _run_applescript(f'''tell application "Google Chrome"
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
tell application "Google Chrome"
    execute active tab of front window javascript "{js_attach}"
end tell''')
    time.sleep(2)

    js_pos = (
        'var res="not found";'
        'document.querySelectorAll("li span,li div,[role=\\"button\\"] span").forEach(function(el){'
        '  if(res==="not found" && el.textContent.trim()==="' + _menu_label + '"){'
        '    var r=el.getBoundingClientRect();'
        '    res=Math.round(r.left+r.width/2)+","+Math.round(r.top+r.height/2);'
        '  }'
        '});res;'
    )
    r_pos2 = _run_applescript(f'''tell application "Google Chrome"
    set jsResult to execute active tab of front window javascript "{js_pos}"
end tell
return jsResult''')

    doc_clicked = False
    if r_pos2.returncode == 0:
        pos_str = r_pos2.stdout.strip().strip('"')
        if ',' in pos_str and pos_str != 'not found':
            try:
                rel_x, rel_y = [int(v) for v in pos_str.split(',')]
                abs_doc_x = wx + rel_x
                abs_doc_y = wy + rel_y + 88
                _run_applescript(f'''tell application "System Events"
    click at {{{abs_doc_x}, {abs_doc_y}}}
end tell''')
                doc_clicked = True
                time.sleep(2)
            except Exception:
                pass

    if not doc_clicked:
        time.sleep(1)
        pyautogui.click(attach_x, attach_y)
        time.sleep(2.5)
        pyautogui.click(menu_x, menu_y)
        time.sleep(1.5)

    # Tempo de upload proporcional ao tamanho do arquivo (vídeo grande precisa de mais)
    try:
        _mb = os.path.getsize(abs_path) / (1024 * 1024)
    except Exception:
        _mb = 1
    _upload_wait = int(min(max(6, _mb * 1.3), 240))  # 6s mínimo, ~1.3s/MB, teto 240s

    script3 = f'''set the clipboard to "{safe_path}"
delay 0.5
tell application "System Events"
    tell process "Google Chrome"
        set waited to 0
        repeat
            try
                if exists sheet 1 of front window then exit repeat
            end try
            if (count of windows) > 1 then exit repeat
            delay 0.5
            set waited to waited + 0.5
            if waited >= 15 then exit repeat
        end repeat
        delay 0.5
        keystroke "g" using {{command down, shift down}}
        delay 2.5
        keystroke "a" using {{command down}}
        delay 0.3
        keystroke "v" using {{command down}}
        delay 1
        key code 36
        delay 2.5
        key code 36
        delay {_upload_wait}
        keystroke return
        delay 2
    end tell
end tell'''
    r3 = _run_applescript(script3)
    shutil.rmtree(tmp_dir, ignore_errors=True)
    if r3.returncode != 0:
        err = r3.stderr.strip() or r3.stdout.strip() or "erro desconhecido"
        return False, f"Erro ao enviar documento: {err}"
    return True, "ok"


def send_whatsapp_auto(phone, message, nome="", empresa="", wait_time=18, file_path=None, file_paths=None, close_tab=True):
    """
    Envia mensagem (+ 1 ou vários arquivos opcionais) via WhatsApp Web.
    Reutiliza o tab existente para evitar 'WhatsApp aberto em outra janela'.
    Usa pyautogui para cliques de hardware (evita timeout -1712 do System Events).
    """
    # Normaliza a lista de arquivos (aceita file_path único OU file_paths lista)
    files = [f for f in (file_paths or []) if f]
    if not files and file_path:
        files = [file_path]

    if not IS_MACOS:
        return _send_whatsapp_windows(phone, message, nome, empresa, wait_time, files)
    phone_clean = clean_phone(phone)
    if not phone_clean:
        return False, "Número de telefone inválido."

    msg = personalize(message, nome, empresa)
    encoded = urllib.parse.quote(msg)
    url = f"https://web.whatsapp.com/send?phone={phone_clean}&text={encoded}"
    safe_url = url.replace('"', '\\"')

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
end tell
delay 2'''

    r1 = _run_applescript(script1)
    if r1.returncode != 0:
        err = r1.stderr.strip() or r1.stdout.strip() or "erro desconhecido"
        return False, f"Erro AppleScript: {err}"

    # Sem arquivos: fecha o tab e retorna
    if not files:
        if close_tab:
            _close_whatsapp_tab()
        return True, "Mensagem enviada com sucesso."

    # Geometria da janela do Chrome (uma vez para todos os anexos)
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
        wx, wy, ww, wh = 0, 121, 1440, 779  # fallback tela cheia

    # Envia cada arquivo em sequência no mesmo chat
    enviados = 0
    falhas = []
    for idx, f in enumerate(files):
        ok, m = _attach_file_mac(f, wx, wy, ww, wh)
        if ok:
            enviados += 1
        else:
            falhas.append(f"{os.path.basename(f)}: {m}")
        if idx < len(files) - 1:
            time.sleep(3)  # respiro entre anexos

    if close_tab:
        _close_whatsapp_tab()

    if falhas:
        return (enviados > 0), (f"Mensagem enviada. {enviados}/{len(files)} arquivo(s) OK. "
                                f"Falha: {'; '.join(falhas)}")
    return True, f"Mensagem e {enviados} arquivo(s) enviados com sucesso."


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
