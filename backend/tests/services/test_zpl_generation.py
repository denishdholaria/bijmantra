import pytest
from app.services.label_printing import generate_zpl_label, label_printing_service

def test_generate_zpl_basic():
    """Test basic ZPL generation."""
    template = {
        "id": "test",
        "width_mm": 50.8,
        "height_mm": 25.4,
        "fields": ["field1", "field2"],
        "barcode_type": "qr"
    }
    data = {
        "field1": "Value1",
        "field2": "Value2"
    }

    zpl = generate_zpl_label(template, data)

    assert "^XA" in zpl
    assert "^XZ" in zpl
    # 50.8 * 8 = 406.4 -> 406
    assert "^PW406" in zpl
    # 25.4 * 8 = 203.2 -> 203
    assert "^LL203" in zpl
    assert "field1: Value1" in zpl
    assert "field2: Value2" in zpl

def test_generate_zpl_barcodes():
    """Test ZPL generation with different barcodes."""
    data = {"barcode": "12345"}

    # QR Code
    template_qr = {
        "width_mm": 50, "height_mm": 25,
        "fields": ["barcode"],
        "barcode_type": "qr"
    }
    zpl_qr = generate_zpl_label(template_qr, data)
    assert "^BQN" in zpl_qr
    assert "FDQA,12345" in zpl_qr

    # Code 128
    template_128 = {
        "width_mm": 50, "height_mm": 25,
        "fields": ["barcode"],
        "barcode_type": "code128"
    }
    zpl_128 = generate_zpl_label(template_128, data)
    assert "^BCN" in zpl_128
    assert "^FD12345" in zpl_128

    # DataMatrix
    template_dm = {
        "width_mm": 50, "height_mm": 25,
        "fields": ["barcode"],
        "barcode_type": "datamatrix"
    }
    zpl_dm = generate_zpl_label(template_dm, data)
    assert "^BXN" in zpl_dm
    assert "^FD12345" in zpl_dm

def test_service_generate_label():
    """Test generating label via service."""
    # Use an existing template from DEFAULT_TEMPLATES
    # plot-standard has fields: ["plot_id", "germplasm", "rep", "barcode"] and type qr
    data = {
        "plot_id": "P001",
        "germplasm": "Wheat-1",
        "rep": "1",
        "barcode": "BARCODE123"
    }

    zpl = label_printing_service.generate_label("plot-standard", data)

    assert zpl is not None
    assert "^XA" in zpl
    assert "plot_id: P001" in zpl
    assert "germplasm: Wheat-1" in zpl
    assert "FDQA,BARCODE123" in zpl

def test_service_generate_label_not_found():
    """Test generating label for non-existent template."""
    zpl = label_printing_service.generate_label("non-existent", {})
    assert zpl is None
