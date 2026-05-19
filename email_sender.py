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

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

SENT_FOLDERS = ["INBOX.enviadas", "INBOX.Sent", "INBOX.Sent Itens", "INBOX.Itens Enviados", "Sent", "Sent Items"]


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
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


def _build_message(cfg, to_email, to_name, empresa, subject, body, attachment_paths=None):
    body_final = personalize(body, to_name, empresa)
    subject_final = personalize(subject, to_name, empresa)
    remetente = cfg['remetente']
    nome_exib = cfg.get('nome_exibicao', '')

    sig_path = cfg.get('assinatura_imagem', '')
    has_sig = sig_path and os.path.exists(sig_path)
    has_attach = bool(attachment_paths)

    if has_sig:
        # mixed > related > (alternative > plain+html) + inline image [+ attachments]
        msg = MIMEMultipart('mixed')
        related = MIMEMultipart('related')
        alternative = MIMEMultipart('alternative')

        html_body = (
            "<html><body style='font-family:Arial,sans-serif;font-size:14px'>"
            + body_final.replace('\n', '<br>')
            + "<br><br><img src='cid:assinatura' style='max-width:600px'>"
            + "</body></html>"
        )
        alternative.attach(MIMEText(body_final, 'plain', 'utf-8'))
        alternative.attach(MIMEText(html_body, 'html', 'utf-8'))
        related.attach(alternative)

        with open(sig_path, 'rb') as f:
            img_data = f.read()
        img_mime = MIMEImage(img_data)
        img_mime.add_header('Content-ID', '<assinatura>')
        img_mime.add_header('Content-Disposition', 'inline', filename=os.path.basename(sig_path))
        related.attach(img_mime)
        msg.attach(related)

    elif has_attach:
        # mixed > alternative > (plain+html) [+ attachments]
        msg = MIMEMultipart('mixed')
        alternative = MIMEMultipart('alternative')
        html_body = (
            "<html><body style='font-family:Arial,sans-serif;font-size:14px'>"
            + body_final.replace('\n', '<br>')
            + "</body></html>"
        )
        alternative.attach(MIMEText(body_final, 'plain', 'utf-8'))
        alternative.attach(MIMEText(html_body, 'html', 'utf-8'))
        msg.attach(alternative)

    else:
        msg = MIMEMultipart('alternative')
        html_body = (
            "<html><body style='font-family:Arial,sans-serif;font-size:14px'>"
            + body_final.replace('\n', '<br>')
            + "</body></html>"
        )
        msg.attach(MIMEText(body_final, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    # Attach files (works for both has_sig and has_attach cases)
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
