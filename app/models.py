"""Pydantic models for structured data exchange within the application."""

from typing import List, Optional
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Receipt / Invoice models
# ---------------------------------------------------------------------------

class LineItem(BaseModel):
    """A single line item extracted from a receipt or invoice."""
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: Optional[float] = None
    confidence: Optional[float] = None


class AnalysisResult(BaseModel):
    """Normalized result from Azure Document Intelligence analysis."""
    analysis_id: str
    document_type: str                      # "receipt" or "invoice"

    # --- Common fields ---
    vendor_name: Optional[str] = None       # MerchantName / VendorName
    vendor_address: Optional[str] = None    # MerchantAddress / VendorAddress
    vendor_phone: Optional[str] = None      # MerchantPhoneNumber
    vendor_tax_id: Optional[str] = None     # VendorTaxId
    document_date: Optional[str] = None     # TransactionDate / InvoiceDate
    currency: Optional[str] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    document_id: Optional[str] = None       # InvoiceId / ReceiptId
    items: List[LineItem] = []
    confidence_score: Optional[float] = None
    needs_review: bool = False
    source_filename: str = ""

    # --- Receipt-specific ---
    transaction_time: Optional[str] = None  # TransactionTime
    payment_method: Optional[str] = None    # e.g. "Visa *1234"
    tip: Optional[float] = None

    # --- Invoice-specific ---
    due_date: Optional[str] = None          # DueDate
    customer_name: Optional[str] = None     # CustomerName
    customer_address: Optional[str] = None  # CustomerAddress / BillingAddress
    shipping_address: Optional[str] = None  # ShippingAddress
    payment_term: Optional[str] = None      # PaymentTerm / PaymentTerms
    purchase_order: Optional[str] = None    # PurchaseOrder


# ---------------------------------------------------------------------------
# OCR Read model
# ---------------------------------------------------------------------------

class ReadWord(BaseModel):
    """A single word extracted by OCR Read."""
    content: str
    confidence: Optional[float] = None


class ReadLine(BaseModel):
    """A line of text extracted by OCR Read."""
    content: str
    words: List[ReadWord] = []


class ReadPage(BaseModel):
    """One page of the document analysed by OCR Read."""
    page_number: int
    width: Optional[float] = None
    height: Optional[float] = None
    unit: Optional[str] = None
    lines: List[ReadLine] = []
    words: List[ReadWord] = []


class ReadResult(BaseModel):
    """Normalized result from Azure Document Intelligence OCR Read."""
    analysis_id: str
    document_type: str = "read"              # always "read"
    source_filename: str = ""
    content: str = ""                        # full extracted text
    pages: List[ReadPage] = []
    languages: List[str] = []                # detected languages (e.g. ["en", "pt"])
    has_handwriting: bool = False             # whether handwritten text was detected
    total_pages: int = 0
    total_words: int = 0
