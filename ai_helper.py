"""
IA de criação de mensagens para o AlcanceMax.
Gera e-mails e mensagens de WhatsApp de alto nível a partir de uma descrição
simples do produto/oferta, seguindo o padrão da ferramenta (tópicos com •,
personalização com {nome}, comunicação profissional).

Usa a API da Anthropic (Claude). A chave fica em config['ia']['api_key']
ou na variável de ambiente ANTHROPIC_API_KEY.
"""
import os
import json

MODELO = "claude-opus-4-8"


def _get_api_key(config=None):
    if config:
        chave = (config.get('ia', {}) or {}).get('api_key', '')
        if chave and chave.strip():
            return chave.strip()
    return os.environ.get("ANTHROPIC_API_KEY", "").strip()


def ia_disponivel(config=None):
    """Retorna True se há uma chave de API configurada."""
    return bool(_get_api_key(config))


def _client(config=None):
    import anthropic
    chave = _get_api_key(config)
    if not chave:
        raise ValueError("Chave da API de IA não configurada. Configure em Configurações → IA.")
    return anthropic.Anthropic(api_key=chave)


_INSTRUCOES_COMUNS = """Você é um redator publicitário sênior especializado em prospecção B2B \
para a indústria moveleira e de componentes. Escreve em português do Brasil, com tom \
profissional, consultivo e de alto nível — nunca apelativo ou "vendedor de spam".

Regras de formatação obrigatórias:
- Sempre use {nome} para personalizar (o sistema substitui pelo nome do cliente).
- Para listas de produtos/benefícios, use tópicos começando com "• " (bullet).
- Quando um tópico tiver nome + descrição, coloque o nome na primeira linha e a \
descrição na linha seguinte (o sistema deixa o nome em negrito automaticamente).
- Separe parágrafos com uma linha em branco.
- Seja claro, direto e elegante. Evite jargão de marketing raso e superlativos vazios.
- Feche sempre colocando-se à disposição para amostras, informações ou reunião."""


def gerar_email(descricao, empresa_remetente="Iddea Componentes",
                nome_remetente="Allan Tonini", contato="", config=None):
    """Gera assunto + corpo de e-mail a partir da descrição do produto/oferta.
    Retorna (assunto, corpo)."""
    client = _client(config)

    assinatura = f"{nome_remetente}\n{empresa_remetente}"
    if contato:
        assinatura += f"\n{contato}"

    prompt = f"""{_INSTRUCOES_COMUNS}

Crie um E-MAIL de prospecção com base nesta descrição do que deve ser comunicado:

\"\"\"{descricao}\"\"\"

O e-mail deve:
- Ter uma saudação personalizada com {{nome}}.
- Ser conciso (cabe na tela, sem rolar demais).
- Terminar com a assinatura:
{assinatura}

Responda em JSON com exatamente estas chaves:
{{"assunto": "linha de assunto curta e atraente (use {{nome}} se fizer sentido)", "corpo": "corpo completo do e-mail"}}"""

    resp = client.messages.create(
        model=MODELO,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "assunto": {"type": "string"},
                        "corpo": {"type": "string"},
                    },
                    "required": ["assunto", "corpo"],
                    "additionalProperties": False,
                },
            }
        },
    )
    texto = next(b.text for b in resp.content if b.type == "text")
    dados = json.loads(texto)
    return dados["assunto"], dados["corpo"]


def gerar_whatsapp(descricao, empresa_remetente="Iddea Componentes",
                   nome_remetente="Allan Tonini", config=None):
    """Gera a mensagem de WhatsApp a partir da descrição. Retorna a mensagem (str)."""
    client = _client(config)

    prompt = f"""{_INSTRUCOES_COMUNS}

Crie uma MENSAGEM DE WHATSAPP de prospecção com base nesta descrição:

\"\"\"{descricao}\"\"\"

A mensagem de WhatsApp deve:
- Ser mais curta e direta que um e-mail (WhatsApp é conversa).
- Começar com uma saudação personalizada com {{nome}}.
- Ter no máximo 2 ou 3 parágrafos curtos; use tópicos com "• " só se realmente ajudar.
- Ser calorosa mas profissional, assinada por {nome_remetente} da {empresa_remetente}.

Responda em JSON com exatamente esta chave:
{{"mensagem": "a mensagem completa de WhatsApp"}}"""

    resp = client.messages.create(
        model=MODELO,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": {
                    "type": "object",
                    "properties": {"mensagem": {"type": "string"}},
                    "required": ["mensagem"],
                    "additionalProperties": False,
                },
            }
        },
    )
    texto = next(b.text for b in resp.content if b.type == "text")
    dados = json.loads(texto)
    return dados["mensagem"]
