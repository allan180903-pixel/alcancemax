import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import os
import time
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

import database as db
import email_sender as es
import whatsapp_helper as wh
import report_generator as rg
import license as lic

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AlcanceMax",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# ── LOGO BASE64 ───────────────────────────────────────────────────────────────
import base64 as _b64
_LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
with open(_LOGO_PATH, "rb") as _f:
    _LOGO_B64 = _b64.b64encode(_f.read()).decode()

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after { font-family: 'Inter', -apple-system, sans-serif !important; box-sizing: border-box; }

/* Seta CSS no expander */
details > summary::before {
    content: '›';
    font-family: 'Inter', sans-serif !important;
    font-size: 1.3rem !important;
    font-weight: 300 !important;
    color: #9CA3AF;
    margin-right: 8px;
    display: inline-block;
    transition: transform 0.15s;
    vertical-align: middle;
}
details[open] > summary::before { transform: rotate(90deg); color: #059669; }
html, body, .stApp { background: #F8FAFC !important; }
[data-testid="stAppViewContainer"], [data-testid="stMain"],
[data-testid="stMainBlockContainer"], section.main { background: #F8FAFC !important; }

#MainMenu, footer, [data-testid="stHeader"], header { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
/* Esconde botões de fechar/abrir sidebar — sidebar sempre visível */
[data-testid="collapsedControl"] { display: none !important; }
[data-testid="stSidebarCollapseButton"] { display: none !important; }

/* ── SIDEBAR SEMPRE VISÍVEL ──────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #E2E8F0 !important;
    box-shadow: 2px 0 8px rgba(0,0,0,0.04) !important;
    transform: none !important;
    display: block !important;
    visibility: visible !important;
    min-width: 240px !important;
    width: 240px !important;
    position: relative !important;
    left: 0 !important;
    margin-left: 0 !important;
}
[data-testid="stSidebar"] > div { background: #FFFFFF !important; }
[data-testid="stSidebar"] * { color: #374151 !important; }
[data-testid="stSidebar"] hr { border-color: #F1F5F9 !important; margin: 10px 0 !important; }

[data-testid="stSidebar"] .stRadio { margin: 0 !important; }
[data-testid="stSidebar"] .stRadio > div > label {
    display: flex !important; align-items: center !important;
    padding: 10px 14px !important; margin: 2px 0 !important;
    border-radius: 8px !important; cursor: pointer !important;
    transition: all 0.15s !important; font-size: 0.875rem !important;
    font-weight: 500 !important; color: #6B7280 !important;
}
[data-testid="stSidebar"] .stRadio > div > label:hover {
    background: #F0FDF4 !important; color: #059669 !important;
}
[data-testid="stSidebar"] .stRadio > div [aria-checked="true"] ~ div,
[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {
    background: #ECFDF5 !important; color: #059669 !important; font-weight: 600 !important;
}
[data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child,
[data-testid="stSidebar"] .stRadio span[data-testid="stMarkdownContainer"] > p { display: none !important; }

/* ── METRIC CARDS ────────────────────────────────────────────── */
.metric-card {
    background: #FFFFFF; border-radius: 14px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    padding: 22px 20px; text-align: left;
    transition: box-shadow 0.2s;
}
.metric-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.09); }
.metric-icon { font-size: 1.5rem; margin-bottom: 10px; }
.metric-value { font-size: 2.1rem; font-weight: 700; color: #0F172A; line-height: 1.1; }
.metric-label { color: #6B7280; font-size: 0.8rem; font-weight: 500; margin-top: 6px; }
.metric-accent { display: inline-block; width: 4px; height: 100%; background: #059669; }

/* ── BOTÕES ──────────────────────────────────────────────────── */
.stButton > button {
    background: #059669 !important; color: #FFFFFF !important;
    border: none !important; border-radius: 8px !important;
    font-weight: 600 !important; font-size: 0.875rem !important;
    padding: 9px 20px !important; transition: all 0.15s !important;
    box-shadow: 0 1px 3px rgba(5,150,105,0.3) !important;
}
.stButton > button:hover { background: #047857 !important; box-shadow: 0 4px 12px rgba(5,150,105,0.35) !important; transform: translateY(-1px) !important; }
.stButton > button:active { transform: translateY(0) !important; }
.stButton > button[kind="secondary"] {
    background: #FFFFFF !important; color: #374151 !important;
    border: 1px solid #E2E8F0 !important; box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
}
.stButton > button[kind="secondary"]:hover { background: #F9FAFB !important; border-color: #D1D5DB !important; box-shadow: none !important; transform: none !important; }

/* ── INPUTS ──────────────────────────────────────────────────── */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
    border: 1.5px solid #E5E7EB !important; border-radius: 8px !important;
    background: #FFFFFF !important; color: #111827 !important;
    font-size: 0.9rem !important; padding: 9px 12px !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}
.stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {
    border-color: #059669 !important; box-shadow: 0 0 0 3px rgba(5,150,105,0.10) !important; outline: none !important;
}
.stSelectbox > div > div { border: 1.5px solid #E5E7EB !important; border-radius: 8px !important; background: #FFFFFF !important; }
.stSelectbox > div > div:focus-within { border-color: #059669 !important; box-shadow: 0 0 0 3px rgba(5,150,105,0.10) !important; }

.stTextInput label, .stTextArea label, .stSelectbox label, .stNumberInput label {
    font-weight: 500 !important; font-size: 0.85rem !important; color: #374151 !important; margin-bottom: 4px !important;
}

div[data-testid="stForm"] {
    background: #FFFFFF !important; padding: 28px !important;
    border-radius: 14px !important; border: 1px solid #E5E7EB !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid #E5E7EB !important; border-radius: 12px !important;
    background: #FFFFFF !important; overflow: hidden !important;
}

[data-testid="stExpander"] { border: 1px solid #E5E7EB !important; border-radius: 10px !important; background: #FFFFFF !important; overflow: hidden !important; }
[data-testid="stExpander"] summary { font-weight: 500 !important; font-size: 0.9rem !important; color: #374151 !important; padding: 12px 16px !important; }
[data-testid="stExpander"] summary:hover { background: #F9FAFB !important; }

.stTabs [data-baseweb="tab-list"] { border-bottom: 2px solid #E5E7EB !important; gap: 0 !important; background: transparent !important; }
.stTabs [data-baseweb="tab"] { font-weight: 500 !important; color: #6B7280 !important; padding: 10px 18px !important; border-bottom: 2px solid transparent !important; margin-bottom: -2px !important; background: transparent !important; font-size: 0.875rem !important; }
.stTabs [data-baseweb="tab"]:hover { color: #059669 !important; }
.stTabs [aria-selected="true"] { color: #059669 !important; border-bottom: 2px solid #059669 !important; font-weight: 600 !important; }

[data-testid="stDataFrame"] { border-radius: 10px !important; overflow: hidden !important; border: 1px solid #E5E7EB !important; }
[data-testid="stDataFrame"] th { background: #F9FAFB !important; color: #374151 !important; font-weight: 600 !important; font-size: 0.78rem !important; text-transform: uppercase !important; letter-spacing: 0.06em !important; padding: 10px 14px !important; border-bottom: 1.5px solid #E5E7EB !important; }
[data-testid="stDataFrame"] td { font-size: 0.875rem !important; color: #374151 !important; padding: 9px 14px !important; border-bottom: 1px solid #F3F4F6 !important; }

[data-testid="stAlert"] { border-radius: 8px !important; border: none !important; }

.success-banner { background: #ECFDF5; color: #065F46; padding: 12px 16px; border-radius: 8px; border-left: 4px solid #059669; font-size: 0.875rem; margin: 8px 0; }
.warning-banner { background: #FFFBEB; color: #92400E; padding: 12px 16px; border-radius: 8px; border-left: 4px solid #D97706; font-size: 0.875rem; margin: 8px 0; }
.info-banner    { background: #F0FDF4; color: #065F46; padding: 12px 16px; border-radius: 8px; border-left: 4px solid #10B981; font-size: 0.875rem; margin: 8px 0; }
.error-banner   { background: #FEF2F2; color: #991B1B; padding: 12px 16px; border-radius: 8px; border-left: 4px solid #DC2626; font-size: 0.875rem; margin: 8px 0; }

.badge      { background: #D1FAE5; color: #065F46; padding: 3px 10px; border-radius: 20px; font-size: 0.72rem; font-weight: 700; display: inline-block; }
.badge-gray { background: #F3F4F6; color: #4B5563; padding: 3px 10px; border-radius: 20px; font-size: 0.72rem; font-weight: 700; display: inline-block; }
.badge-red  { background: #FEF2F2; color: #991B1B; padding: 3px 10px; border-radius: 20px; font-size: 0.72rem; font-weight: 700; display: inline-block; }

h1 { font-weight: 700 !important; color: #111827 !important; font-size: 1.65rem !important; letter-spacing: -0.3px !important; }
h2 { font-weight: 600 !important; color: #111827 !important; font-size: 1.15rem !important; }
h3 { font-weight: 600 !important; color: #1F2937 !important; font-size: 1rem !important; }
hr { border: none !important; border-top: 1px solid #E5E7EB !important; margin: 16px 0 !important; }

[data-testid="stSpinner"] { color: #059669 !important; }
[data-testid="stProgress"] > div > div { background: #059669 !important; }
.stCheckbox label { font-size: 0.875rem !important; color: #374151 !important; }
[data-baseweb="checkbox"] > div { border-color: #D1D5DB !important; }
[data-baseweb="checkbox"][aria-checked="true"] > div { background: #059669 !important; border-color: #059669 !important; }
[data-baseweb="tag"] { background: #D1FAE5 !important; color: #065F46 !important; border-radius: 4px !important; }

/* PAGE HEADER */
.page-header { margin-bottom: 28px; }
.page-greeting { font-size: 1.9rem; font-weight: 700; color: #111827; letter-spacing: -0.5px; line-height: 1.2; }
.page-title    { font-size: 1.5rem; font-weight: 700; color: #111827; letter-spacing: -0.3px; }
.page-subtitle { font-size: 0.9rem; color: #6B7280; margin-top: 5px; }

[data-testid="stCaptionContainer"] { color: #9CA3AF !important; font-size: 0.8rem !important; }
.stNumberInput button { background: #F9FAFB !important; border: 1px solid #E5E7EB !important; color: #374151 !important; }

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #F9FAFB; }
::-webkit-scrollbar-thumb { background: #D1D5DB; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #9CA3AF; }

/* Botão de REABRIR sidebar — sempre visível e destacado */
[data-testid="collapsedControl"] {
    background: #059669 !important;
    border-radius: 0 10px 10px 0 !important;
    padding: 10px 6px !important;
    box-shadow: 3px 0 12px rgba(5,150,105,0.3) !important;
}
[data-testid="collapsedControl"] button { color: #FFFFFF !important; }

/* ── ESCONDER ÍCONE keyboard_arrow NOS EXPANDERS ────────────────── */
/* data-testid="stIconMaterial" é o atributo exato do ícone no bundle */
[data-testid="stIconMaterial"] {
    font-size: 0 !important;
    line-height: 0 !important;
    width: 0 !important;
    height: 0 !important;
    display: inline-block !important;
    overflow: hidden !important;
    opacity: 0 !important;
}

</style>
""", unsafe_allow_html=True)


# ── FIX ÍCONE EXPANDER (keyboard_arrow_right via JS) ─────────────────────────
components.html("""
<script>
(function() {
    function fixExpanders() {
        try {
            var doc = window.parent.document;
            doc.querySelectorAll('details > summary').forEach(function(summary) {
                Array.from(summary.childNodes).forEach(function(node) {
                    // Text node com "keyboard_arrow"
                    if (node.nodeType === 3 && node.textContent.indexOf('keyboard_arrow') !== -1) {
                        node.textContent = '';
                    }
                    // Element node cujo conteúdo é exatamente o nome do ícone
                    else if (node.nodeType === 1) {
                        var t = node.textContent.trim();
                        if (t === 'keyboard_arrow_right' || t === 'keyboard_arrow_down' || t === 'keyboard_arrow_up') {
                            node.style.setProperty('font-size', '0', 'important');
                            node.style.setProperty('line-height', '0', 'important');
                            node.style.setProperty('color', 'transparent', 'important');
                            node.style.setProperty('width', '0', 'important');
                            node.style.setProperty('overflow', 'hidden', 'important');
                        }
                    }
                });
            });
        } catch(e) {}
    }
    fixExpanders();
    setInterval(fixExpanders, 300);
    try {
        new MutationObserver(fixExpanders).observe(
            window.parent.document.documentElement,
            {childList: true, subtree: true}
        );
    } catch(e) {}
})();
</script>
""", height=0)

# ── LOGIN SCREEN ─────────────────────────────────────────────────────────────

def _show_login():
    """Tela de login/ativação de licença."""
    st.markdown(f"""
    <style>
        .login-box {{
            max-width: 440px; margin: 60px auto; padding: 40px;
            background: white; border-radius: 16px;
            box-shadow: 0 8px 40px rgba(0,0,0,0.10);
            border-top: 5px solid #059669;
        }}
        .login-title {{ font-size: 2rem; font-weight: 800; color: #064E3B; text-align: center; margin-bottom: 4px; }}
        .login-sub   {{ text-align: center; color: #64748B; margin-bottom: 28px; font-size: 0.95rem; }}
        .login-footer{{ text-align: center; color: #aaa; font-size: 0.8rem; margin-top: 20px; }}
        .login-logo  {{ text-align: center; margin-bottom: 20px; }}
    </style>
    <div class="login-box">
        <div class="login-logo">
            <img src='data:image/jpeg;base64,{_LOGO_B64}' style='max-width:220px;width:100%;height:auto;' alt='AlcanceMax'>
        </div>
        <div class="login-title">Bem-vindo de volta</div>
        <div class="login-sub">Prospecção Inteligente</div>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:
        with st.form("login_form"):
            st.markdown("### Ativar Licença")
            email = st.text_input("E-mail", placeholder="seu@email.com")
            key   = st.text_input("Chave de Licença", placeholder="XXXX-XXXX-XXXX-XXXX")
            submitted = st.form_submit_button("🔓 Entrar", use_container_width=True, type="primary")

            if submitted:
                if not email or not key:
                    st.error("Preencha e-mail e chave de licença.")
                else:
                    with st.spinner("Validando licença..."):
                        result = lic.validate_license(email, key)
                    if result["valid"]:
                        lic._save_session(email, key, result["plan"],
                                          role=result.get("role", lic.ROLE_USER),
                                          agency_id=result.get("agency_id"),
                                          max_users=result.get("max_users", 1),
                                          nome=result.get("nome", ""))
                        st.session_state["authenticated"] = True
                        st.session_state["user_email"]    = email
                        st.session_state["user_plan"]     = result["plan"]
                        st.session_state["user_role"]     = result.get("role", lic.ROLE_USER)
                        st.session_state["agency_id"]     = result.get("agency_id")
                        st.session_state["max_users"]     = result.get("max_users", 1)
                        st.session_state["user_nome"]     = result.get("nome", "")
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])

        st.markdown(
            "<div style='text-align:center;color:#aaa;font-size:0.8rem;margin-top:12px'>"
            "Não tem licença? Fale conosco pelo WhatsApp para adquirir a sua."
            "</div>", unsafe_allow_html=True)


def _check_auth():
    """Verifica se o usuário está autenticado. Tenta sessão local primeiro."""
    if st.session_state.get("authenticated"):
        return True
    session = lic._load_session()
    if session:
        st.session_state["authenticated"] = True
        st.session_state["user_email"]    = session.get("email", "")
        st.session_state["user_plan"]     = session.get("plan", "starter")
        st.session_state["user_role"]     = session.get("role", lic.ROLE_USER)
        st.session_state["agency_id"]     = session.get("agency_id")
        st.session_state["max_users"]     = session.get("max_users", 1)
        st.session_state["user_nome"]     = session.get("nome", "")
        return True
    return False


def _is_super_admin():
    return (st.session_state.get("user_role") == lic.ROLE_SUPER_ADMIN or
            st.session_state.get("user_email") == lic.ADMIN_EMAIL)

def _is_agency_admin():
    return st.session_state.get("user_role") == lic.ROLE_AGENCY_ADMIN


# Bloqueia o app se não autenticado
if not _check_auth():
    _show_login()
    st.stop()


# ── HELPERS ──────────────────────────────────────────────────────────────────

def _default_config():
    """Config em branco para novos usuários."""
    return {
        "email": {
            "remetente": "", "senha": "", "smtp_server": "smtp.gmail.com",
            "smtp_port": 587, "nome_exibicao": "", "assinatura_imagem": ""
        },
        "filtros": {
            "status": ["Novo", "Email Enviado", "WhatsApp Enviado", "Contatado",
                       "Respondeu", "Reunião Agendada", "Fechado", "Sem Interesse"],
            "segmentos": ["Arquiteto", "Designer de Interiores", "Construtora",
                          "Incorporadora", "Loja de Móveis", "Decorador", "Outro"]
        },
        "fallbacks": {"nome": "prezado(a)", "empresa": "sua empresa"},
        "templates": {
            "email": [{"nome": "Prospecção Inicial", "assunto": "", "corpo": ""}],
            "whatsapp": [{"nome": "Prospecção Inicial", "mensagem": ""}]
        }
    }


def load_config():
    path = db.get_user_config_path()
    if not os.path.exists(path):
        return _default_config()
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return _default_config()


def save_config(config):
    path = db.get_user_config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def banner(text, kind="success"):
    css_class = f"{kind}-banner"
    st.markdown(f'<div class="{css_class}">{text}</div>', unsafe_allow_html=True)


# ── INIT — configura caminhos isolados por usuário ───────────────────────────
_current_user = st.session_state.get("user_email", "")
db.set_user(_current_user)
es.set_user_config_path(db.get_user_config_path())
db.init_db()

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='padding:16px 8px 20px 8px;text-align:center;'>
        <img src='data:image/jpeg;base64,{_LOGO_B64}' style='max-width:180px;width:100%;height:auto;' alt='AlcanceMax'>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    _nav_pages = ["Dashboard", "Leads", "E-mail", "WhatsApp", "Relatórios", "Configurações"]
    if _is_agency_admin():
        _nav_pages.append("Minha Agência")
    if _is_super_admin():
        _nav_pages.append("Admin")
    page = st.radio("Navegação", _nav_pages, label_visibility="collapsed")

    st.divider()

    _nome_display  = st.session_state.get("user_nome", "")
    _email_display = st.session_state.get("user_email", "")
    _plan_display  = lic.PLANS.get(st.session_state.get("user_plan",""), {}).get("nome", "")
    _role_display  = st.session_state.get("user_role", lic.ROLE_USER)
    _role_label    = {"super_admin": "Super Admin", "agency_admin": "Gestor", "user": "Usuário"}.get(_role_display, "")
    _initials      = (_nome_display or _email_display or "U")[0].upper()

    st.markdown(f"""
    <div style='padding:12px;background:#F9FAFB;border-radius:10px;border:1px solid #E5E7EB;margin-bottom:12px;display:flex;align-items:center;gap:10px;'>
        <div style='width:32px;height:32px;background:#ECFDF5;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;'>
            <span style='color:#059669;font-weight:700;font-size:0.85rem;'>{_initials}</span>
        </div>
        <div style='overflow:hidden;'>
            <div style='font-size:0.85rem;font-weight:600;color:#111827;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{_nome_display or _email_display}</div>
            <div style='font-size:0.72rem;color:#9CA3AF;margin-top:1px;'>{_plan_display} · {_role_label}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Sair", use_container_width=True, type="secondary"):
        lic.clear_session()
        st.session_state.clear()
        st.rerun()

    st.markdown(f"<div style='margin-top:12px;font-size:0.7rem;color:#D1D5DB;text-align:center;'>v1.0 · {datetime.now().strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)



# ════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════════════════════
if page == "Dashboard":
    _primeiro_nome = (st.session_state.get("user_nome", "") or "").split()[0] or "você"
    st.markdown(f"""
    <div class='page-header'>
        <div class='page-greeting'>Olá, {_primeiro_nome} 👋</div>
        <div class='page-subtitle'>Aqui está o resumo da sua prospecção</div>
    </div>
    """, unsafe_allow_html=True)
    stats = db.get_stats()

    _layout_kwargs = dict(
        plot_bgcolor='#FFFFFF',
        paper_bgcolor='#FFFFFF',
        font=dict(family='Inter, sans-serif', color='#374151', size=12),
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(showgrid=False, tickfont=dict(size=11, color='#64748B'), linecolor='#E2E8F0'),
        yaxis=dict(showgrid=True, gridcolor='#F1F5F9', tickfont=dict(size=11, color='#64748B'), linecolor='rgba(0,0,0,0)'),
        showlegend=False,
    )

    col1, col2, col3, col4, col5 = st.columns(5)
    metrics = [
        (col1, "Total de Leads",     stats['total_leads'],       "👥"),
        (col2, "E-mails (7 dias)",   stats['emails_semana'],     "📧"),
        (col3, "WhatsApp (7 dias)",  stats['whatsapp_semana'],   "💬"),
        (col4, "E-mails (total)",    stats['total_emails'],      "📨"),
        (col5, "WhatsApp (total)",   stats['total_whatsapp'],    "📲"),
    ]
    for col, label, val, icon in metrics:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">{icon}</div>
                <div class="metric-value">{val}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Leads por Status")
        if not stats['por_status'].empty:
            fig = px.bar(stats['por_status'], x='status', y='count', color_discrete_sequence=['#059669'])
            fig.update_layout(**_layout_kwargs)
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Nenhum lead cadastrado ainda.")

    with col_right:
        st.subheader("Leads por Segmento")
        if not stats['leads_por_segmento'].empty:
            fig2 = px.bar(stats['leads_por_segmento'], x='segmento', y='count', color_discrete_sequence=['#064E3B'])
            fig2.update_layout(**_layout_kwargs)
            fig2.update_traces(marker_line_width=0)
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Sem dados de segmento ainda.")

    st.markdown("---")
    st.subheader("Atividade dos Últimos 30 Dias")
    if not stats['atividade_diaria'].empty:
        df_act = stats['atividade_diaria'].pivot(index='data', columns='tipo', values='total').fillna(0).reset_index()
        fig3 = go.Figure()
        if 'email' in df_act.columns:
            fig3.add_trace(go.Bar(x=df_act['data'], y=df_act['email'], name='E-mail', marker_color='#059669'))
        if 'whatsapp' in df_act.columns:
            fig3.add_trace(go.Bar(x=df_act['data'], y=df_act['whatsapp'], name='WhatsApp', marker_color='#10B981'))
        fig3.update_layout(**{**_layout_kwargs, 'showlegend': True, 'barmode': 'group',
            'legend': dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=11))})
        st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("Nenhum envio registrado ainda.")

    st.markdown("---")
    st.subheader("Leads Recentes")
    all_leads = db.get_all_leads()
    if not all_leads.empty:
        recent = all_leads.head(10)[['nome', 'empresa', 'email', 'whatsapp', 'status', 'data_criacao']]
        recent.columns = ['Nome', 'Empresa', 'E-mail', 'WhatsApp', 'Status', 'Data']
        st.dataframe(recent, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum lead cadastrado. Vá para **Leads** para adicionar.")


# ════════════════════════════════════════════════════════════════════════════
# LEADS
# ════════════════════════════════════════════════════════════════════════════
elif page == "Leads":
    st.markdown("""
    <div class='page-header'>
        <div class='page-title'>Leads</div>
        <div class='page-subtitle'>Gerencie seus contatos e oportunidades</div>
    </div>
    """, unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📋 Lista de Leads", "➕ Novo Lead", "📥 Importar Planilha"])

    # ── TAB 1: LISTA ────────────────────────────────────────────────────────
    with tab1:
        all_leads = db.get_all_leads()

        col_filter1, col_filter2, col_search = st.columns([2, 2, 3])
        with col_filter1:
            status_filter = st.selectbox("Filtrar por Status", ["Todos"] + db.get_status_options())
        with col_filter2:
            seg_filter = st.selectbox("Filtrar por Segmento", ["Todos"] + db.get_segmento_options())
        with col_search:
            search = st.text_input("🔍 Buscar por nome ou empresa", placeholder="Digite para buscar...")

        if not all_leads.empty:
            filtered = all_leads.copy()
            if status_filter != "Todos":
                filtered = filtered[filtered['status'] == status_filter]
            if seg_filter != "Todos":
                filtered = filtered[filtered['segmento'] == seg_filter]
            if search:
                mask = (filtered['nome'].str.contains(search, case=False, na=False) |
                        filtered['empresa'].str.contains(search, case=False, na=False))
                filtered = filtered[mask]

            st.markdown(f"**{len(filtered)} lead(s) encontrado(s)**")

            if not filtered.empty:
                for _, row in filtered.iterrows():
                    with st.expander(f"**{row['nome']}** — {row['empresa'] or '—'}  |  {row['status']}"):
                        c1, c2, c3 = st.columns(3)
                        c1.markdown(f"**E-mail:** {row['email'] or '—'}")
                        c1.markdown(f"**WhatsApp:** {row['whatsapp'] or '—'}")
                        c2.markdown(f"**Cidade:** {row['cidade'] or '—'}")
                        c2.markdown(f"**Segmento:** {row['segmento'] or '—'}")
                        c3.markdown(f"**Status:** {row['status']}")
                        c3.markdown(f"**Cadastrado em:** {row['data_criacao'][:10] if row['data_criacao'] else '—'}")
                        if row['notas']:
                            st.markdown(f"**Notas:** {row['notas']}")

                        edit_col, del_col = st.columns([3, 1])
                        with edit_col:
                            new_status = st.selectbox(
                                "Atualizar status", db.get_status_options(),
                                index=db.get_status_options().index(row['status']) if row['status'] in db.get_status_options() else 0,
                                key=f"status_{row['id']}")
                            if st.button("💾 Salvar Status", key=f"save_{row['id']}"):
                                db.update_lead_status(row['id'], new_status)
                                st.success("Status atualizado!")
                                st.rerun()
                        with del_col:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("🗑️ Excluir", key=f"del_{row['id']}", type="secondary"):
                                db.delete_lead(row['id'])
                                st.success("Lead excluído.")
                                st.rerun()
            else:
                st.info("Nenhum lead encontrado com os filtros selecionados.")
        else:
            st.info("Nenhum lead cadastrado. Use a aba **Novo Lead** ou **Importar Planilha**.")

    # ── TAB 2: NOVO LEAD ────────────────────────────────────────────────────
    with tab2:
        st.subheader("Adicionar Novo Lead")
        with st.form("new_lead_form"):
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome", placeholder="Ex: Ana Lima (opcional)")
            empresa = c2.text_input("Empresa", placeholder="Ex: Studio Lima Arquitetura")
            email = c1.text_input("E-mail", placeholder="ana@studio.com")
            whatsapp = c2.text_input("WhatsApp", placeholder="11999999999")
            cidade = c1.text_input("Cidade", placeholder="Ex: São Paulo")
            segmento = c2.selectbox("Segmento", [""] + db.get_segmento_options())
            notas = st.text_area("Notas / Observações", placeholder="Informações adicionais sobre o lead...")
            submitted = st.form_submit_button("✅ Adicionar Lead", type="primary")

        if submitted:
            if not empresa.strip() and not email.strip() and not whatsapp.strip():
                st.error("Preencha pelo menos a empresa, e-mail ou WhatsApp.")
            else:
                label = nome.strip() or empresa.strip() or email.strip() or whatsapp.strip()
                db.add_lead(nome.strip(), empresa.strip(), email.strip(),
                            whatsapp.strip(), cidade.strip(), segmento, notas.strip())
                st.success(f"Lead **{label}** adicionado com sucesso!")

    # ── TAB 3: IMPORTAR ─────────────────────────────────────────────────────
    with tab3:
        st.subheader("Importar Leads por Planilha")
        st.markdown("""
        <div class="info-banner">
        Faça upload de um arquivo <strong>.xlsx</strong> ou <strong>.csv</strong> com colunas:<br>
        <code>nome</code>, <code>empresa</code>, <code>email</code>, <code>whatsapp</code>, <code>cidade</code>, <code>segmento</code>, <code>notas</code>
        <br><em>Apenas a coluna <strong>nome</strong> é obrigatória.</em>
        </div>
        """, unsafe_allow_html=True)

        uploaded = st.file_uploader("Selecionar arquivo", type=["xlsx", "xls", "csv"])
        if uploaded:
            try:
                if uploaded.name.endswith('.csv'):
                    df_up = pd.read_csv(uploaded)
                else:
                    df_up = pd.read_excel(uploaded)

                st.markdown(f"**Prévia — {len(df_up)} linha(s) encontrada(s):**")
                st.dataframe(df_up.head(5), use_container_width=True, hide_index=True)

                if st.button("📥 Importar Leads", type="primary"):
                    imported, skipped = db.import_leads_from_df(df_up)
                    st.success(f"✅ {imported} lead(s) importado(s) com sucesso! {skipped} linha(s) ignorada(s).")
            except Exception as e:
                st.error(f"Erro ao ler o arquivo: {e}")


# ════════════════════════════════════════════════════════════════════════════
# E-MAIL
# ════════════════════════════════════════════════════════════════════════════
elif page == "E-mail":
    st.markdown("""
    <div class='page-header'>
        <div class='page-title'>E-mail</div>
        <div class='page-subtitle'>Envie campanhas personalizadas para seus leads</div>
    </div>
    """, unsafe_allow_html=True)
    config = load_config()

    if not config['email'].get('remetente'):
        st.warning("⚙️ Configure seu e-mail Outlook em **Configurações** antes de enviar.")
        st.stop()

    all_leads = db.get_all_leads()
    if all_leads.empty:
        st.info("Nenhum lead cadastrado. Adicione leads primeiro.")
        st.stop()

    leads_com_email = all_leads[all_leads['email'].notna() & (all_leads['email'] != '')]

    tab_enviar, tab_historico = st.tabs(["📤 Enviar E-mails", "📋 Histórico"])

    with tab_enviar:
        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.subheader("Selecionar Template")
            templates_email = config['templates']['email']
            template_names = [t['nome'] for t in templates_email]
            selected_template_name = st.selectbox("Template", template_names)
            template = next(t for t in templates_email if t['nome'] == selected_template_name)

            assunto = st.text_input("Assunto", value=template.get('assunto', ''))
            corpo = st.text_area("Corpo do e-mail", value=template.get('corpo', ''), height=200)
            st.markdown("<small>Use <code>{nome}</code> e <code>{empresa}</code> para personalizar automaticamente.</small>", unsafe_allow_html=True)

            st.markdown("---")
            uploaded_attachments = st.file_uploader(
                "📎 Anexos (opcional)",
                accept_multiple_files=True,
                help="Os mesmos anexos serão enviados para todos os destinatários selecionados."
            )

        with col_right:
            st.subheader("Filtrar Destinatários")
            status_f = st.multiselect("Status dos leads", db.get_status_options(), default=["Novo"])
            seg_f = st.multiselect("Segmento", db.get_segmento_options())

        # Filter leads
        targets = leads_com_email.copy()
        if status_f:
            targets = targets[targets['status'].isin(status_f)]
        if seg_f:
            targets = targets[targets['segmento'].isin(seg_f)]

        st.markdown(f"---\n**{len(targets)} lead(s) serão contactados**")

        if not targets.empty:
            st.dataframe(
                targets[['nome', 'empresa', 'email', 'status']].rename(
                    columns={'nome': 'Nome', 'empresa': 'Empresa', 'email': 'E-mail', 'status': 'Status'}),
                use_container_width=True, hide_index=True)

        if st.button("🚀 Enviar E-mails", type="primary", disabled=targets.empty or not assunto):
            if not assunto.strip():
                st.error("Preencha o assunto antes de enviar.")
            else:
                # Salva anexos em pasta temporária
                attachment_paths = []
                if uploaded_attachments:
                    tmp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados", "tmp")
                    os.makedirs(tmp_dir, exist_ok=True)
                    for uf in uploaded_attachments:
                        tmp_path = os.path.join(tmp_dir, uf.name)
                        with open(tmp_path, 'wb') as f:
                            f.write(uf.getvalue())
                        attachment_paths.append(tmp_path)

                progress = st.progress(0)
                status_text = st.empty()
                success_count = 0
                error_count = 0
                errors = []

                for i, (_, lead) in enumerate(targets.iterrows()):
                    status_text.markdown(f"Enviando para **{lead['nome']}**...")
                    try:
                        es.send_email(
                            lead['email'], lead['nome'], lead.get('empresa', ''),
                            assunto, corpo,
                            attachment_paths=attachment_paths or None
                        )
                        db.log_envio(lead['id'], 'email', selected_template_name)
                        db.update_lead_status(lead['id'], 'Email Enviado')
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        errors.append(f"{lead['nome']}: {str(e)}")

                    progress.progress((i + 1) / len(targets))
                    time.sleep(0.5)  # Avoid spam filters

                status_text.empty()
                progress.empty()

                if success_count:
                    st.success(f"✅ {success_count} e-mail(s) enviado(s) com sucesso!")
                if error_count:
                    st.error(f"❌ {error_count} erro(s):")
                    for err in errors:
                        st.markdown(f"- {err}")
                if success_count:
                    st.rerun()

    with tab_historico:
        import sqlite3
        conn = db.get_connection()
        hist = pd.read_sql_query(
            '''SELECT l.nome, l.empresa, l.email, e.data_envio, e.template_nome
               FROM envios e JOIN leads l ON e.lead_id = l.id
               WHERE e.tipo = 'email'
               ORDER BY e.data_envio DESC LIMIT 100''', conn)
        conn.close()

        if not hist.empty:
            hist.columns = ['Nome', 'Empresa', 'E-mail', 'Data de Envio', 'Template']
            st.dataframe(hist, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum e-mail enviado ainda.")


# ════════════════════════════════════════════════════════════════════════════
# WHATSAPP
# ════════════════════════════════════════════════════════════════════════════
elif page == "WhatsApp":
    st.markdown("""
    <div class='page-header'>
        <div class='page-title'>WhatsApp</div>
        <div class='page-subtitle'>Envio em massa personalizado ou manual — cada mensagem com o nome e empresa do lead</div>
    </div>
    """, unsafe_allow_html=True)

    config = load_config()
    all_leads = db.get_all_leads()

    if all_leads.empty:
        st.info("Nenhum lead cadastrado. Adicione leads primeiro.")
        st.stop()

    leads_com_zap = all_leads[all_leads['whatsapp'].notna() & (all_leads['whatsapp'] != '')]

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("Selecionar Template")
        templates_zap = config['templates']['whatsapp']
        template_names_zap = [t['nome'] for t in templates_zap]
        selected_zap_name = st.selectbox("Template WhatsApp", template_names_zap)
        template_zap = next(t for t in templates_zap if t['nome'] == selected_zap_name)
        mensagem = st.text_area("Mensagem", value=template_zap.get('mensagem', ''), height=180)
        st.markdown("<small>Use <code>{nome}</code> e <code>{empresa}</code> para personalizar automaticamente.</small>", unsafe_allow_html=True)

        st.markdown("---")
        uploaded_zap_file = st.file_uploader(
            "📎 Arquivo para enviar (opcional)",
            accept_multiple_files=False,
            help="O mesmo arquivo será enviado para todos os contatos selecionados. Funciona apenas no modo Automático."
        )

    # Opções dinâmicas baseadas nos leads reais (não lista fixa do config)
    status_opts_zap = sorted(leads_com_zap['status'].dropna().unique().tolist())
    seg_opts_zap = sorted([s for s in leads_com_zap['segmento'].dropna().unique().tolist() if str(s).strip()])
    if not seg_opts_zap:
        seg_opts_zap = db.get_segmento_options()

    with col_right:
        st.subheader("Configurações")
        default_status_zap = [s for s in ["Novo"] if s in status_opts_zap]
        status_fz = st.multiselect("Status dos leads", status_opts_zap, default=default_status_zap)
        seg_fz = st.multiselect("Segmento", seg_opts_zap, key="seg_zap")
        modo = st.radio("Modo de envio", ["🤖 Automático (recomendado)", "👆 Manual (um por um)"])
        wait_time = st.slider("Tempo de carregamento (seg)", 10, 30, 18,
                              help="Quanto tempo aguardar o WhatsApp Web carregar antes de enviar. Aumente se sua internet for lenta.")

    targets_zap = leads_com_zap.copy()
    if status_fz:
        targets_zap = targets_zap[targets_zap['status'].isin(status_fz)]
    if seg_fz:
        targets_zap = targets_zap[targets_zap['segmento'].isin(seg_fz)]

    st.markdown("---")
    st.markdown(f"**{len(targets_zap)} lead(s) serão contactados**")
    if not targets_zap.empty:
        st.dataframe(
            targets_zap[['nome', 'empresa', 'whatsapp', 'status']].rename(
                columns={'nome': 'Nome', 'empresa': 'Empresa',
                         'whatsapp': 'WhatsApp', 'status': 'Status'}),
            use_container_width=True, hide_index=True)

    if not mensagem.strip():
        st.warning("Preencha a mensagem do template para continuar.")
        st.stop()

    if targets_zap.empty:
        st.info("Nenhum lead encontrado com os filtros selecionados.")
        st.stop()

    # Salva o arquivo do WhatsApp em pasta temporária (se enviado)
    zap_file_path = None
    if uploaded_zap_file:
        tmp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados", "tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        zap_file_path = os.path.join(tmp_dir, uploaded_zap_file.name)
        with open(zap_file_path, 'wb') as f:
            f.write(uploaded_zap_file.getvalue())

    # ── MODO AUTOMÁTICO ──────────────────────────────────────────────────────
    if "🤖 Automático" in modo:
        if not wh.IS_MACOS:
            st.info("ℹ️ **Windows detectado:** o envio automático funciona via Chrome. Deixe o Chrome aberto e não mexa no computador durante o envio.")
        st.markdown("""
        <div class="info-banner">
        🤖 <strong>Modo Automático com personalização:</strong> cada mensagem é enviada com o nome e empresa do lead automaticamente — mesmo em listas de centenas de contatos.<br>
        O Chrome abre e fecha as abas sozinho. Não mexa no computador durante o envio.<br><br>
        ⚠️ <strong>Primeira vez no Mac:</strong> acesse <strong>Ajustes do Sistema → Privacidade → Acessibilidade</strong> e ative o Terminal.
        </div>
        """, unsafe_allow_html=True)

        total = len(targets_zap)
        tempo_estimado = total * (wait_time + (10 if zap_file_path else 5))
        minutos = tempo_estimado // 60
        segundos = tempo_estimado % 60
        label_arquivo = f" + arquivo **{uploaded_zap_file.name}**" if zap_file_path else ""
        st.info(f"⏱️ Tempo estimado: ~{minutos}min {segundos}s para {total} contato(s){label_arquivo}")

        if st.button(f"🚀 Enviar {total} mensagem(ns) automaticamente", type="primary"):
            progress = st.progress(0)
            status_box = st.empty()
            log_box = st.empty()
            resultados = []

            for i, (_, lead) in enumerate(targets_zap.iterrows()):
                nome = lead['nome']
                empresa = lead.get('empresa', '') or ''

                label = f"💬📎 **{i+1}/{total}** — **{nome}** ({empresa or '—'})" if zap_file_path else f"💬 **{i+1}/{total}** — **{nome}** ({empresa or '—'})"
                status_box.markdown(label)

                is_last = (i == total - 1)
                ok, msg_result = wh.send_whatsapp_auto(
                    lead['whatsapp'], mensagem, nome, empresa,
                    wait_time=wait_time,
                    file_path=zap_file_path,
                    close_tab=is_last
                )

                if ok:
                    db.log_envio(lead['id'], 'whatsapp', selected_zap_name)
                    db.update_lead_status(lead['id'], 'WhatsApp Enviado')
                    resultados.append(f"✅ {nome}" + (" (mensagem + arquivo)" if zap_file_path else ""))
                else:
                    resultados.append(f"❌ {nome}: {msg_result}")

                log_box.markdown("\n".join(resultados))
                progress.progress((i + 1) / total)

                if i < total - 1:
                    time.sleep(5)  # Extra delay between contacts

            status_box.empty()
            progress.empty()
            sucessos = sum(1 for r in resultados if r.startswith("✅"))
            st.success(f"✅ Concluído! {sucessos}/{total} contato(s) com mensagem enviada.")
            # Mostra detalhes para debug — não faz rerun automático
            for r in resultados:
                if r.startswith("❌"):
                    st.error(r)
                else:
                    st.success(r)

    # ── MODO MANUAL ──────────────────────────────────────────────────────────
    else:
        st.markdown("""
        <div class="info-banner">
        👆 <strong>Modo Manual com personalização:</strong> a mensagem já aparece pré-preenchida com o nome e empresa de cada lead — é só confirmar o envio no WhatsApp.<br>
        Clique em <strong>"📱 Abrir"</strong>, envie a mensagem e marque <strong>"✅ Enviado"</strong>.
        </div>
        """, unsafe_allow_html=True)
        if zap_file_path:
            st.warning(f"⚠️ O envio de arquivo **({uploaded_zap_file.name})** só funciona no modo **Automático**. No modo manual, anexe o arquivo manualmente no WhatsApp após abrir a conversa.")

        for _, lead in targets_zap.iterrows():
            nome = lead['nome']
            empresa = lead.get('empresa', '') or ''
            link = wh.get_whatsapp_web_link(lead['whatsapp'], mensagem, nome, empresa)
            if not link:
                continue

            col_info, col_btn, col_mark = st.columns([3, 1, 1])
            with col_info:
                st.markdown(f"**{nome}** — {empresa or '—'}  ·  `{lead['whatsapp']}`")
            with col_btn:
                st.link_button("📱 Abrir", link, use_container_width=True)
            with col_mark:
                if st.button("✅ Enviado", key=f"zap_sent_{lead['id']}", use_container_width=True):
                    db.log_envio(lead['id'], 'whatsapp', selected_zap_name)
                    db.update_lead_status(lead['id'], 'WhatsApp Enviado')
                    st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# RELATÓRIOS
# ════════════════════════════════════════════════════════════════════════════
elif page == "Relatórios":
    st.markdown("""
    <div class='page-header'>
        <div class='page-title'>Relatórios</div>
        <div class='page-subtitle'>Analise o desempenho da sua prospecção</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 3])
    with col1:
        dias = st.selectbox("Período", [7, 14, 30, 60, 90], format_func=lambda x: f"Últimos {x} dias")
        gerar = st.button("📥 Gerar Relatório Excel", type="primary", use_container_width=True)

    if gerar:
        with st.spinner("Gerando relatório..."):
            try:
                path = rg.generate_excel_report(dias)
                with open(path, 'rb') as f:
                    st.download_button(
                        label="⬇️ Baixar Relatório",
                        data=f,
                        file_name=os.path.basename(path),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                    )
                st.success(f"Relatório gerado: `{os.path.basename(path)}`")
            except Exception as e:
                st.error(f"Erro ao gerar relatório: {e}")

    st.markdown("---")
    st.subheader("📈 Resumo Rápido")
    data = rg.get_report_data(dias if 'dias' in locals() else 7)

    if data:
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Total de Leads", data['total_leads'])
        col_b.metric("E-mails no Período", data['emails_periodo'])
        col_c.metric("WhatsApp no Período", data['whatsapp_periodo'])

        col_d, col_e = st.columns(2)
        with col_d:
            st.subheader("Leads por Status")
            if not data['por_status'].empty:
                st.dataframe(data['por_status'].rename(columns={'status': 'Status', 'count': 'Qtd'}),
                             hide_index=True, use_container_width=True)

        with col_e:
            st.subheader("Envios Recentes")
            if not data['envios_detalhado'].empty:
                st.dataframe(
                    data['envios_detalhado'][['nome', 'tipo', 'data_envio']].rename(
                        columns={'nome': 'Nome', 'tipo': 'Tipo', 'data_envio': 'Data'}),
                    hide_index=True, use_container_width=True)
            else:
                st.info("Nenhum envio no período.")

    st.markdown("---")
    st.subheader("📁 Relatórios Anteriores")
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "relatorios")
    if os.path.exists(reports_dir):
        files = sorted(
            [f for f in os.listdir(reports_dir) if f.endswith('.xlsx')],
            reverse=True
        )
        if files:
            for fname in files[:10]:
                fpath = os.path.join(reports_dir, fname)
                with open(fpath, 'rb') as f:
                    st.download_button(
                        label=f"⬇️ {fname}",
                        data=f,
                        file_name=fname,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=fname,
                    )
        else:
            st.info("Nenhum relatório gerado ainda.")


# ════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES
# ════════════════════════════════════════════════════════════════════════════
elif page == "Configurações":
    st.markdown("""
    <div class='page-header'>
        <div class='page-title'>Configurações</div>
        <div class='page-subtitle'>Personalize e-mail, templates e filtros</div>
    </div>
    """, unsafe_allow_html=True)
    config = load_config()

    tab_email, tab_assinatura, tab_filtros, tab_templates = st.tabs(["E-mail", "🖊️ Assinatura", "🏷️ Filtros", "📝 Templates de Mensagem"])

    # ── TAB: EMAIL CONFIG ───────────────────────────────────────────────────
    with tab_email:
        st.subheader("Configurar Conta de E-mail")

        # ── Guia de configuração ──────────────────────────────────────────
        with st.expander("📖 Como configurar — clique para ver o passo a passo", expanded=False):
            st.markdown("""
**Gmail (recomendado — gratuito)**
1. Acesse [myaccount.google.com](https://myaccount.google.com) e ative a **Verificação em 2 etapas**
2. Vá em **Segurança → Senhas de app** (ou acesse [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords))
3. Crie uma senha de app → escolha "Outro" → dê o nome "AlcanceMax"
4. Copie a senha de **16 letras** gerada
5. No formulário abaixo: selecione **Gmail**, informe seu e-mail e cole a senha de app

---

**Outlook / Hotmail / Microsoft 365**
1. Certifique-se de que o SMTP está habilitado na sua conta Microsoft
2. Selecione **Outlook / Hotmail** abaixo e use sua senha normal ou senha de app

---

**Servidor próprio / Locaweb / outro provedor**
1. Selecione **Outro (personalizado)** e insira o servidor SMTP fornecido pelo seu provedor
2. A porta padrão é 587 (TLS). Use 465 para SSL se o provedor exigir.
            """)

        # ── Formulário de configuração ────────────────────────────────────
        SMTP_PROVIDERS = {
            "Gmail":                   ("smtp.gmail.com",        587),
            "Outlook / Hotmail":       ("smtp.office365.com",    587),
            "Yahoo Mail":              ("smtp.mail.yahoo.com",   587),
            "Outro (personalizado)":   ("",                      587),
        }

        current_smtp   = config['email'].get('smtp_server', '')
        current_port   = config['email'].get('smtp_port', 587)

        # Descobre qual provider está configurado (ou "Outro")
        reverse_map = {v[0]: k for k, v in SMTP_PROVIDERS.items() if v[0]}
        current_provider = reverse_map.get(current_smtp, "Outro (personalizado)")

        provider_keys = list(SMTP_PROVIDERS.keys())
        prov_idx = provider_keys.index(current_provider) if current_provider in provider_keys else 3

        with st.form("email_config_form"):
            email_remetente = st.text_input(
                "E-mail do remetente",
                value=config['email'].get('remetente', ''),
                placeholder="seuemail@gmail.com")

            email_senha = st.text_input(
                "Senha / Senha de App",
                value=config['email'].get('senha', ''),
                type="password",
                placeholder="Para Gmail: use a Senha de App de 16 letras")

            nome_exib = st.text_input(
                "Nome de exibição",
                value=config['email'].get('nome_exibicao', ''),
                placeholder="Ex: João Silva — Sua Empresa")

            st.markdown("---")
            st.markdown("**Configurações SMTP**")

            provider_sel = st.selectbox(
                "Provedor de e-mail",
                provider_keys,
                index=prov_idx)

            # Servidor personalizado (só aparece visualmente — lógica pós-submit)
            smtp_custom = ""
            port_default = SMTP_PROVIDERS[provider_sel][1]
            if provider_sel == "Outro (personalizado)":
                smtp_custom = st.text_input(
                    "Servidor SMTP",
                    value=current_smtp if current_smtp not in [v[0] for v in SMTP_PROVIDERS.values() if v[0]] else "",
                    placeholder="mail.seudominio.com.br")

            smtp_port_val = st.number_input(
                "Porta SMTP",
                min_value=1, max_value=65535,
                value=int(current_port) if current_port else port_default,
                help="587 = TLS (recomendado) · 465 = SSL · 25 = sem criptografia")

            salvar_email = st.form_submit_button("💾 Salvar Configurações", type="primary")

        if salvar_email:
            if provider_sel == "Outro (personalizado)":
                smtp_final = smtp_custom.strip()
            else:
                smtp_final = SMTP_PROVIDERS[provider_sel][0]

            if not email_remetente.strip():
                st.error("Informe o e-mail do remetente.")
            elif not smtp_final:
                st.error("Informe o servidor SMTP.")
            else:
                config['email']['remetente']    = email_remetente.strip()
                config['email']['senha']        = email_senha
                config['email']['nome_exibicao'] = nome_exib.strip()
                config['email']['smtp_server']  = smtp_final
                config['email']['smtp_port']    = int(smtp_port_val)
                save_config(config)
                st.success(f"✅ Configurações salvas! Usando {smtp_final}:{int(smtp_port_val)}")

        st.markdown("---")
        if st.button("🔌 Testar conexão de e-mail"):
            with st.spinner("Testando..."):
                ok, msg = es.test_connection()
            if ok:
                st.success(f"✅ {msg}")
            else:
                st.error(f"❌ {msg}")

    # ── TAB: TEMPLATES ──────────────────────────────────────────────────────
    # ── TAB: ASSINATURA ─────────────────────────────────────────────────────
    with tab_assinatura:
        st.subheader("Assinatura de E-mail")
        st.markdown("""
        <div class="info-banner">
        Faça upload da imagem da sua assinatura. Ela será inserida automaticamente no rodapé de todos os e-mails enviados.
        </div>
        """, unsafe_allow_html=True)

        sig_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados")
        os.makedirs(sig_dir, exist_ok=True)
        current_sig = config['email'].get('assinatura_imagem', '')

        if current_sig and os.path.exists(current_sig):
            st.markdown("**Assinatura atual:**")
            st.image(current_sig, width=500)
            if st.button("🗑️ Remover Assinatura", type="secondary"):
                config['email']['assinatura_imagem'] = ''
                save_config(config)
                st.success("Assinatura removida.")
                st.rerun()
        else:
            st.info("Nenhuma assinatura configurada.")

        st.markdown("---")
        uploaded_sig = st.file_uploader(
            "Upload da assinatura (PNG, JPG)",
            type=["png", "jpg", "jpeg"],
            help="Recomendado: PNG com fundo transparente, largura entre 400-600px"
        )
        if uploaded_sig:
            ext = uploaded_sig.name.split('.')[-1].lower()
            sig_path = os.path.join(sig_dir, f"assinatura.{ext}")
            with open(sig_path, 'wb') as f:
                f.write(uploaded_sig.read())
            config['email']['assinatura_imagem'] = sig_path
            save_config(config)
            st.success("Assinatura salva com sucesso!")
            st.image(sig_path, width=500)
            st.rerun()

    # ── TAB: FILTROS ─────────────────────────────────────────────────────────
    with tab_filtros:
        st.subheader("Gerenciar Filtros de Leads")
        st.markdown("Personalize as opções que aparecem nos filtros e nos campos de cadastro de leads.")

        filtros_cfg = config.get('filtros', {})
        col_st, col_seg = st.columns(2)

        # ── STATUS ──
        with col_st:
            st.markdown("#### Status de Lead")
            status_list = filtros_cfg.get('status', db.get_status_options())

            for i, item in enumerate(status_list):
                c1, c2 = st.columns([4, 1])
                c1.text_input("", value=item, key=f"st_item_{i}", label_visibility="collapsed",
                              on_change=None)
                if c2.button("✕", key=f"st_del_{i}", help="Remover"):
                    status_list.pop(i)
                    config['filtros']['status'] = status_list
                    save_config(config)
                    st.rerun()

            with st.form("add_status_form"):
                novo_status = st.text_input("Novo status", placeholder="Ex: Em Negociação")
                if st.form_submit_button("➕ Adicionar", type="primary"):
                    if novo_status.strip() and novo_status.strip() not in status_list:
                        status_list.append(novo_status.strip())
                        if 'filtros' not in config:
                            config['filtros'] = {}
                        config['filtros']['status'] = status_list
                        save_config(config)
                        st.success(f"Status **{novo_status}** adicionado!")
                        st.rerun()

            # Save edits
            if st.button("💾 Salvar alterações de Status", key="save_status"):
                new_vals = [st.session_state.get(f"st_item_{i}", v)
                            for i, v in enumerate(status_list)]
                new_vals = [v.strip() for v in new_vals if v.strip()]
                config['filtros']['status'] = new_vals
                save_config(config)
                st.success("Status salvos!")
                st.rerun()

        # ── SEGMENTOS ──
        with col_seg:
            st.markdown("#### Segmentos")
            seg_list = filtros_cfg.get('segmentos', db.get_segmento_options())

            for i, item in enumerate(seg_list):
                c1, c2 = st.columns([4, 1])
                c1.text_input("", value=item, key=f"seg_item_{i}", label_visibility="collapsed")
                if c2.button("✕", key=f"seg_del_{i}", help="Remover"):
                    seg_list.pop(i)
                    config['filtros']['segmentos'] = seg_list
                    save_config(config)
                    st.rerun()

            with st.form("add_seg_form"):
                novo_seg = st.text_input("Novo segmento", placeholder="Ex: Revendedor")
                if st.form_submit_button("➕ Adicionar", type="primary"):
                    if novo_seg.strip() and novo_seg.strip() not in seg_list:
                        seg_list.append(novo_seg.strip())
                        if 'filtros' not in config:
                            config['filtros'] = {}
                        config['filtros']['segmentos'] = seg_list
                        save_config(config)
                        st.success(f"Segmento **{novo_seg}** adicionado!")
                        st.rerun()

            if st.button("💾 Salvar alterações de Segmento", key="save_seg"):
                new_vals = [st.session_state.get(f"seg_item_{i}", v)
                            for i, v in enumerate(seg_list)]
                new_vals = [v.strip() for v in new_vals if v.strip()]
                config['filtros']['segmentos'] = new_vals
                save_config(config)
                st.success("Segmentos salvos!")
                st.rerun()

    with tab_templates:
        st.subheader("Templates de E-mail")
        st.markdown("<small>Use <code>{nome}</code> e <code>{empresa}</code> para personalizar.</small>", unsafe_allow_html=True)

        email_templates = config['templates']['email']
        for i, tmpl in enumerate(email_templates):
            with st.expander(f"📧 {tmpl['nome']}", expanded=i == 0):
                with st.form(f"email_tmpl_{i}"):
                    t_nome = st.text_input("Nome do Template", value=tmpl['nome'], key=f"en_{i}")
                    t_assunto = st.text_input("Assunto", value=tmpl.get('assunto', ''), key=f"ea_{i}")
                    t_corpo = st.text_area("Corpo", value=tmpl.get('corpo', ''), height=200, key=f"ec_{i}")
                    c1, c2 = st.columns(2)
                    save_t = c1.form_submit_button("💾 Salvar", type="primary")
                    del_t = c2.form_submit_button("🗑️ Excluir", type="secondary")

                if save_t:
                    config['templates']['email'][i] = {'nome': t_nome, 'assunto': t_assunto, 'corpo': t_corpo}
                    save_config(config)
                    st.success("Template salvo!")
                    st.rerun()
                if del_t and len(email_templates) > 1:
                    config['templates']['email'].pop(i)
                    save_config(config)
                    st.rerun()

        if st.button("➕ Novo Template de E-mail"):
            config['templates']['email'].append({'nome': 'Novo Template', 'assunto': '', 'corpo': ''})
            save_config(config)
            st.rerun()

        st.markdown("---")
        st.subheader("Templates de WhatsApp")

        zap_templates = config['templates']['whatsapp']
        for i, tmpl in enumerate(zap_templates):
            with st.expander(f"💬 {tmpl['nome']}", expanded=i == 0):
                with st.form(f"zap_tmpl_{i}"):
                    zt_nome = st.text_input("Nome do Template", value=tmpl['nome'], key=f"zn_{i}")
                    zt_msg = st.text_area("Mensagem", value=tmpl.get('mensagem', ''), height=180, key=f"zm_{i}")
                    zc1, zc2 = st.columns(2)
                    zsave = zc1.form_submit_button("💾 Salvar", type="primary")
                    zdel = zc2.form_submit_button("🗑️ Excluir", type="secondary")

                if zsave:
                    config['templates']['whatsapp'][i] = {'nome': zt_nome, 'mensagem': zt_msg}
                    save_config(config)
                    st.success("Template salvo!")
                    st.rerun()
                if zdel and len(zap_templates) > 1:
                    config['templates']['whatsapp'].pop(i)
                    save_config(config)
                    st.rerun()

        if st.button("➕ Novo Template de WhatsApp"):
            config['templates']['whatsapp'].append({'nome': 'Novo Template', 'mensagem': ''})
            save_config(config)
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# MINHA AGÊNCIA — Painel do Gestor
# ════════════════════════════════════════════════════════════════════════════
elif page == "Minha Agência":
    if not _is_agency_admin():
        st.error("Acesso restrito ao gestor da agência.")
        st.stop()

    agency_id  = st.session_state.get("agency_id")
    max_users  = st.session_state.get("max_users", 5)
    users, err = lic.agency_list_users(agency_id)
    total_ativos = len([u for u in users if u.get("active")])

    st.markdown("""
    <div class='page-header'>
        <div class='page-title'>Minha Agência</div>
        <div class='page-subtitle'>Gerencie os usuários da sua equipe</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Métricas rápidas ──────────────────────────────────────────────────
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{total_ativos}</div>
            <div class="metric-label">Usuários ativos</div></div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{max_users}</div>
            <div class="metric-label">Vagas no plano</div></div>""", unsafe_allow_html=True)
    with m3:
        vagas = max(0, max_users - total_ativos)
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{vagas}</div>
            <div class="metric-label">Vagas disponíveis</div></div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Adicionar novo usuário ────────────────────────────────────────────
    with st.expander("➕ Adicionar Novo Usuário", expanded=total_ativos == 0):
        if total_ativos >= max_users:
            st.warning(f"⚠️ Limite atingido ({max_users} usuários). Entre em contato para ampliar o plano.")
        else:
            with st.form("form_agency_user"):
                c1, c2 = st.columns(2)
                nu_nome  = c1.text_input("Nome completo", placeholder="João Silva")
                nu_email = c2.text_input("E-mail", placeholder="joao@empresa.com")
                criar_u  = st.form_submit_button("🔑 Criar usuário e gerar chave", type="primary")

            if criar_u:
                if not nu_nome or not nu_email:
                    st.error("Preencha nome e e-mail.")
                else:
                    key_u, erro_u = lic.agency_create_user(nu_nome, nu_email, agency_id)
                    if erro_u:
                        st.error(f"Erro: {erro_u}")
                    else:
                        st.success(f"✅ Usuário **{nu_nome}** criado!")
                        st.markdown("**Envie estas informações para o usuário:**")
                        st.info(f"""
📧 **E-mail:** {nu_email}
🔑 **Chave de licença:** `{key_u}`

🔗 **Link para instalar:** https://allan180903-pixel.github.io/alcancemax/
                        """)
                        st.rerun()

    st.markdown("---")

    # ── Lista de usuários ─────────────────────────────────────────────────
    st.subheader("👥 Usuários da Agência")

    if err:
        st.error(f"Erro: {err}")
    elif not users:
        st.info("Nenhum usuário cadastrado ainda. Adicione o primeiro usuário acima.")
    else:
        for row in users:
            lid    = row.get("id", "")
            nome   = row.get("nome") or "—"
            email  = row.get("email", "")
            lkey   = row.get("license_key", "")
            active = row.get("active", False)
            criado = row.get("created_at", "")[:10] if row.get("created_at") else "—"
            status_icon = "🟢" if active else "🔴"

            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
                col1.markdown(f"**{nome}**  \n✉️ {email}")
                col2.markdown(f"`{lkey}`  \n📅 Desde {criado}")
                col3.markdown(f"{status_icon} {'Ativo' if active else 'Inativo'}")

                with col4:
                    if active:
                        if st.button("⏸ Suspender", key=f"ag_off_{lid}"):
                            ok, e = lic.agency_toggle_user(lid, False)
                            if ok: st.rerun()
                            else: st.error(e)
                    else:
                        if st.button("▶️ Reativar", key=f"ag_on_{lid}"):
                            ok, e = lic.agency_toggle_user(lid, True)
                            if ok: st.rerun()
                            else: st.error(e)
                    if st.button("🗑️ Remover", key=f"ag_del_{lid}"):
                        ok, e = lic.agency_delete_user(lid)
                        if ok: st.rerun()
                        else: st.error(e)


# ════════════════════════════════════════════════════════════════════════════
# ADMIN — Gerenciamento de Licenças (Super Admin)
# ════════════════════════════════════════════════════════════════════════════
elif page == "Admin":
    if not _is_super_admin():
        st.error("⛔ Acesso restrito ao administrador do sistema.")
        st.stop()

    st.markdown("""
    <div class='page-header'>
        <div class='page-title'>Admin</div>
        <div class='page-subtitle'>Gerenciamento de licenças e usuários</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Nova Licença ──────────────────────────────────────────────────────
    with st.expander("➕ Criar Nova Licença", expanded=False):
        with st.form("form_new_license"):
            c1, c2 = st.columns(2)
            novo_nome  = c1.text_input("Nome do cliente")
            novo_email = c2.text_input("E-mail")
            c3, c4    = st.columns(2)
            novo_plano = c3.selectbox("Plano", ["starter", "pro", "agencia"])
            novo_exp   = c4.date_input("Vencimento (opcional)", value=None)

            # Campos extras para Agência
            novo_role     = "user"
            novo_max_users = 1
            if novo_plano == "agencia":
                st.markdown("---")
                st.markdown("**⚙️ Configurações da Agência**")
                rc1, rc2 = st.columns(2)
                novo_role_sel  = rc1.selectbox("Tipo de acesso", ["Gestor (Agency Admin)", "Usuário comum"])
                novo_max_users = rc2.number_input("Máximo de usuários", min_value=1, max_value=100, value=5)
                novo_role = lic.ROLE_AGENCY_ADMIN if "Gestor" in novo_role_sel else lic.ROLE_USER

            criar = st.form_submit_button("🔑 Gerar Licença", type="primary")

        if criar:
            if not novo_nome or not novo_email:
                st.error("Preencha nome e e-mail.")
            else:
                from datetime import datetime as _dt
                exp = _dt.combine(novo_exp, _dt.min.time()) if novo_exp else None
                key_gerada, erro = lic.admin_create_license(
                    novo_nome, novo_email, novo_plano, exp,
                    role=novo_role, max_users=int(novo_max_users)
                )
                if erro:
                    st.error(f"Erro: {erro}")
                else:
                    tipo = "Gestor de Agência" if novo_role == lic.ROLE_AGENCY_ADMIN else "Usuário"
                    st.success(f"✅ Licença {tipo} criada!")
                    st.code(key_gerada, language=None)
                    st.info(f"Envie para **{novo_email}**: chave `{key_gerada}`")
                    if novo_role == lic.ROLE_AGENCY_ADMIN:
                        st.markdown(f"🏢 Este gestor poderá criar até **{int(novo_max_users)} usuários** na equipe dele.")
                    st.rerun()

    st.markdown("---")

    # ── Lista de Licenças ─────────────────────────────────────────────────
    st.subheader("📋 Todas as Licenças")
    licenses, erro = lic.admin_list_licenses()

    if erro:
        st.error(f"Erro ao carregar licenças: {erro}")
    elif not licenses:
        st.info("Nenhuma licença cadastrada.")
    else:
        # Separa: licenças principais (super_admin, agency_admin, users individuais)
        # Usuários de agência (role=user com agency_id) ficam dentro do card do gestor
        agency_users_map = {}   # agency_id → [users]
        main_licenses   = []

        for row in licenses:
            role      = row.get("role", lic.ROLE_USER)
            agency_id = row.get("agency_id")
            if role == lic.ROLE_USER and agency_id:
                agency_users_map.setdefault(agency_id, []).append(row)
            else:
                main_licenses.append(row)

        role_order = {lic.ROLE_SUPER_ADMIN: 0, lic.ROLE_AGENCY_ADMIN: 1, lic.ROLE_USER: 2}
        main_licenses.sort(key=lambda r: (role_order.get(r.get("role", "user"), 2),
                                          r.get("created_at", "")))

        for row in main_licenses:
            lid       = row.get("id", "")
            nome      = row.get("nome") or "—"
            email     = row.get("email", "")
            lkey      = row.get("license_key", "")
            plan      = row.get("plan", "starter")
            active    = row.get("active", False)
            role      = row.get("role", lic.ROLE_USER)
            exp       = row.get("expires_at")
            max_u     = row.get("max_users", 1)
            agency_id = row.get("agency_id")
            exp_str    = exp[:10] if exp else "Sem vencimento"
            plan_label = lic.PLANS.get(plan, {}).get("nome", plan)

            role_labels = {lic.ROLE_SUPER_ADMIN: "⚡ Super Admin",
                           lic.ROLE_AGENCY_ADMIN: "🏢 Gestor",
                           lic.ROLE_USER:         "👤 Usuário"}
            role_label  = role_labels.get(role, role)
            status_icon = "🟢" if active else "🔴"

            # Usuários desta agência (se for gestor)
            sub_users = agency_users_map.get(agency_id, []) if role == lic.ROLE_AGENCY_ADMIN else []
            ativos    = len([u for u in sub_users if u.get("active")])

            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
                col1.markdown(f"**{nome}** {role_label}  \n✉️ {email}")

                info_extra = ""
                if role == lic.ROLE_AGENCY_ADMIN:
                    info_extra = f" · 👥 {ativos}/{max_u} usuários"
                col2.markdown(f"`{lkey}`  \n📦 {plan_label} · 📅 {exp_str}{info_extra}")
                col3.markdown(f"{status_icon} {'Ativa' if active else 'Inativa'}")

                with col4:
                    if active:
                        if st.button("⏸ Desativar", key=f"off_{lid}"):
                            ok, err = lic.admin_toggle_license(lid, False)
                            if ok: st.rerun()
                            else: st.error(err)
                    else:
                        if st.button("▶️ Ativar", key=f"on_{lid}"):
                            ok, err = lic.admin_toggle_license(lid, True)
                            if ok: st.rerun()
                            else: st.error(err)
                    if st.button("🗑️ Deletar", key=f"del_{lid}"):
                        ok, err = lic.admin_delete_license(lid)
                        if ok: st.rerun()
                        else: st.error(err)

                # ── Expander com usuários da agência ─────────────────────
                if role == lic.ROLE_AGENCY_ADMIN:
                    label_exp = (f"👥 Ver equipe ({ativos} ativo{'s' if ativos != 1 else ''})"
                                 if sub_users else "👥 Nenhum usuário ainda")
                    with st.expander(label_exp):
                        if not sub_users:
                            st.caption("O gestor ainda não criou nenhum usuário.")
                        else:
                            for u in sub_users:
                                uid     = u.get("id", "")
                                u_nome  = u.get("nome") or "—"
                                u_email = u.get("email", "")
                                u_key   = u.get("license_key", "")
                                u_active = u.get("active", False)
                                u_icon   = "🟢" if u_active else "🔴"
                                uc1, uc2, uc3 = st.columns([4, 4, 2])
                                uc1.markdown(f"**{u_nome}**  \n✉️ {u_email}")
                                uc2.markdown(f"`{u_key}`")
                                with uc3:
                                    st.markdown(f"{u_icon} {'Ativo' if u_active else 'Inativo'}")
                                    if u_active:
                                        if st.button("⏸", key=f"su_off_{uid}", help="Suspender"):
                                            ok, e = lic.admin_toggle_license(uid, False)
                                            if ok: st.rerun()
                                    else:
                                        if st.button("▶️", key=f"su_on_{uid}", help="Reativar"):
                                            ok, e = lic.admin_toggle_license(uid, True)
                                            if ok: st.rerun()
                                st.divider()
