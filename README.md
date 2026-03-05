# 📄 Extrator de Documentos com Azure Document Intelligence

[![License: MIT](https://img.shields.io/badge/Licença-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

**Lab prático:** Aprenda a integrar os modelos prebuilt do **Azure AI Document Intelligence** com FastAPI — incluindo **OCR Read** (extração de texto), **Receipt** (recibos) e **Invoice** (faturas) — e exportar resultados para CSV/Excel.

---

## 📋 O que você vai fazer

1. ✅ Upload de PDF/PNG/JPG pelo navegador
2. ✅ Escolher o modelo prebuilt: OCR Read, Receipt ou Invoice
3. ✅ **OCR Read** → extrair texto puro (páginas, linhas, palavras) com detecção de idioma e manuscrito
4. ✅ **Receipt / Invoice** → extrair campos estruturados: fornecedor, data, total, impostos, itens…
5. ✅ Visualizar resultado na tela
6. ✅ Baixar TXT (OCR Read) ou CSV/Excel (Receipt/Invoice)

---

## 🤖 O que é o Azure Document Intelligence?

O [Azure AI Document Intelligence](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/?view=doc-intel-4.0.0) é um serviço de IA do Azure que usa OCR (reconhecimento óptico de caracteres) e modelos de deep learning para analisar documentos e extrair texto, campos e estruturas automaticamente.

O serviço oferece **modelos prebuilt** (pré-treinados) prontos para uso, sem necessidade de treinamento. Neste lab utilizamos três deles:

| Modelo | ID do Azure | O que faz | Saída |
|--------|-------------|-----------|-------|
| **Read** | `prebuilt-read` | OCR puro — extrai texto impresso e manuscrito, detecta idiomas | Texto completo, páginas, linhas, palavras com confiança |
| **Receipt** | `prebuilt-receipt` | Extrai campos de comprovantes de venda | Comerciante, data, itens, total, impostos, forma de pagamento |
| **Invoice** | `prebuilt-invoice` | Extrai campos de documentos de cobrança | Fornecedor, cliente, itens, total, vencimento, condições |

O modelo **Read** é a base dos demais — ele faz a leitura OCR. Os modelos Receipt e Invoice vão além: além do OCR, eles interpretam os campos e devolvem dados estruturados.

> **Referências oficiais:**
> - [Modelo Read (prebuilt-read)](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/read?view=doc-intel-4.0.0)
> - [Modelo Receipt (prebuilt-receipt)](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/receipt?view=doc-intel-4.0.0)
> - [Modelo Invoice (prebuilt-invoice)](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/invoice?view=doc-intel-4.0.0)

### Este app vs. Document Intelligence Studio

O Azure também oferece o [Document Intelligence Studio](https://documentintelligence.ai.azure.com/studio), que é uma interface web do próprio Azure para testar os modelos diretamente no navegador, sem escrever código.

**A diferença é que este lab é um app Python próprio** que consome a mesma API por trás do Studio — via SDK — mostrando como integrar o Document Intelligence em uma aplicação real. No Studio você testa; aqui você aprende a construir.

---

## 💡 Exemplo de Caso de Uso

Imagine que seu time financeiro recebe **dezenas de recibos e faturas por semana** em PDF ou foto. Alguém precisa abrir cada um, copiar dados manualmente para uma planilha e conferir valores.

**Com este lab:**
- **OCR Read** → Precisa apenas extrair texto de um documento escaneado? Use o Read.
- **Receipt / Invoice** → Quer os campos estruturados (fornecedor, data, total, itens)? Use Receipt ou Invoice.

Faça upload, clique "Analisar", e em segundos tenha o resultado. É isso que você vai aprender: **extração inteligente de documentos com IA do Azure**.

---

## 🛠️ Requisitos

- **Seu computador:** Windows 10/11 ou macOS
- **Python:** 3.11 ou superior (✅ testado até 3.14)
- **Git:** Opcional, para clonar o repositório ([baixar aqui](https://git-scm.com/))
- **Conta Azure:** Com recurso Azure AI Document Intelligence criado
- **VS Code:** Recomendado (opcional)
- **Internet:** Conexão estável

---

## 📖 Como Começar

| Guia | Tempo | Indicado para |
|------|-------|---------------|
| [COMECE AQUI (START_HERE.md)](START_HERE.md) | ~1h | Primeira vez? Comece aqui! |
| [RESUMO RÁPIDO (QUICKSTART.md)](QUICKSTART.md) | ~5 min | Já tem tudo configurado? Rode rápido |

---

## 🎯 Caso esteja começando do zero, vá por aqui:

👉 Leia **[COMECE AQUI (START_HERE.md)](START_HERE.md)** para o guia passo a passo completo!

---

## 🚀 Caso Já Tenha Noções do Funcionamento, Veja o Resumo

Para quem já tem tudo configurado, em resumo será:

```bash
# Clonar o repositório
git clone https://github.com/ofabricio-oliveira/lab-azure-doc-intelligence.git
cd lab-azure-doc-intelligence

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows

# Instalar dependências
pip install -r requirements.txt

# Criar arquivo .env
cp .env.example .env
# ⚠️ Edite .env e adicione suas credenciais do Azure

# Rodar o servidor
uvicorn app.main:app --reload

# Abra no navegador
# http://localhost:8000
```

---

## 📐 Arquitetura

```
Usuário
  │
  │  1. Upload PDF/imagem
  ▼
┌──────────────────────────┐
│  Frontend (HTML/CSS)     │
│  - Formulário de upload  │
│  - Seleção: Read,        │
│    Receipt ou Invoice    │
└──────────┬───────────────┘
           │ 2. POST /analyze
           ▼
┌──────────────────────────┐
│  FastAPI Backend         │
│  ├─ Validação            │  3. Valida arquivo
│  ├─ DI Service           │  4. Envia para Azure
│  ├─ Normalizer           │  5. Normaliza resultado
│  └─ Exporter             │  6. Gera TXT/CSV/XLSX
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  Azure Document          │
│  Intelligence            │
│  (prebuilt-read,         │
│   prebuilt-receipt ou    │
│   prebuilt-invoice)      │
└──────────────────────────┘
```

---

## ⚙️ Variáveis de Ambiente

Crie um arquivo `.env` baseado em `.env.example`:

```env
AZURE_DI_ENDPOINT=https://seu-recurso.cognitiveservices.azure.com
AZURE_DI_KEY=sua-chave-aqui
```

| Variável | Obrigatória | Descrição | Default |
|----------|-------------|-----------|---------|
| `AZURE_DI_ENDPOINT` | ✅ | URL do recurso Document Intelligence | — |
| `AZURE_DI_KEY` | ✅ | Chave de acesso (KEY 1 ou KEY 2) | — |
| `AZURE_DI_API_VERSION` | ❌ | Versão da API | `2024-11-30` |
| `MAX_FILE_SIZE_MB` | ❌ | Tamanho máximo do upload (MB) | `10` |

⚠️ **Pontos críticos:**
- ✅ `AZURE_DI_ENDPOINT` **NÃO** deve terminar com `/`
- ✅ A key deve ser copiada exatamente do portal Azure
- ✅ **Não commite o `.env`!** Ele já está no `.gitignore`

---

## 🏗️ Estrutura do Código

```
lab-azure-doc-intelligence/
├── app/
│   ├── main.py                              # FastAPI — rotas e app principal
│   ├── config.py                            # Configuração via .env
│   ├── models.py                            # Pydantic models (AnalysisResult, ReadResult, etc.)
│   ├── services/
│   │   └── document_intelligence_service.py # Integração com Azure DI SDK (3 modelos)
│   ├── utils/
│   │   ├── normalizer.py                    # Normalização — Receipt/Invoice + OCR Read
│   │   └── exporter.py                      # Geração de CSV/XLSX
│   ├── templates/
│   │   ├── index.html                       # Formulário de upload (seleção de modelo)
│   │   ├── result.html                      # Resultado Receipt/Invoice
│   │   └── read_result.html                 # Resultado OCR Read
│   └── static/
│       └── styles.css                       # Estilos
├── data/
│   ├── uploads/                             # Arquivos enviados (temporário)
│   └── results/                             # JSON bruto do Azure (educacional)
├── sample_docs/                             # Documentos de exemplo para testar
├── tests/
│   ├── test_normalizer.py                   # Testes do normalizer (inclui formato 2024-11-30)
│   └── test_exporter.py                     # Testes do exporter CSV/XLSX
├── .env.example                             # Exemplo de variáveis de ambiente
├── .gitignore
├── Makefile                                 # Atalhos: make run, make test, make clean
├── requirements.txt
├── QUICKSTART.md                            # Resumo rápido (~5 min)
├── START_HERE.md                            # Guia passo a passo completo (~1h)
└── README.md                                # Este arquivo
```

**Fluxo de dados:**

1. Usuário faz upload no `index.html` e escolhe o modelo (Read, Receipt ou Invoice)
2. `main.py` recebe e valida
3. `document_intelligence_service.py` envia para Azure DI com o modelo escolhido
4. `normalizer.py` normaliza o JSON (compatível com API 2024-11-30)
5. Template exibe o resultado: `read_result.html` (OCR) ou `result.html` (Receipt/Invoice)
6. Download: `.txt` (OCR Read) ou CSV/XLSX (Receipt/Invoice)

---

## 🧪 Testes

```bash
# Rodar todos os testes
pytest tests/ -v

# Ou via Makefile
make test
```

São **63 testes** cobrindo:
- Normalização de datas, valores monetários, campos de moeda
- Formato antigo da API (`value`) e novo (`valueCurrency`, `valueString`, etc.)
- Extração de itens com `valueArray`/`valueObject`
- Normalização do OCR Read (páginas, palavras, idiomas, manuscrito)
- Geração de CSV e XLSX

---

## 📚 Conceitos Aprendidos

✅ Integração com Azure AI Document Intelligence
✅ Modelos prebuilt: `prebuilt-read` (OCR), `prebuilt-receipt`, `prebuilt-invoice`
✅ Normalização de dados extraídos por IA (texto OCR + campos estruturados)
✅ Exportação para CSV e Excel (.xlsx)
✅ API assíncrona com FastAPI
✅ Validação de arquivos e tratamento de erros
✅ Variáveis de ambiente e configuração segura

---

## ❌ Troubleshooting

### Erro: "Azure Document Intelligence not configured"

**Verificar:**
- ✅ Arquivo `.env` existe na raiz do projeto
- ✅ `AZURE_DI_ENDPOINT` e `AZURE_DI_KEY` estão preenchidos
- ✅ Sem espaços extras ou aspas nos valores

### Erro: "403 Forbidden" ou "401 Unauthorized"

**Verificar:**
- ✅ A key está correta (copie novamente do portal)
- ✅ O endpoint corresponde ao recurso correto

### Campos ausentes no resultado

**Informação:**
- A qualidade da extração depende da qualidade do PDF/imagem
- PDFs escaneados com baixa resolução podem ter resultados piores
- O modelo prebuilt pode não reconhecer todos os campos de todos os documentos
- Quando campos importantes estão faltando, o flag **Requer Revisão** é ativado

### Erro: "File type not allowed"

**Verificar:**
- ✅ Use apenas: `.pdf`, `.png`, `.jpg`, `.jpeg`
- ✅ Tamanho máximo: 10 MB (configurável via `MAX_FILE_SIZE_MB`)

---

## ⚠️ Aviso Importante sobre Segurança

Este projeto **NÃO possui** as seguintes proteções necessárias para produção:

- 🔓 **Sem autenticação/autorização** — qualquer pessoa com acesso à URL pode usar
- 🔑 **Chave da API em .env** — em produção, use Azure Key Vault ou Managed Identity
- 💾 **Dados em memória** — reiniciar o servidor perde todos os resultados
- 🧹 **Sem limpeza automática** — arquivos em `data/` acumulam manualmente
- 🌐 **Sem HTTPS** — em produção, sempre use HTTPS com certificado válido
- 🛡️ **Sem rate limiting** — sem proteção contra uso excessivo

**Para uso em produção**, considere: autenticação (Azure AD / OAuth), HTTPS, banco de dados, Azure Key Vault para secrets, rate limiting, logging centralizado e monitoramento.

---

## ⚠️ Disclaimer

> **Esta solução foi desenvolvida com finalidade exclusivamente laboratorial e educacional.**
>
> O objetivo deste projeto é demonstrar as capacidades do **Azure AI Document Intelligence** — especificamente os modelos prebuilt Read (OCR), Receipt e Invoice — e não ensinar boas práticas de desenvolvimento Python ou engenharia de software.
>
> O uso em ambientes de produção deve considerar critérios adicionais de segurança, desempenho, conformidade e manutenção, que **não estão contemplados** neste projeto.

---

## 📄 Licença

MIT. Veja [LICENSE](LICENSE).

---

**Desenvolvido com ❤️ para aprendizado — 2026**
