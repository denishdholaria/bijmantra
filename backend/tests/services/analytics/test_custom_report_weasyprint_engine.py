import os
import pytest
from unittest.mock import MagicMock, patch, mock_open
from jinja2 import Template

from app.modules.genomics.compute.analytics.custom_report_weasyprint_engine import CustomReportEngine

# Mock weasyprint availability for testing
@pytest.fixture
def mock_weasyprint():
    with patch("app.modules.core.services.analytics.custom_report_weasyprint_engine_service.WEASYPRINT_AVAILABLE", True), \
         patch("app.modules.core.services.analytics.custom_report_weasyprint_engine_service.HTML") as MockHTML, \
         patch("app.modules.core.services.analytics.custom_report_weasyprint_engine_service.CSS") as MockCSS:

        mock_html_instance = MagicMock()
        mock_html_instance.write_pdf.return_value = b"%PDF-1.4 mock content"
        MockHTML.return_value = mock_html_instance

        yield MockHTML, MockCSS

@pytest.fixture
def mock_weasyprint_unavailable():
    with patch("app.modules.core.services.analytics.custom_report_weasyprint_engine_service.WEASYPRINT_AVAILABLE", False):
        yield

class TestCustomReportEngine:

    def test_generate_pdf_raw_string(self, mock_weasyprint):
        """Test generating PDF from a raw template string."""
        MockHTML, _ = mock_weasyprint

        engine = CustomReportEngine()
        template_str = "<h1>Hello {{ name }}</h1>"
        context = {"name": "World"}

        pdf_bytes = engine.generate_pdf(template_str, context)

        assert pdf_bytes == b"%PDF-1.4 mock content"

        # Verify HTML was initialized with rendered content
        MockHTML.assert_called_once()
        call_args = MockHTML.call_args
        assert "<h1>Hello World</h1>" in call_args.kwargs['string']

    def test_generate_pdf_template_file(self, mock_weasyprint, tmp_path):
        """Test generating PDF from a template file."""
        MockHTML, _ = mock_weasyprint

        # Create a temporary template file
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "report.html"
        template_file.write_text("<h1>Report for {{ item }}</h1>")

        engine = CustomReportEngine(template_dir=str(template_dir))
        context = {"item": "Q1 2024"}

        pdf_bytes = engine.generate_pdf("report.html", context)

        assert pdf_bytes == b"%PDF-1.4 mock content"

        # Verify HTML was initialized with rendered content
        MockHTML.assert_called_once()
        call_args = MockHTML.call_args
        assert "<h1>Report for Q1 2024</h1>" in call_args.kwargs['string']

    def test_generate_pdf_with_css(self, mock_weasyprint):
        """Test generating PDF with CSS."""
        MockHTML, MockCSS = mock_weasyprint

        engine = CustomReportEngine()
        template_str = "<p>Styled Text</p>"
        css_str = "p { color: red; }"

        engine.generate_pdf(template_str, {}, css=css_str)

        # Verify CSS was initialized
        MockCSS.assert_called_once_with(string=css_str)

        # Verify write_pdf was called with stylesheets
        mock_html_instance = MockHTML.return_value
        mock_html_instance.write_pdf.assert_called_once()
        call_kwargs = mock_html_instance.write_pdf.call_args.kwargs
        assert len(call_kwargs['stylesheets']) == 1

    def test_weasyprint_unavailable(self, mock_weasyprint_unavailable):
        """Test error when WeasyPrint is unavailable."""
        engine = CustomReportEngine()

        with pytest.raises(RuntimeError, match="PDF generation requires weasyprint"):
            engine.generate_pdf("TEMPLATE", {})

    def test_template_rendering_error(self, mock_weasyprint):
        """Test error during template rendering."""
        engine = CustomReportEngine()
        # Invalid jinja2 syntax
        template_str = "Hello {{ name "

        with pytest.raises(Exception): # Jinja2 raises TemplateSyntaxError or similar
            engine.generate_pdf(template_str, {})

    def test_pdf_generation_error(self, mock_weasyprint):
        """Test error during PDF writing."""
        MockHTML, _ = mock_weasyprint
        mock_html_instance = MockHTML.return_value
        mock_html_instance.write_pdf.side_effect = Exception("Write failed")

        engine = CustomReportEngine()

        with pytest.raises(RuntimeError, match="Failed to generate PDF: Write failed"):
            engine.generate_pdf("Hello", {})
