import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime

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

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #1B3A5C; }
    [data-testid="stSidebar"] * { color: white !important; }
    [data-testid="stSidebar"] .stRadio label { font-size: 15px; }
    [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.2); }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        text-align: center;
        border-top: 4px solid #1B3A5C;
    }
    .metric-value { font-size: 2.5rem; font-weight: 700; color: #1B3A5C; }
    .metric-label { font-size: 0.85rem; color: #888; margin-top: 4px; }
    .stButton button { border-radius: 6px; }
    div[data-testid="stForm"] { background: #f8f9fa; padding: 20px; border-radius: 10px; }
    .success-banner {
        background: #d4edda; color: #155724; padding: 12px 16px;
        border-radius: 8px; border-left: 4px solid #28a745; margin: 8px 0;
    }
    .warning-banner {
        background: #fff3cd; color: #856404; padding: 12px 16px;
        border-radius: 8px; border-left: 4px solid #ffc107; margin: 8px 0;
    }
    .info-banner {
        background: #d1ecf1; color: #0c5460; padding: 12px 16px;
        border-radius: 8px; border-left: 4px solid #17a2b8; margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)


# ── LOGIN SCREEN ─────────────────────────────────────────────────────────────

def _show_login():
    """Tela de login/ativação de licença."""
    st.markdown("""
    <style>
        .login-box {
            max-width: 440px; margin: 60px auto; padding: 40px;
            background: white; border-radius: 16px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.10);
            border-top: 5px solid #1B3A5C;
        }
        .login-title { font-size: 2rem; font-weight: 800; color: #1B3A5C; text-align: center; margin-bottom: 4px; }
        .login-sub   { text-align: center; color: #888; margin-bottom: 28px; font-size: 0.95rem; }
        .login-footer{ text-align: center; color: #aaa; font-size: 0.8rem; margin-top: 20px; }
    </style>
    <div class="login-box">
        <div class="login-title">🚀 AlcanceMax</div>
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
                        lic._save_session(email, key, result["plan"])
                        st.session_state["authenticated"] = True
                        st.session_state["user_email"]    = email
                        st.session_state["user_plan"]     = result["plan"]
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
    # Tenta restaurar sessão salva em disco
    session = lic._load_session()
    if session:
        st.session_state["authenticated"] = True
        st.session_state["user_email"]    = session.get("email", "")
        st.session_state["user_plan"]     = session.get("plan", "starter")
        return True
    return False


# Bloqueia o app se não autenticado
if not _check_auth():
    _show_login()
    st.stop()


# ── HELPERS ──────────────────────────────────────────────────────────────────
def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def banner(text, kind="success"):
    css_class = f"{kind}-banner"
    st.markdown(f'<div class="{css_class}">{text}</div>', unsafe_allow_html=True)


# ── INIT ─────────────────────────────────────────────────────────────────────
db.init_db()

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚀 AlcanceMax")
    st.markdown("**Prospecção Inteligente**")
    st.divider()
    _nav_pages = ["🏠 Dashboard", "👥 Leads", "📧 E-mail", "💬 WhatsApp", "📊 Relatórios", "⚙️ Configurações"]
    if st.session_state.get("user_email", "") == lic.ADMIN_EMAIL:
        _nav_pages.append("🔑 Admin")
    page = st.radio("Navegação", _nav_pages, label_visibility="collapsed")
    st.divider()
    _email_display = st.session_state.get("user_email", "")
    _plan_display  = lic.PLANS.get(st.session_state.get("user_plan",""), {}).get("nome", "")
    st.markdown(f"<small style='color:rgba(255,255,255,0.6)'>👤 {_email_display}</small>", unsafe_allow_html=True)
    st.markdown(f"<small style='color:rgba(255,255,255,0.45)'>📦 Plano {_plan_display}</small>", unsafe_allow_html=True)
    if st.button("🚪 Sair", use_container_width=True):
        lic.clear_session()
        st.session_state.clear()
        st.rerun()
    st.markdown(f"<small style='color:rgba(255,255,255,0.35)'>AlcanceMax v1.0 · {datetime.now().strftime('%d/%m/%Y')}</small>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════════════════════
if page == "🏠 Dashboard":
    st.title("Dashboard")
    stats = db.get_stats()

    col1, col2, col3, col4, col5 = st.columns(5)
    metrics = [
        (col1, "Total de Leads", stats['total_leads'], ""),
        (col2, "E-mails (7 dias)", stats['emails_semana'], ""),
        (col3, "WhatsApp (7 dias)", stats['whatsapp_semana'], ""),
        (col4, "E-mails (total)", stats['total_emails'], ""),
        (col5, "WhatsApp (total)", stats['total_whatsapp'], ""),
    ]
    for col, label, val, _ in metrics:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{val}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📊 Leads por Status")
        if not stats['por_status'].empty:
            df_status = stats['por_status'].set_index('status')
            st.bar_chart(df_status['count'])
        else:
            st.info("Nenhum lead cadastrado ainda.")

    with col_right:
        st.subheader("🏷️ Leads por Segmento")
        if not stats['leads_por_segmento'].empty:
            df_seg = stats['leads_por_segmento'].set_index('segmento')
            st.bar_chart(df_seg['count'])
        else:
            st.info("Sem dados de segmento ainda.")

    st.markdown("---")
    st.subheader("📅 Atividade dos Últimos 30 Dias")
    if not stats['atividade_diaria'].empty:
        df_act = stats['atividade_diaria'].pivot(index='data', columns='tipo', values='total').fillna(0)
        st.bar_chart(df_act)
    else:
        st.info("Nenhum envio registrado ainda.")

    st.markdown("---")
    st.subheader("👥 Leads Recentes")
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
elif page == "👥 Leads":
    st.title("Gestão de Leads")
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
elif page == "📧 E-mail":
    st.title("Envio de E-mails")
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
        conn = sqlite3.connect(db.DB_PATH)
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
elif page == "💬 WhatsApp":
    st.title("Envio de WhatsApp")

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
        st.markdown("""
        <div class="info-banner">
        <strong>Modo Automático:</strong> O app abre o WhatsApp Web para cada contato e envia sozinho.
        Não mexa no computador durante o envio. O Chrome vai abrir e fechar as abas automaticamente.<br><br>
        ⚠️ <strong>Primeira vez:</strong> o macOS pode pedir permissão de Acessibilidade para o Terminal.
        Acesse <strong>Ajustes do Sistema → Privacidade → Acessibilidade</strong> e ative o Terminal.
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
            st.rerun()

    # ── MODO MANUAL ──────────────────────────────────────────────────────────
    else:
        st.markdown("""
        <div class="info-banner">
        Clique em <strong>"Abrir no WhatsApp"</strong>, envie a mensagem e depois clique <strong>"✅ Enviado"</strong>.
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
elif page == "📊 Relatórios":
    st.title("Relatórios de Produtividade")

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
elif page == "⚙️ Configurações":
    st.title("Configurações")
    config = load_config()

    tab_email, tab_assinatura, tab_filtros, tab_templates = st.tabs(["📧 E-mail", "🖊️ Assinatura", "🏷️ Filtros", "📝 Templates de Mensagem"])

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
# ADMIN — Gerenciamento de Licenças
# ════════════════════════════════════════════════════════════════════════════
elif page == "🔑 Admin":
    if st.session_state.get("user_email") != lic.ADMIN_EMAIL:
        st.error("Acesso restrito.")
        st.stop()

    st.title("🔑 Gerenciamento de Licenças")

    # ── Nova Licença ──────────────────────────────────────────────────────
    with st.expander("➕ Criar Nova Licença", expanded=False):
        with st.form("form_new_license"):
            c1, c2 = st.columns(2)
            novo_nome  = c1.text_input("Nome do cliente")
            novo_email = c2.text_input("E-mail")
            c3, c4 = st.columns(2)
            novo_plano = c3.selectbox("Plano", ["starter", "pro", "agencia"])
            novo_exp   = c4.date_input("Vencimento (opcional)", value=None)
            criar = st.form_submit_button("🔑 Gerar Licença", type="primary")

        if criar:
            if not novo_nome or not novo_email:
                st.error("Preencha nome e e-mail.")
            else:
                from datetime import datetime as _dt
                exp = _dt.combine(novo_exp, _dt.min.time()) if novo_exp else None
                key_gerada, erro = lic.admin_create_license(novo_nome, novo_email, novo_plano, exp)
                if erro:
                    st.error(f"Erro: {erro}")
                else:
                    st.success(f"✅ Licença criada com sucesso!")
                    st.code(key_gerada, language=None)
                    st.info(f"Envie para **{novo_email}**: chave `{key_gerada}`")
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
        for row in licenses:
            lid    = row.get("id", "")
            nome   = row.get("nome") or "—"
            email  = row.get("email", "")
            lkey   = row.get("license_key", "")
            plan   = row.get("plan", "starter")
            active = row.get("active", False)
            exp    = row.get("expires_at")
            exp_str = exp[:10] if exp else "Sem vencimento"
            plan_label = lic.PLANS.get(plan, {}).get("nome", plan)

            status_icon = "🟢" if active else "🔴"

            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
                col1.markdown(f"**{nome}**  \n{email}")
                col2.markdown(f"`{lkey}`  \n📦 {plan_label} · 📅 {exp_str}")
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
