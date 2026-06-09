# Como publicar o AlcanceMax para clientes

## Passo a passo completo

---

### 1. Criar conta no GitHub (gratuito)
Acesse https://github.com e crie uma conta.

---

### 2. Criar repositório privado
1. Clique em **New repository**
2. Nome: `alcancemax`
3. Marque **Private**
4. Clique em **Create repository**

---

### 3. Preparar o ZIP do app para distribuição
Monte um ZIP com estes arquivos:
```
alcancemax/
├── app.py
├── license.py
├── email_sender.py
├── whatsapp_helper.py
├── requirements.txt
├── config.json          ← use o config_padrao.json (renomeado)
└── dados/
    └── tmp/             ← pasta vazia (crie manualmente)
```

**Importante:** use o `config_padrao.json` (sem seus dados pessoais) renomeado para `config.json`.

---

### 4. Criar um Release no GitHub
1. No repositório, clique em **Releases → Create a new release**
2. Tag: `v1.0`
3. Arraste e solte estes arquivos:
   - `alcancemax.zip` (o ZIP do app)
   - `instalar.sh` (instalador Mac/Linux)
   - `instalar.bat` (instalador Windows)
4. Clique em **Publish release**

---

### 5. Atualizar as URLs nos instaladores
Abra `instalar.sh` e `instalar.bat` e substitua:
```
SEU_USUARIO
```
pelo seu usuário do GitHub. Exemplo:
```
https://github.com/allantonini/alcancemax/releases/latest/download/alcancemax.zip
```

---

### 6. Publicar a página de download
**Opção A — GitHub Pages (gratuito):**
1. Suba o `index.html` no repositório (pode ser público)
2. Vá em **Settings → Pages → Source: main branch**
3. O link será: `https://SEU_USUARIO.github.io/alcancemax/`

**Opção B — Qualquer hospedagem:**
Faça upload do `index.html` para seu site/servidor.

---

### 7. Atualizar as URLs no index.html
Abra `index.html` e substitua as 3 URLs no objeto `URLS`:
```javascript
const URLS = {
  mac_cmd:   "curl -fsSL https://github.com/SEU_USUARIO/alcancemax/releases/latest/download/instalar.sh | bash",
  linux_cmd: "curl -fsSL https://github.com/SEU_USUARIO/alcancemax/releases/latest/download/instalar.sh | bash",
  win_bat:   "https://github.com/SEU_USUARIO/alcancemax/releases/latest/download/instalar.bat",
};
```

---

### 8. Enviar para o cliente
Você envia apenas **um link** para o cliente, por exemplo:
```
https://allantonini.github.io/alcancemax/
```

A página detecta automaticamente o sistema e mostra o instalador certo.

---

## Fluxo do cliente

1. Cliente acessa o link
2. Vê o botão certo para o SO dele (Mac/Windows/Linux)
3. Baixa/executa o instalador
4. O app instala em ~2-3 minutos
5. Abre o AlcanceMax e insere e-mail + chave de licença
6. Você aprova a licença no painel admin

---

## Como atualizar o app depois

1. Atualize os arquivos
2. Crie um novo ZIP
3. Publique um novo Release no GitHub (pode manter o tag `latest`)
4. Os instaladores sempre baixam a versão mais recente automaticamente
