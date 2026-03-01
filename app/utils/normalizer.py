"""Normalizer — converte o JSON bruto do Azure Document Intelligence em modelos Pydantic.

Suporta dois tipos de normalização:
  - normalize_result()      → para prebuilt-receipt e prebuilt-invoice (campos estruturados)
  - normalize_read_result() → para prebuilt-read (texto OCR: páginas, linhas, palavras)

Extrai todos os campos disponíveis com fallbacks robustos para que o resto do app
receba sempre uma estrutura consistente.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models import AnalysisResult, LineItem, ReadLine, ReadPage, ReadResult, ReadWord

logger = logging.getLogger("app.utils.normalizer")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_field_value(fields: Dict[str, Any], *keys: str) -> Any:
    """
    Try each key in order and return the first non-None value found.

    Azure DI 2024-11-30 uses type-specific keys:
      valueString, valueNumber, valueDate, valueTime,
      valueCurrency (dict with 'amount' and 'currencyCode'),
      valueAddress (dict), valueCountryRegion, etc.
    Older versions use a plain 'value' key.
    Falls back to 'content' (raw OCR text).
    """
    _VALUE_KEYS = (
        "value", "valueString", "valueNumber", "valueInteger",
        "valueDate", "valueTime", "valueCurrency", "valueAddress",
        "valueCountryRegion", "valuePhoneNumber",
    )
    for key in keys:
        field = fields.get(key)
        if field is None:
            continue
        if not isinstance(field, dict):
            return field
        # Try every known value key
        for vk in _VALUE_KEYS:
            val = field.get(vk)
            if val is not None:
                return val
        # Fall back to content (raw text)
        content = field.get("content")
        if content is not None:
            return content
    return None


def _get_field_confidence(fields: Dict[str, Any], *keys: str) -> Optional[float]:
    """Return the confidence of the first matching field, or None."""
    for key in keys:
        field = fields.get(key)
        if isinstance(field, dict) and "confidence" in field:
            return field["confidence"]
    return None


_DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y-%m-%dT%H:%M:%S",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%B %d, %Y",
    "%b %d, %Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
]


def normalize_date(raw: Any) -> Optional[str]:
    """Normalize a date value to ISO YYYY-MM-DD when possible."""
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw.strftime("%Y-%m-%d")
    if hasattr(raw, "isoformat"):
        return raw.isoformat()[:10]

    raw_str = str(raw).strip()
    if not raw_str:
        return None

    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    logger.warning("Could not parse date '%s' — keeping original", raw_str)
    return raw_str


def _to_float(val: Any) -> Optional[float]:
    """Best-effort conversion to float.

    Handles plain numbers, numeric strings, and Azure ``valueCurrency``
    dicts like ``{"amount": 13.5, "currencyCode": "USD"}``.
    """
    if val is None:
        return None
    # valueCurrency is a dict with an 'amount' key
    if isinstance(val, dict):
        amt = val.get("amount")
        if amt is not None:
            try:
                return float(amt)
            except (ValueError, TypeError):
                return None
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _currency_code(val: Any) -> Optional[str]:
    """Extract currency code from a valueCurrency dict, or return as-is."""
    if isinstance(val, dict):
        return val.get("currencyCode") or val.get("currencySymbol")
    if val is not None:
        return str(val)
    return None


def _address_str(val: Any) -> Optional[str]:
    """Convert an address value (possibly a dict) to a readable string."""
    if val is None:
        return None
    if isinstance(val, dict):
        # valueAddress has 'streetAddress', 'city', 'state', 'postalCode' etc.
        parts = []
        for k in ("streetAddress", "city", "state", "postalCode", "countryRegion"):
            v = val.get(k)
            if v:
                parts.append(str(v))
        return ", ".join(parts) if parts else str(val)
    return str(val)


def _to_str(val: Any) -> Optional[str]:
    """Convert to str if not None."""
    return str(val) if val is not None else None


# ---------------------------------------------------------------------------
# Line-item extraction
# ---------------------------------------------------------------------------

def _extract_items(fields: Dict[str, Any]) -> List[LineItem]:
    """Extract line items from the 'Items' field."""
    items_field = fields.get("Items")
    if items_field is None:
        return []

    # Azure 2024-11-30 uses "valueArray"; older versions use "value"
    if isinstance(items_field, list):
        raw_items = items_field
    elif isinstance(items_field, dict):
        raw_items = items_field.get("valueArray") or items_field.get("value", [])
    else:
        return []

    if not isinstance(raw_items, list):
        return []

    result: List[LineItem] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        # Azure 2024-11-30 uses "valueObject"; older versions use "value"
        sub = item.get("valueObject") or item.get("value", item)
        if not isinstance(sub, dict):
            continue
        result.append(
            LineItem(
                description=_get_field_value(sub, "Description", "ProductCode", "description"),
                quantity=_to_float(_get_field_value(sub, "Quantity", "quantity")),
                unit_price=_to_float(_get_field_value(sub, "UnitPrice", "Price", "unit_price")),
                amount=_to_float(_get_field_value(sub, "TotalPrice", "Amount", "amount")),
                confidence=_get_field_confidence(sub, "Description", "TotalPrice", "Amount"),
            )
        )
    return result


def _compute_confidence(fields: Dict[str, Any]) -> Optional[float]:
    """Average of all available confidence values, or None."""
    scores = []
    for field in fields.values():
        if isinstance(field, dict) and "confidence" in field:
            try:
                scores.append(float(field["confidence"]))
            except (ValueError, TypeError):
                pass
    return round(sum(scores) / len(scores), 4) if scores else None


# ---------------------------------------------------------------------------
# Main normalisation entry-point
# ---------------------------------------------------------------------------

def normalize_result(
    raw: Dict[str, Any],
    document_type: str,
    analysis_id: str,
    source_filename: str,
) -> AnalysisResult:
    """Convert raw Azure DI JSON into a normalised AnalysisResult."""
    documents = raw.get("documents", [])
    if not documents:
        logger.warning("No documents block in Azure response")
        return AnalysisResult(
            analysis_id=analysis_id,
            document_type=document_type,
            needs_review=True,
            source_filename=source_filename,
        )

    fields: Dict[str, Any] = documents[0].get("fields", {})

    # --- Common fields ---
    vendor_name = _get_field_value(
        fields, "MerchantName", "VendorName",
    )
    vendor_address = _address_str(
        _get_field_value(fields, "MerchantAddress", "VendorAddress", "VendorAddressRecipient")
    )
    vendor_phone = _to_str(_get_field_value(fields, "MerchantPhoneNumber"))
    vendor_tax_id = _to_str(_get_field_value(fields, "VendorTaxId"))

    raw_date = _get_field_value(fields, "TransactionDate", "InvoiceDate", "Date")
    document_date = normalize_date(raw_date)

    # Monetary values — _to_float handles valueCurrency dicts
    subtotal_raw = _get_field_value(fields, "Subtotal", "SubTotal")
    tax_raw = _get_field_value(fields, "TotalTax", "Tax")
    total_raw = _get_field_value(fields, "Total", "InvoiceTotal")
    tip_raw = _get_field_value(fields, "Tip")

    subtotal = _to_float(subtotal_raw)
    tax = _to_float(tax_raw)
    total = _to_float(total_raw)
    tip = _to_float(tip_raw)

    # Currency: try explicit CurrencyCode, then extract from any monetary field
    currency_val = _get_field_value(fields, "CurrencyCode", "currency")
    if currency_val is None:
        for raw_money in (total_raw, subtotal_raw, tax_raw):
            code = _currency_code(raw_money)
            if code:
                currency_val = code
                break

    document_id = _get_field_value(fields, "InvoiceId", "ReceiptId")

    # --- Receipt-specific ---
    transaction_time = _to_str(
        _get_field_value(fields, "TransactionTime")
    )
    payment_method = _to_str(
        _get_field_value(fields, "PaymentMethod")
    )

    # --- Invoice-specific ---
    raw_due = _get_field_value(fields, "DueDate")
    due_date = normalize_date(raw_due)
    customer_name = _to_str(_get_field_value(fields, "CustomerName"))
    customer_address = _address_str(
        _get_field_value(fields, "CustomerAddress", "BillingAddress")
    )
    shipping_address = _address_str(_get_field_value(fields, "ShippingAddress"))
    payment_term = _to_str(
        _get_field_value(fields, "PaymentTerm", "PaymentTerms")
    )
    purchase_order = _to_str(_get_field_value(fields, "PurchaseOrder"))

    items = _extract_items(fields)
    confidence_score = _compute_confidence(fields)
    needs_review = total is None or document_date is None

    result = AnalysisResult(
        analysis_id=analysis_id,
        document_type=document_type,
        vendor_name=_to_str(vendor_name),
        vendor_address=vendor_address,
        vendor_phone=vendor_phone,
        vendor_tax_id=vendor_tax_id,
        document_date=document_date,
        currency=_currency_code(currency_val) if not isinstance(currency_val, str) else currency_val,
        subtotal=subtotal,
        tax=tax,
        total=total,
        document_id=_to_str(document_id),
        items=items,
        confidence_score=confidence_score,
        needs_review=needs_review,
        source_filename=source_filename,
        transaction_time=transaction_time,
        payment_method=payment_method,
        tip=tip,
        due_date=due_date,
        customer_name=customer_name,
        customer_address=customer_address,
        shipping_address=shipping_address,
        payment_term=payment_term,
        purchase_order=purchase_order,
    )

    if needs_review:
        logger.warning(
            "analysis_id=%s needs review: total=%s, date=%s",
            analysis_id, total, document_date,
        )

    return result


# ---------------------------------------------------------------------------
# OCR Read normalisation
# ---------------------------------------------------------------------------

def normalize_read_result(
    raw: Dict[str, Any],
    analysis_id: str,
    source_filename: str,
) -> ReadResult:
    """Convert raw Azure DI prebuilt-read JSON into a ReadResult.

    The Read model returns pages → lines → words, plus optional style and
    language information.  We flatten everything into a simple structure
    that the template can render easily.
    """

    # Full OCR text
    content: str = raw.get("content", "")

    # --- Pages, lines, words ---
    pages: List[ReadPage] = []
    total_words = 0

    for raw_page in raw.get("pages", []):
        lines: List[ReadLine] = []
        page_words: List[ReadWord] = []

        for raw_line in raw_page.get("lines", []):
            lines.append(ReadLine(content=raw_line.get("content", "")))

        for raw_word in raw_page.get("words", []):
            w = ReadWord(
                content=raw_word.get("content", ""),
                confidence=raw_word.get("confidence"),
            )
            page_words.append(w)
            total_words += 1

        pages.append(ReadPage(
            page_number=raw_page.get("pageNumber", 0),
            width=raw_page.get("width"),
            height=raw_page.get("height"),
            unit=raw_page.get("unit"),
            lines=lines,
            words=page_words,
        ))

    # --- Languages ---
    languages: List[str] = []
    for lang_entry in raw.get("languages", []):
        locale = lang_entry.get("locale")
        if locale and locale not in languages:
            languages.append(locale)

    # --- Handwriting detection ---
    has_handwriting = False
    for style in raw.get("styles", []):
        if style.get("isHandwritten"):
            has_handwriting = True
            break

    return ReadResult(
        analysis_id=analysis_id,
        source_filename=source_filename,
        content=content,
        pages=pages,
        languages=languages,
        has_handwriting=has_handwriting,
        total_pages=len(pages),
        total_words=total_words,
    )
