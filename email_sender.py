import smtplib
import imaplib
import json
import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

SENT_FOLDERS = ["INBOX.enviadas", "INBOX.Sent", "INBOX.Sent Itens", "INBOX.Itens Enviados", "Sent", "Sent Items"]


def set_user_config_path(path: str):
    """Define o caminho do config.json do usuário logado."""
    global _CONFIG_PATH
    _CONFIG_PATH = path


def load_config():
    with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


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


_thumb_cache = {}


def _find_youtube_url(text):
    """Retorna a primeira URL do YouTube encontrada no texto (ou None)."""
    import re
    m = re.search(r'https?://(?:www\.)?(?:youtu\.be/|youtube\.com/)[^\s]+', text or '')
    return m.group(0) if m else None


def _youtube_id(url):
    """Extrai o ID do vídeo de uma URL do YouTube."""
    import re
    m = re.search(r'(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|shorts/|v/))([A-Za-z0-9_-]{6,})', url or '')
    return m.group(1) if m else None


def _make_video_thumb(video_id):
    """Baixa a thumbnail do vídeo do YouTube e sobrepõe um botão de play.
    Retorna os bytes PNG (ou None em caso de erro). Faz cache por vídeo."""
    if not video_id:
        return None
    if video_id in _thumb_cache:
        return _thumb_cache[video_id]
    try:
        from PIL import Image, ImageDraw
        import urllib.request
        import io

        data = None
        for q in ('maxresdefault', 'hqdefault'):
            try:
                url = f'https://img.youtube.com/vi/{video_id}/{q}.jpg'
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                d = urllib.request.urlopen(req, timeout=10).read()
                if d and len(d) > 1500:
                    data = d
                    break
            except Exception:
                continue
        if not data:
            return None

        img = Image.open(io.BytesIO(data)).convert('RGBA')
        W, H = img.size
        overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)

        # Círculo semitransparente + triângulo branco (botão de play)
        r = int(min(W, H) * 0.13)
        cx, cy = W // 2, H // 2
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(200, 30, 30, 220))
        t = int(r * 0.55)
        d.polygon([(cx - t // 2, cy - t), (cx - t // 2, cy + t), (cx + t, cy)],
                  fill=(255, 255, 255, 245))

        combined = Image.alpha_composite(img, overlay).convert('RGB')

        # Reduz fisicamente para ~520px de largura (Outlook ignora max-width do CSS)
        target_w = 520
        if combined.width > target_w:
            ratio = target_w / combined.width
            combined = combined.resize((target_w, int(combined.height * ratio)), Image.LANCZOS)

        out = io.BytesIO()
        combined.save(out, format='PNG')
        thumb = out.getvalue()
        _thumb_cache[video_id] = thumb
        return thumb
    except Exception:
        return None


def _text_to_html(text, video_url=None, video_cid=None):
    """Converte o texto do template em HTML formatado para e-mail.
    - Parágrafos (separados por linha em branco) viram <p> com espaçamento real.
    - Linhas iniciadas por •, - ou * viram tópicos.
      * Tópico seguido de uma linha de descrição → nome em negrito + descrição embaixo.
      * Tópico de linha única → texto simples (sem negrito).
    - **texto** vira negrito; URLs viram links clicáveis.
    - Se video_url/video_cid forem passados, a URL do vídeo vira uma imagem
      clicável (thumbnail com botão de play) embutida no corpo.
    """
    import re

    def fmt(s):
        s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
        placeholder = None
        if video_url and video_cid and video_url in s:
            placeholder = '\x00VID\x00'
            s = s.replace(video_url, placeholder)
        s = re.sub(r'(https?://[^\s<]+)', r'<a href="\1">\1</a>', s)
        if placeholder:
            img_link = (f'<br><a href="{video_url}">'
                        f'<img src="cid:{video_cid}" width="520" '
                        f'style="width:520px;max-width:100%;border-radius:8px;display:block" '
                        f'alt="Assistir ao video"></a>')
            s = s.replace(placeholder, img_link)
        return s

    lines = text.split('\n')
    html = []
    para_buf = []
    i, n = 0, len(lines)

    def flush_para():
        if para_buf:
            html.append('<p style="margin:0 0 12px 0">'
                        + '<br>'.join(fmt(l) for l in para_buf)
                        + '</p>')
            para_buf.clear()

    while i < n:
        raw = lines[i]
        m = re.match(r'^\s*[•\-\*]\s+(.*)', raw)
        if m:
            flush_para()
            html.append('<ul style="margin:0 0 12px 0;padding-left:24px">')
            while i < n:
                mm = re.match(r'^\s*[•\-\*]\s+(.*)', lines[i])
                if not mm:
                    break
                name = mm.group(1).strip()
                i += 1
                desc = ''
                if i < n and lines[i].strip() != '' and not re.match(r'^\s*[•\-\*]\s+', lines[i]):
                    desc = lines[i].strip()
                    i += 1
                if desc:
                    html.append('<li style="margin-bottom:6px"><b>' + fmt(name)
                                + '</b><br>' + fmt(desc) + '</li>')
                else:
                    html.append('<li style="margin-bottom:6px">' + fmt(name) + '</li>')
            html.append('</ul>')
        elif raw.strip() == '':
            flush_para()
            i += 1
        else:
            para_buf.append(raw.strip())
            i += 1

    flush_para()
    return ''.join(html)


_HTML_OPEN = ("<html><body style='font-family:Calibri,Arial,sans-serif;"
              "font-size:12pt;color:#000000;line-height:1.5'>")
_HTML_CLOSE = "</body></html>"


def _build_message(cfg, to_email, to_name, empresa, subject, body, attachment_paths=None):
    body_final = personalize(body, to_name, empresa)
    subject_final = personalize(subject, to_name, empresa)
    remetente = cfg['remetente']
    nome_exib = cfg.get('nome_exibicao', '')

    sig_path = cfg.get('assinatura_imagem', '')
    has_sig = sig_path and os.path.exists(sig_path)
    has_attach = bool(attachment_paths)

    # Imagens embutidas no corpo (cid, bytes, nome)
    inline_images = []

    # Detecta vídeo do YouTube → gera thumbnail clicável com botão de play
    video_url = _find_youtube_url(body_final)
    video_cid = None
    if video_url:
        thumb = _make_video_thumb(_youtube_id(video_url))
        if thumb:
            video_cid = 'videothumb'
            inline_images.append((video_cid, thumb, 'video.png'))

    html_inner = _text_to_html(body_final, video_url=video_url, video_cid=video_cid)

    if has_sig:
        with open(sig_path, 'rb') as f:
            inline_images.append(('assinatura', f.read(), os.path.basename(sig_path)))
        html_inner += "<br><br><img src='cid:assinatura' style='max-width:600px'>"

    html_body = _HTML_OPEN + html_inner + _HTML_CLOSE

    # Estrutura unificada: mixed > related > (alternative > plain+html) + imagens inline [+ anexos]
    msg = MIMEMultipart('mixed')
    related = MIMEMultipart('related')
    alternative = MIMEMultipart('alternative')
    alternative.attach(MIMEText(body_final, 'plain', 'utf-8'))
    alternative.attach(MIMEText(html_body, 'html', 'utf-8'))
    related.attach(alternative)

    for cid, data, fname in inline_images:
        img_mime = MIMEImage(data)
        img_mime.add_header('Content-ID', f'<{cid}>')
        img_mime.add_header('Content-Disposition', 'inline', filename=fname)
        related.attach(img_mime)

    msg.attach(related)

    # Anexos (arquivos que ficam no rodapé do e-mail)
    if has_attach:
        for fpath in attachment_paths:
            if os.path.exists(fpath):
                with open(fpath, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment',
                                filename=os.path.basename(fpath))
                msg.attach(part)

    msg['Subject'] = subject_final
    msg['From'] = f"{nome_exib} <{remetente}>" if nome_exib else remetente
    msg['To'] = to_email
    return msg


def _save_to_sent(msg_bytes, cfg):
    imap_host = cfg.get('imap_server') or cfg.get('smtp_server', '').replace('smtp.', 'mail.').replace('mail.', 'mail.')
    try:
        with imaplib.IMAP4_SSL(imap_host, 993, timeout=10) as imap:
            imap.login(cfg['remetente'], cfg['senha'])
            for folder in SENT_FOLDERS:
                try:
                    result = imap.append(folder, r'\Seen', None, msg_bytes)
                    if result[0] == 'OK':
                        return True
                except Exception:
                    continue
    except Exception:
        pass
    return False


def send_email(to_email, to_name, empresa, subject, body, attachment_paths=None):
    config = load_config()
    cfg = config['email']

    if not cfg.get('remetente') or not cfg.get('senha'):
        raise ValueError("Configure o e-mail e senha em Configurações antes de enviar.")

    msg = _build_message(cfg, to_email, to_name, empresa, subject, body, attachment_paths)

    with smtplib.SMTP(cfg['smtp_server'], cfg['smtp_port'], timeout=15) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(cfg['remetente'], cfg['senha'])
        server.send_message(msg)

    # Save to Sent folder via IMAP
    _save_to_sent(msg.as_bytes(), cfg)


def test_connection():
    config = load_config()
    cfg = config['email']

    if not cfg.get('remetente') or not cfg.get('senha'):
        return False, "E-mail ou senha não configurados."

    try:
        with smtplib.SMTP(cfg['smtp_server'], cfg['smtp_port'], timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(cfg['remetente'], cfg['senha'])
        return True, "Conexão estabelecida com sucesso!"
    except smtplib.SMTPAuthenticationError:
        return False, "Erro de autenticação. Verifique e-mail e senha."
    except smtplib.SMTPException as e:
        return False, f"Erro SMTP: {str(e)}"
    except Exception as e:
        return False, f"Erro de conexão: {str(e)}"
