# 🎯 GUIA PASSO A PASSO COMPLETO — COMECE AQUI!

## 👋 Bem-vindo!

Você está prestes a construir algo incrível! 🚀

Este é o guia completo para aprender como **integrar Azure AI Document Intelligence com Python**. Vamos criar um **extrator inteligente de documentos** que usa IA para ler texto via OCR, analisar recibos e faturas e extrair dados estruturados automaticamente!

Perfeito para aprender, experimentar e criar algo legal pro seu portfólio. 💻

---

## 📋 O Que Você Vai Fazer

1. ✅ Instalar Python e dependências
2. ✅ Criar recurso Azure Document Intelligence
3. ✅ Rodar o projeto localmente
4. ✅ Testar com documentos de exemplo

**Tempo total estimado:** ~1 hora (incluindo leitura)

---

## 🚀 ETAPA 1: Preparar o Ambiente (15 minutos)

### 1.1 — Instalar Python

1. Acesse: `https://www.python.org/downloads/`
2. ⚠️ **CRÍTICO:** Baixe **Python 3.11.x ou 3.12.x**
3. Execute o instalador
4. ⚠️ **Marque "Add Python to PATH"** na primeira tela
5. Clique em **"Install Now"**

**Validar:**

```powershell
python --version
# Deve mostrar: Python 3.11.x ou 3.12.x
```

---

### 1.2 — Instalar Git (opcional, para clonar)

1. Acesse: `https://git-scm.com/download/win`
2. Baixe e instale com opções padrão

---

## 💻 ETAPA 2: Baixar e Configurar o Projeto (10 minutos)

### 2.1 — Obter o projeto

```powershell
# Se tem Git:
git clone https://github.com/SEU_USUARIO/lab-document-intelligence.git
cd lab-document-intelligence

# OU: baixe o ZIP e extraia
```

### 2.2 — Criar ambiente virtual

```powershell
# Windows
python -m venv venv
venv\Scripts\activate
```

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 2.3 — Instalar dependências

```bash
pip install -r requirements.txt
```

Aguarde ~2 minutos.

---

## 🔑 ETAPA 3: Criar o Recurso no Azure (20 minutos)

### 3.1 — Acessar Azure Portal

1. Abra: `https://portal.azure.com`
2. Faça login com sua conta Microsoft

### 3.2 — Criar recurso Document Intelligence

1. Na barra de busca, digite: **"Document Intelligence"**
2. Clique em **"Azure AI Document Intelligence"**
3. Clique em **"+ Create"**
4. Preencha:
   - **Subscription:** Selecione sua assinatura
   - **Resource group:** Clique "Create new" → `docint-lab-rg`
   - **Region:** `East US` (boa disponibilidade)
   - **Name:** `meu-doc-intelligence-2026` (nome único)
   - **Pricing tier:** `Free F0` (para lab — até 500 páginas/mês grátis)
5. Clique **"Review + create"** → **"Create"**
6. Aguarde ~1 minuto → **"Go to resource"**

### 3.3 — Obter Endpoint e Key

1. No recurso, menu esquerdo: **"Keys and Endpoint"**
2. Copie:
   - **Endpoint:** `https://meu-doc-intelligence-2026.cognitiveservices.azure.com/`
   - **KEY 1:** Clique no ícone de copiar

### 3.4 — Configurar .env

```powershell
copy .env.example .env
```

Edite o `.env`:

```env
AZURE_DI_ENDPOINT=https://meu-doc-intelligence-2026.cognitiveservices.azure.com
AZURE_DI_KEY=sua-chave-copiada-aqui
```

⚠️ **O endpoint NÃO deve terminar com `/`**

---

## 🎮 ETAPA 4: Rodar o Projeto (5 minutos)

```bash
uvicorn app.main:app --reload
```

Saída esperada:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Application startup complete.
```

✅ O servidor está rodando!

---

## 🧪 ETAPA 5: Testar (5 minutos)

### 5.1 — Testar com documento de exemplo

1. Abra o navegador: `http://localhost:8000`
2. Clique em **"Escolher Arquivo"** (ou "Browse")
3. Selecione um arquivo de `sample_docs/` ou um recibo/documento real (PDF/PNG/JPG)
4. Escolha o modelo: **OCR Read**, **Recibo (Receipt)** ou **Fatura (Invoice)**
5. Clique em **"Analisar"**
6. Aguarde 10–30 segundos

### 5.2 — Verificar resultado

**Se usou OCR Read:**
1. Veja o texto completo extraído do documento
2. Veja informações: total de páginas, palavras, idiomas detectados
3. Expanda “Ver palavras e confiança” para detalhes por página
4. Clique em **"Baixar Texto (.txt)"**

**Se usou Receipt ou Invoice:**
1. Veja o **Resumo** com fornecedor, data, total, etc.
2. Veja a **tabela de itens** (se o documento tiver)
3. Observe o flag **Requer Revisão** se algum campo estiver faltando
4. Clique em **"Baixar CSV"** ou **"Baixar Excel"**
5. Abra o arquivo baixado e compare com a tela

✅ **Funcionou? Parabéns!**

---

## ✅ CHECKLIST FINAL

- [ ] Python instalado e funcionando
- [ ] Recurso Azure Document Intelligence criado
- [ ] Endpoint e key configurados no `.env`
- [ ] Servidor rodando (`http://localhost:8000`)
- [ ] Teste com documento funcionou (OCR Read, Receipt ou Invoice)
- [ ] Download funcionou (.txt, CSV ou Excel)

---

## 🎉 PARABÉNS!

Você completou o lab com sucesso:

✅ Integrou com Azure AI Document Intelligence  
✅ Extraiu texto (OCR Read) e dados estruturados (Receipt/Invoice)  
✅ Gerou exports (TXT, CSV, Excel)  
✅ Criou um projeto de portfólio!  

---

## 📚 Próximos Passos

1. **Experimente:** Teste os 3 modelos — OCR Read, Receipt e Invoice — com diferentes documentos
2. **Explore:** Veja o JSON bruto em `data/results/` para entender a resposta do Azure
3. **Customize:** Adicione novos campos ou modelos (ex: `prebuilt-idDocument`)
4. **Compartilhe:** Adicione ao seu GitHub e portfólio

---

## 🆘 Precisa de Ajuda?

- **Documentação completa:** [README.md](README.md)
- **Resumo rápido:** [QUICKSTART.md](QUICKSTART.md)
- **Mais conteúdo:** [fabricio.tech](https://fabricio.tech)

---

**Desenvolvido com ❤️ para aprendizado — 2026**

📌 Mais conteúdo em [fabricio.tech](https://fabricio.tech)
