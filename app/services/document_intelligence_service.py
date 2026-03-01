"""Azure Document Intelligence service.

Envia documentos para a API do Azure e retorna o JSON bruto.
Suporta três modelos prebuilt: prebuilt-receipt, prebuilt-invoice e prebuilt-read (OCR).
"""

import logging
from pathlib import Path

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

from app.config import settings

logger = logging.getLogger("app.services.document_intelligence")

# Mapeia o valor do formulário para o model ID do Azure
ALLOWED_MODELS = {
    "receipt": "prebuilt-receipt",   # extrai campos de recibos (comerciante, itens, total…)
    "invoice": "prebuilt-invoice",   # extrai campos de faturas (fornecedor, cliente, vencimento…)
    "read":    "prebuilt-read",      # OCR puro — extrai texto, linhas e palavras
}


def get_client() -> DocumentIntelligenceClient:
    """Cria o cliente do Azure Document Intelligence usando endpoint + key do .env."""
    if not settings.AZURE_DI_ENDPOINT or not settings.AZURE_DI_KEY:
        raise RuntimeError(
            "Azure Document Intelligence not configured. "
            "Set AZURE_DI_ENDPOINT and AZURE_DI_KEY in your .env file."
        )
    return DocumentIntelligenceClient(
        endpoint=settings.AZURE_DI_ENDPOINT.rstrip("/"),
        credential=AzureKeyCredential(settings.AZURE_DI_KEY),
        api_version=settings.AZURE_DI_API_VERSION,
    )


def analyze_document(file_path: str, document_type: str) -> dict:
    """Envia o documento para o Azure e retorna o resultado bruto (dict).

    O fluxo é o mesmo para os três modelos — o que muda é o model_id:
    1. Abre o arquivo em bytes
    2. Chama begin_analyze_document (operação assíncrona no Azure)
    3. Aguarda o resultado com poller.result()
    4. Converte para dict com as_dict()

    Args:
        file_path: Caminho do arquivo (PDF, PNG, JPG).
        document_type: 'receipt', 'invoice' ou 'read'.
    Returns:
        Dict com o JSON completo retornado pela API do Azure.
    """
    if document_type not in ALLOWED_MODELS:
        raise ValueError(
            f"Unsupported document type '{document_type}'. "
            f"Allowed: {list(ALLOWED_MODELS.keys())}"
        )

    model_id = ALLOWED_MODELS[document_type]
    client = get_client()

    logger.info("Starting analysis: model=%s, file=%s", model_id, Path(file_path).name)

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    # begin_analyze_document retorna um LROPoller (Long Running Operation)
    poller = client.begin_analyze_document(
        model_id=model_id,
        analyze_request=file_bytes,
        content_type="application/octet-stream",
    )
    result = poller.result()  # bloqueia até a análise terminar
    logger.info("Analysis complete: model=%s", model_id)
    return result.as_dict()
