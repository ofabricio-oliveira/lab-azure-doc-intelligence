"""
Unit tests for app.utils.normalizer
"""

import pytest
from app.utils.normalizer import (
    normalize_date,
    normalize_result,
    normalize_read_result,
    _to_float,
    _get_field_value,
    _currency_code,
    _address_str,
)


# ---------------------------------------------------------------------------
# normalize_date
# ---------------------------------------------------------------------------

class TestNormalizeDate:
    def test_iso_date(self):
        assert normalize_date("2025-03-15") == "2025-03-15"

    def test_us_format(self):
        assert normalize_date("03/15/2025") == "2025-03-15"

    def test_datetime_string(self):
        assert normalize_date("2025-03-15T10:30:00") == "2025-03-15"

    def test_written_date(self):
        assert normalize_date("March 15, 2025") == "2025-03-15"

    def test_none_returns_none(self):
        assert normalize_date(None) is None

    def test_empty_string_returns_none(self):
        assert normalize_date("") is None

    def test_unparseable_returns_original(self):
        assert normalize_date("sometime in march") == "sometime in march"

    def test_datetime_object(self):
        from datetime import datetime
        dt = datetime(2025, 6, 1, 14, 30)
        assert normalize_date(dt) == "2025-06-01"


# ---------------------------------------------------------------------------
# _to_float
# ---------------------------------------------------------------------------

class TestToFloat:
    def test_int(self):
        assert _to_float(42) == 42.0

    def test_string_number(self):
        assert _to_float("19.99") == 19.99

    def test_none(self):
        assert _to_float(None) is None

    def test_bad_string(self):
        assert _to_float("abc") is None


# ---------------------------------------------------------------------------
# _get_field_value
# ---------------------------------------------------------------------------

class TestGetFieldValue:
    def test_dict_with_value(self):
        fields = {"Total": {"value": 49.90, "confidence": 0.95}}
        assert _get_field_value(fields, "Total") == 49.90

    def test_fallback_keys(self):
        fields = {"VendorName": {"value": "Contoso"}}
        result = _get_field_value(fields, "MerchantName", "VendorName")
        assert result == "Contoso"

    def test_missing_key(self):
        assert _get_field_value({}, "Missing") is None


# ---------------------------------------------------------------------------
# normalize_result (integration-style with mock data)
# ---------------------------------------------------------------------------

class TestNormalizeResult:
    @pytest.fixture
    def sample_receipt_raw(self):
        return {
            "documents": [
                {
                    "fields": {
                        "MerchantName": {"value": "Contoso Cafe", "confidence": 0.95},
                        "TransactionDate": {"value": "2025-01-20", "confidence": 0.92},
                        "Total": {"value": 15.50, "confidence": 0.98},
                        "TotalTax": {"value": 1.50, "confidence": 0.88},
                        "Items": {
                            "value": [
                                {
                                    "value": {
                                        "Description": {"value": "Cappuccino", "confidence": 0.90},
                                        "Quantity": {"value": 2},
                                        "TotalPrice": {"value": 10.00, "confidence": 0.93},
                                    }
                                },
                                {
                                    "value": {
                                        "Description": {"value": "Muffin", "confidence": 0.85},
                                        "Quantity": {"value": 1},
                                        "TotalPrice": {"value": 4.00, "confidence": 0.91},
                                    }
                                },
                            ]
                        },
                    }
                }
            ]
        }

    def test_basic_extraction(self, sample_receipt_raw):
        result = normalize_result(
            raw=sample_receipt_raw,
            document_type="receipt",
            analysis_id="test123",
            source_filename="receipt.pdf",
        )
        assert result.vendor_name == "Contoso Cafe"
        assert result.document_date == "2025-01-20"
        assert result.total == 15.50
        assert result.tax == 1.50
        assert result.needs_review is False
        assert len(result.items) == 2
        assert result.items[0].description == "Cappuccino"
        assert result.items[0].quantity == 2
        assert result.items[1].description == "Muffin"
        assert result.source_filename == "receipt.pdf"

    def test_needs_review_no_total(self, sample_receipt_raw):
        del sample_receipt_raw["documents"][0]["fields"]["Total"]
        result = normalize_result(
            raw=sample_receipt_raw,
            document_type="receipt",
            analysis_id="test456",
            source_filename="receipt.pdf",
        )
        assert result.needs_review is True

    def test_needs_review_no_date(self, sample_receipt_raw):
        del sample_receipt_raw["documents"][0]["fields"]["TransactionDate"]
        result = normalize_result(
            raw=sample_receipt_raw,
            document_type="receipt",
            analysis_id="test789",
            source_filename="receipt.pdf",
        )
        assert result.needs_review is True

    def test_empty_documents(self):
        result = normalize_result(
            raw={"documents": []},
            document_type="invoice",
            analysis_id="empty001",
            source_filename="empty.pdf",
        )
        assert result.needs_review is True
        assert result.vendor_name is None

    def test_confidence_score_computed(self, sample_receipt_raw):
        result = normalize_result(
            raw=sample_receipt_raw,
            document_type="receipt",
            analysis_id="conf001",
            source_filename="receipt.pdf",
        )
        assert result.confidence_score is not None
        assert 0 < result.confidence_score <= 1.0


# ---------------------------------------------------------------------------
# _to_float — valueCurrency dict support
# ---------------------------------------------------------------------------

class TestToFloatCurrencyDict:
    def test_value_currency_dict(self):
        assert _to_float({"amount": 13.5, "currencyCode": "USD"}) == 13.5

    def test_value_currency_dict_zero(self):
        assert _to_float({"amount": 0, "currencyCode": "USD"}) == 0.0

    def test_value_currency_dict_no_amount(self):
        assert _to_float({"currencyCode": "USD"}) is None


# ---------------------------------------------------------------------------
# _currency_code
# ---------------------------------------------------------------------------

class TestCurrencyCode:
    def test_dict_with_code(self):
        assert _currency_code({"amount": 13.5, "currencyCode": "USD"}) == "USD"

    def test_dict_symbol_fallback(self):
        assert _currency_code({"amount": 13.5, "currencySymbol": "$"}) == "$"

    def test_string_passthrough(self):
        assert _currency_code("BRL") == "BRL"

    def test_none(self):
        assert _currency_code(None) is None


# ---------------------------------------------------------------------------
# _address_str
# ---------------------------------------------------------------------------

class TestAddressStr:
    def test_dict_to_string(self):
        addr = {
            "streetAddress": "123 Main St",
            "city": "Seattle",
            "state": "WA",
            "postalCode": "98101",
        }
        result = _address_str(addr)
        assert "123 Main St" in result
        assert "Seattle" in result
        assert "WA" in result

    def test_string_passthrough(self):
        assert _address_str("123 Main St, Seattle") == "123 Main St, Seattle"

    def test_none(self):
        assert _address_str(None) is None


# ---------------------------------------------------------------------------
# _get_field_value — Azure DI 2024-11-30 format
# ---------------------------------------------------------------------------

class TestGetFieldValueNewFormat:
    def test_value_string(self):
        fields = {"MerchantName": {"type": "string", "valueString": "CONTOSO CAFE", "confidence": 0.978}}
        assert _get_field_value(fields, "MerchantName") == "CONTOSO CAFE"

    def test_value_currency(self):
        fields = {"Total": {"type": "currency", "valueCurrency": {"amount": 13.5, "currencyCode": "USD"}, "confidence": 0.988}}
        result = _get_field_value(fields, "Total")
        assert result == {"amount": 13.5, "currencyCode": "USD"}

    def test_value_date(self):
        fields = {"TransactionDate": {"type": "date", "valueDate": "2025-01-20", "confidence": 0.995}}
        assert _get_field_value(fields, "TransactionDate") == "2025-01-20"

    def test_value_time(self):
        fields = {"TransactionTime": {"type": "time", "valueTime": "14:32:00", "confidence": 0.995}}
        assert _get_field_value(fields, "TransactionTime") == "14:32:00"

    def test_value_address(self):
        fields = {
            "MerchantAddress": {
                "type": "address",
                "valueAddress": {"streetAddress": "123 Main St", "city": "Seattle", "state": "WA", "postalCode": "98101"},
                "confidence": 0.987,
            }
        }
        result = _get_field_value(fields, "MerchantAddress")
        assert isinstance(result, dict)
        assert result["city"] == "Seattle"

    def test_content_fallback(self):
        fields = {"SomeField": {"content": "raw text", "confidence": 0.5}}
        assert _get_field_value(fields, "SomeField") == "raw text"


# ---------------------------------------------------------------------------
# normalize_result — Azure DI 2024-11-30 format (integration)
# ---------------------------------------------------------------------------

class TestNormalizeResultNewFormat:
    @pytest.fixture
    def sample_receipt_2024(self):
        """Receipt payload in Azure DI 2024-11-30 format."""
        return {
            "documents": [
                {
                    "fields": {
                        "MerchantName": {"type": "string", "valueString": "CONTOSO CAFE", "confidence": 0.978},
                        "MerchantAddress": {
                            "type": "address",
                            "valueAddress": {"streetAddress": "123 Main St", "city": "Seattle", "state": "WA", "postalCode": "98101"},
                            "content": "123 Main St\nSeattle, WA 98101",
                            "confidence": 0.987,
                        },
                        "TransactionDate": {"type": "date", "valueDate": "2025-01-20", "confidence": 0.995},
                        "TransactionTime": {"type": "time", "valueTime": "14:32:00", "confidence": 0.995},
                        "Subtotal": {"type": "currency", "valueCurrency": {"amount": 12.5, "currencyCode": "USD"}, "confidence": 0.97},
                        "TotalTax": {"type": "currency", "valueCurrency": {"amount": 1.0, "currencyCode": "USD"}, "confidence": 0.95},
                        "Total": {"type": "currency", "valueCurrency": {"amount": 13.5, "currencyCode": "USD"}, "confidence": 0.988},
                        "Items": {
                            "type": "array",
                            "valueArray": [
                                {
                                    "type": "object",
                                    "valueObject": {
                                        "Description": {"type": "string", "valueString": "Cappuccino", "confidence": 0.90},
                                        "Quantity": {"type": "number", "valueNumber": 2, "confidence": 0.88},
                                        "TotalPrice": {"type": "currency", "valueCurrency": {"amount": 10.0, "currencyCode": "USD"}, "confidence": 0.93},
                                    },
                                },
                                {
                                    "type": "object",
                                    "valueObject": {
                                        "Description": {"type": "string", "valueString": "Muffin", "confidence": 0.85},
                                        "Quantity": {"type": "number", "valueNumber": 1, "confidence": 0.87},
                                        "TotalPrice": {"type": "currency", "valueCurrency": {"amount": 3.5, "currencyCode": "USD"}, "confidence": 0.91},
                                    },
                                },
                            ],
                        },
                    }
                }
            ]
        }

    def test_monetary_fields_extracted(self, sample_receipt_2024):
        result = normalize_result(
            raw=sample_receipt_2024,
            document_type="receipt",
            analysis_id="new001",
            source_filename="receipt.pdf",
        )
        assert result.total == 13.5
        assert result.subtotal == 12.5
        assert result.tax == 1.0

    def test_currency_extracted_from_monetary(self, sample_receipt_2024):
        result = normalize_result(
            raw=sample_receipt_2024,
            document_type="receipt",
            analysis_id="new002",
            source_filename="receipt.pdf",
        )
        assert result.currency == "USD"

    def test_vendor_address_formatted(self, sample_receipt_2024):
        result = normalize_result(
            raw=sample_receipt_2024,
            document_type="receipt",
            analysis_id="new003",
            source_filename="receipt.pdf",
        )
        assert result.vendor_address is not None
        assert "Seattle" in result.vendor_address
        assert "WA" in result.vendor_address

    def test_string_fields_extracted(self, sample_receipt_2024):
        result = normalize_result(
            raw=sample_receipt_2024,
            document_type="receipt",
            analysis_id="new004",
            source_filename="receipt.pdf",
        )
        assert result.vendor_name == "CONTOSO CAFE"
        assert result.document_date == "2025-01-20"
        assert result.transaction_time == "14:32:00"

    def test_items_extracted_from_value_array(self, sample_receipt_2024):
        result = normalize_result(
            raw=sample_receipt_2024,
            document_type="receipt",
            analysis_id="new005",
            source_filename="receipt.pdf",
        )
        assert len(result.items) == 2
        assert result.items[0].description == "Cappuccino"
        assert result.items[0].quantity == 2.0
        assert result.items[0].amount == 10.0
        assert result.items[1].description == "Muffin"

    def test_needs_review_false_when_total_and_date(self, sample_receipt_2024):
        result = normalize_result(
            raw=sample_receipt_2024,
            document_type="receipt",
            analysis_id="new006",
            source_filename="receipt.pdf",
        )
        assert result.needs_review is False


# ---------------------------------------------------------------------------
# OCR Read — normalize_read_result
# ---------------------------------------------------------------------------

class TestNormalizeReadResult:
    """Tests for prebuilt-read (OCR) normalisation."""

    @pytest.fixture
    def sample_read_raw(self):
        """Simulates the JSON returned by prebuilt-read for a 2-page document."""
        return {
            "content": "Hello World\nSecond line on page 1\nPage two content",
            "pages": [
                {
                    "pageNumber": 1,
                    "width": 8.5,
                    "height": 11.0,
                    "unit": "inch",
                    "lines": [
                        {"content": "Hello World"},
                        {"content": "Second line on page 1"},
                    ],
                    "words": [
                        {"content": "Hello", "confidence": 0.99},
                        {"content": "World", "confidence": 0.98},
                        {"content": "Second", "confidence": 0.97},
                        {"content": "line", "confidence": 0.96},
                        {"content": "on", "confidence": 0.95},
                        {"content": "page", "confidence": 0.94},
                        {"content": "1", "confidence": 0.93},
                    ],
                },
                {
                    "pageNumber": 2,
                    "width": 8.5,
                    "height": 11.0,
                    "unit": "inch",
                    "lines": [
                        {"content": "Page two content"},
                    ],
                    "words": [
                        {"content": "Page", "confidence": 0.99},
                        {"content": "two", "confidence": 0.97},
                        {"content": "content", "confidence": 0.96},
                    ],
                },
            ],
            "languages": [
                {"locale": "en"},
            ],
            "styles": [],
        }

    def test_basic_fields(self, sample_read_raw):
        result = normalize_read_result(
            raw=sample_read_raw,
            analysis_id="read001",
            source_filename="doc.pdf",
        )
        assert result.analysis_id == "read001"
        assert result.document_type == "read"
        assert result.source_filename == "doc.pdf"

    def test_full_content(self, sample_read_raw):
        result = normalize_read_result(
            raw=sample_read_raw,
            analysis_id="read002",
            source_filename="doc.pdf",
        )
        assert "Hello World" in result.content
        assert "Page two content" in result.content

    def test_total_pages(self, sample_read_raw):
        result = normalize_read_result(
            raw=sample_read_raw,
            analysis_id="read003",
            source_filename="doc.pdf",
        )
        assert result.total_pages == 2

    def test_total_words(self, sample_read_raw):
        result = normalize_read_result(
            raw=sample_read_raw,
            analysis_id="read004",
            source_filename="doc.pdf",
        )
        assert result.total_words == 10  # 7 on page 1 + 3 on page 2

    def test_page_dimensions(self, sample_read_raw):
        result = normalize_read_result(
            raw=sample_read_raw,
            analysis_id="read005",
            source_filename="doc.pdf",
        )
        page1 = result.pages[0]
        assert page1.page_number == 1
        assert page1.width == 8.5
        assert page1.height == 11.0
        assert page1.unit == "inch"

    def test_page_lines(self, sample_read_raw):
        result = normalize_read_result(
            raw=sample_read_raw,
            analysis_id="read006",
            source_filename="doc.pdf",
        )
        assert len(result.pages[0].lines) == 2
        assert result.pages[0].lines[0].content == "Hello World"
        assert len(result.pages[1].lines) == 1

    def test_page_words_with_confidence(self, sample_read_raw):
        result = normalize_read_result(
            raw=sample_read_raw,
            analysis_id="read007",
            source_filename="doc.pdf",
        )
        words = result.pages[0].words
        assert len(words) == 7
        assert words[0].content == "Hello"
        assert words[0].confidence == 0.99

    def test_languages_detected(self, sample_read_raw):
        result = normalize_read_result(
            raw=sample_read_raw,
            analysis_id="read008",
            source_filename="doc.pdf",
        )
        assert result.languages == ["en"]

    def test_no_handwriting(self, sample_read_raw):
        result = normalize_read_result(
            raw=sample_read_raw,
            analysis_id="read009",
            source_filename="doc.pdf",
        )
        assert result.has_handwriting is False

    def test_handwriting_detected(self, sample_read_raw):
        sample_read_raw["styles"] = [{"isHandwritten": True, "spans": []}]
        result = normalize_read_result(
            raw=sample_read_raw,
            analysis_id="read010",
            source_filename="doc.pdf",
        )
        assert result.has_handwriting is True

    def test_empty_document(self):
        result = normalize_read_result(
            raw={},
            analysis_id="read011",
            source_filename="blank.pdf",
        )
        assert result.content == ""
        assert result.total_pages == 0
        assert result.total_words == 0
        assert result.pages == []
        assert result.languages == []

    def test_multiple_languages(self):
        raw = {
            "content": "Hello Olá",
            "pages": [],
            "languages": [
                {"locale": "en"},
                {"locale": "pt"},
            ],
            "styles": [],
        }
        result = normalize_read_result(
            raw=raw,
            analysis_id="read012",
            source_filename="multi.pdf",
        )
        assert result.languages == ["en", "pt"]

    def test_no_duplicate_languages(self):
        raw = {
            "content": "Hello",
            "pages": [],
            "languages": [
                {"locale": "en"},
                {"locale": "en"},
            ],
            "styles": [],
        }
        result = normalize_read_result(
            raw=raw,
            analysis_id="read013",
            source_filename="dup.pdf",
        )
        assert result.languages == ["en"]
