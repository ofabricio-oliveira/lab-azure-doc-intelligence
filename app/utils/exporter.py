"""
Exporter — generates CSV and XLSX files from an AnalysisResult.

Both formats use the same normalised column set so downloads match what the
user sees on screen.
"""

import csv
import io
import logging
from typing import List

from openpyxl import Workbook

from app.models import AnalysisResult

logger = logging.getLogger("app.utils.exporter")

# Column order for export files
COLUMNS = [
    "document_type",
    "vendor_name",
    "vendor_address",
    "vendor_phone",
    "vendor_tax_id",
    "document_date",
    "currency",
    "subtotal",
    "tax",
    "total",
    "document_id",
    "transaction_time",
    "payment_method",
    "tip",
    "due_date",
    "customer_name",
    "customer_address",
    "shipping_address",
    "payment_term",
    "purchase_order",
    "confidence_score",
    "needs_review",
    "source_filename",
]

ITEM_COLUMNS = [
    "item_description",
    "item_quantity",
    "item_unit_price",
    "item_amount",
    "item_confidence",
]


def _result_to_rows(result: AnalysisResult) -> List[dict]:
    """
    Flatten an AnalysisResult into a list of dicts (one row per item,
    or a single row if there are no items).
    """
    base = {
        "document_type": result.document_type,
        "vendor_name": result.vendor_name or "",
        "vendor_address": result.vendor_address or "",
        "vendor_phone": result.vendor_phone or "",
        "vendor_tax_id": result.vendor_tax_id or "",
        "document_date": result.document_date or "",
        "currency": result.currency or "",
        "subtotal": result.subtotal if result.subtotal is not None else "",
        "tax": result.tax if result.tax is not None else "",
        "total": result.total if result.total is not None else "",
        "document_id": result.document_id or "",
        "transaction_time": result.transaction_time or "",
        "payment_method": result.payment_method or "",
        "tip": result.tip if result.tip is not None else "",
        "due_date": result.due_date or "",
        "customer_name": result.customer_name or "",
        "customer_address": result.customer_address or "",
        "shipping_address": result.shipping_address or "",
        "payment_term": result.payment_term or "",
        "purchase_order": result.purchase_order or "",
        "confidence_score": (
            result.confidence_score if result.confidence_score is not None else ""
        ),
        "needs_review": str(result.needs_review).lower(),
        "source_filename": result.source_filename,
    }

    if not result.items:
        # Single row, items columns empty
        row = {**base}
        for col in ITEM_COLUMNS:
            row[col] = ""
        return [row]

    rows = []
    for item in result.items:
        row = {
            **base,
            "item_description": item.description or "",
            "item_quantity": item.quantity if item.quantity is not None else "",
            "item_unit_price": item.unit_price if item.unit_price is not None else "",
            "item_amount": item.amount if item.amount is not None else "",
            "item_confidence": item.confidence if item.confidence is not None else "",
        }
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

def generate_csv(result: AnalysisResult) -> str:
    """Return a CSV string for the given result."""
    rows = _result_to_rows(result)
    all_columns = COLUMNS + ITEM_COLUMNS
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=all_columns)
    writer.writeheader()
    writer.writerows(rows)
    csv_text = output.getvalue()
    logger.info("CSV generated: %d rows, %d bytes", len(rows), len(csv_text))
    return csv_text


# ---------------------------------------------------------------------------
# XLSX
# ---------------------------------------------------------------------------

def generate_xlsx(result: AnalysisResult) -> bytes:
    """Return XLSX file content as bytes for the given result."""
    rows = _result_to_rows(result)
    all_columns = COLUMNS + ITEM_COLUMNS

    wb = Workbook()
    ws = wb.active
    ws.title = "Analysis"

    # Header row
    ws.append(all_columns)

    # Data rows
    for row in rows:
        ws.append([row.get(col, "") for col in all_columns])

    # Auto-width (best effort)
    for col_cells in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col_cells)
        ws.column_dimensions[col_cells[0].column_letter].width = min(max_len + 2, 40)

    buffer = io.BytesIO()
    wb.save(buffer)
    xlsx_bytes = buffer.getvalue()
    logger.info("XLSX generated: %d rows, %d bytes", len(rows), len(xlsx_bytes))
    return xlsx_bytes
