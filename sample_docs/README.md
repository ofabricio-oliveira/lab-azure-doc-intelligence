# 📁 Documentos de Exemplo

Esta pasta contém arquivos de exemplo para testar o Extrator de Documentos LAB.

## Arquivos incluídos

| Arquivo | Tipo | Descrição |
|---------|------|-----------|
| `sample_receipt.txt` | Recibo (Receipt) | Texto de exemplo — veja instruções abaixo |
| `sample_invoice.txt` | Fatura (Invoice) | Texto de exemplo — veja instruções abaixo |

## Como obter documentos reais para testar

Como não podemos distribuir PDFs protegidos por direitos autorais, seguem as opções:

### Opção A: Usar amostras do próprio Azure (recomendado)

O Azure oferece documentos gratuitos para teste:

1. Acesse o [Azure AI Document Intelligence Studio](https://documentintelligence.ai.azure.com/studio)
2. Selecione **"Receipts"** ou **"Invoices"**
3. Clique em **"Run analysis"** com as amostras prontas
4. Baixe os PDFs de exemplo

### Opção B: Usar seus próprios recibos

- Tire uma foto de qualquer recibo ou fatura (supermercado, restaurante, etc.)
- Salve como JPG/PNG
- Faça upload no lab

### Opção C: Criar PDFs de teste simples

1. Abra o Word ou Google Docs
2. Digite um layout simples de recibo ou fatura
3. Salve/exporte como PDF

### Opção D: Faturas de domínio público

Pesquise por "sample invoice PDF" — há vários disponíveis gratuitamente para testes.

## Dica

A pasta `data/results/` conterá os JSONs brutos das respostas do Azure,
ótimos para aprender como a API do Document Intelligence estrutura suas respostas.
