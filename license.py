"""
AlcanceMax — Sistema de licenciamento via Supabase.
Valida email + chave de licença contra a tabela 'licenses' no Supabase.
"""
import os
import json
import hashlib
import requests
from datetime import datetime

# ── Configuração Supabase (preenchida após criar o projeto) ──────────────────
SUPABASE_URL = "https://vekqadqraqxorzcdkrrg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZla3FhZHFyYXF4b3J6Y2RrcnJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkxOTcyMjUsImV4cCI6MjA5NDc3MzIyNX0.t6GBlmCV8cB6h1Mgeg7lY69iCj7SelFzBwtk-aGNVA8"

LOCAL_SESSION_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".session")

PLANS = {
    "starter":    {"nome": "Starter",    "leads_max": 200},
    "pro":        {"nome": "Pro",        "leads_max": None},
    "agencia":    {"nome": "Agência",    "leads_max": None},
    "dev":        {"nome": "Dev/Teste",  "leads_max": None},
}

# E-mail do administrador do sistema
ADMIN_EMAIL = "allan@formmacomponentes.com.br"


# ── Sessão local (evita pedir login a cada abertura) ─────────────────────────

def _save_session(email: str, license_key: str, plan: str):
    data = {"email": email, "key": license_key, "plan": plan,
            "saved_at": datetime.utcnow().isoformat()}
    with open(LOCAL_SESSION_PATH, "w") as f:
        json.dump(data, f)


def _load_session():
    if not os.path.exists(LOCAL_SESSION_PATH):
        return None
    try:
        with open(LOCAL_SESSION_PATH) as f:
            return json.load(f)
    except Exception:
        return None


def clear_session():
    if os.path.exists(LOCAL_SESSION_PATH):
        os.remove(LOCAL_SESSION_PATH)


# ── Validação contra Supabase ─────────────────────────────────────────────────

def validate_license(email: str, license_key: str) -> dict:
    """
    Retorna dict com:
      valid   bool
      plan    str  (starter / pro / agencia / dev)
      message str  (mensagem para o usuário)
    """
    email = email.strip().lower()
    license_key = license_key.strip().upper()

    if not SUPABASE_URL or not SUPABASE_KEY:
        # Modo desenvolvimento — sem Supabase configurado
        return {"valid": True, "plan": "dev", "email": email,
                "message": "Modo desenvolvimento (Supabase não configurado)."}

    try:
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
        }
        params = {
            "email": f"eq.{email}",
            "license_key": f"eq.{license_key}",
            "select": "email,license_key,plan,active,expires_at",
            "limit": "1",
        }
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/licenses",
            headers=headers, params=params, timeout=8
        )

        if resp.status_code != 200:
            return {"valid": False, "plan": None,
                    "message": "Erro ao conectar com o servidor de licenças. Verifique sua internet."}

        data = resp.json()
        if not data:
            return {"valid": False, "plan": None,
                    "message": "Email ou chave de licença inválidos."}

        row = data[0]

        if not row.get("active", False):
            return {"valid": False, "plan": None,
                    "message": "Licença inativa. Entre em contato com o suporte."}

        # Verifica vencimento (se definido)
        expires = row.get("expires_at")
        if expires:
            exp_date = datetime.fromisoformat(expires.replace("Z", "+00:00"))
            if exp_date < datetime.now(exp_date.tzinfo):
                return {"valid": False, "plan": None,
                        "message": "Licença vencida. Renove em alcancemax.com.br"}

        plan = row.get("plan", "starter")
        return {"valid": True, "plan": plan, "email": email,
                "message": f"Bem-vindo! Plano {PLANS.get(plan, {}).get('nome', plan)} ativo."}

    except requests.exceptions.ConnectionError:
        # Sem internet — tenta usar sessão local em cache
        session = _load_session()
        if session and session.get("email") == email:
            return {"valid": True, "plan": session["plan"], "email": email,
                    "message": "Modo offline — usando sessão local."}
        return {"valid": False, "plan": None,
                "message": "Sem conexão com a internet e nenhuma sessão local encontrada."}

    except Exception as e:
        return {"valid": False, "plan": None,
                "message": f"Erro inesperado: {str(e)}"}


def get_plan_limit(plan: str):
    """Retorna limite de leads do plano (None = ilimitado)."""
    return PLANS.get(plan, {}).get("leads_max")


# ── Funções Admin ─────────────────────────────────────────────────────────────

def _headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def generate_license_key():
    """Gera uma chave no formato XXXX-XXXX-XXXX-XXXX."""
    import random, string
    chars = string.ascii_uppercase + string.digits
    parts = [''.join(random.choices(chars, k=4)) for _ in range(4)]
    return '-'.join(parts)


def admin_list_licenses():
    """Retorna lista de todas as licenças."""
    try:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/licenses",
            headers=_headers(),
            params={"select": "*", "order": "created_at.desc"},
            timeout=8
        )
        if resp.status_code == 200:
            return resp.json(), None
        return [], f"Erro {resp.status_code}: {resp.text}"
    except Exception as e:
        return [], str(e)


def admin_create_license(nome, email, plan, expires_at=None):
    """Cria nova licença. Retorna (license_key, erro)."""
    key = generate_license_key()
    payload = {
        "nome": nome.strip(),
        "email": email.strip().lower(),
        "license_key": key,
        "plan": plan,
        "active": True,
    }
    if expires_at:
        payload["expires_at"] = expires_at.isoformat()
    try:
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/licenses",
            headers=_headers(),
            json=payload,
            timeout=8
        )
        if resp.status_code in (200, 201):
            return key, None
        return None, f"Erro {resp.status_code}: {resp.text}"
    except Exception as e:
        return None, str(e)


def admin_toggle_license(license_id, active):
    """Ativa ou desativa uma licença."""
    try:
        resp = requests.patch(
            f"{SUPABASE_URL}/rest/v1/licenses",
            headers=_headers(),
            params={"id": f"eq.{license_id}"},
            json={"active": active},
            timeout=8
        )
        if resp.status_code in (200, 204):
            return True, None
        return False, f"Erro {resp.status_code}: {resp.text}"
    except Exception as e:
        return False, str(e)


def admin_delete_license(license_id):
    """Deleta uma licença."""
    try:
        resp = requests.delete(
            f"{SUPABASE_URL}/rest/v1/licenses",
            headers=_headers(),
            params={"id": f"eq.{license_id}"},
            timeout=8
        )
        if resp.status_code in (200, 204):
            return True, None
        return False, f"Erro {resp.status_code}: {resp.text}"
    except Exception as e:
        return False, str(e)
