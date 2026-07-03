import logging
import os
from typing import Optional, Union, Dict, Any

from jinja2 import Environment, FileSystemLoader, Template

logger = logging.getLogger(__name__)

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    HTML = None
    CSS = None
    WEASYPRINT_AVAILABLE = False


class CustomReportEngine:
    """
    Engine for generating custom PDF reports using WeasyPrint and Jinja2 templates.
    """

    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize the report engine.

        Args:
            template_dir: Optional directory path for Jinja2 templates.
                          If provided, templates can be loaded by name.
        """
        self.env = Environment(loader=FileSystemLoader(template_dir) if template_dir else None)
        self.template_dir = template_dir

    def generate_pdf(
        self,
        template: Union[str, Template],
        context: Dict[str, Any],
        css: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> bytes:
        """
        Generate a PDF from a template and context.

        Args:
            template: Either a template string (HTML), a template name (if template_dir is set),
                      or a compiled Jinja2 Template object.
            context: Dictionary of data to render in the template.
            css: Optional CSS string or file path.
            base_url: Base URL for resolving relative links in the HTML.

        Returns:
            bytes: The generated PDF content.

        Raises:
            RuntimeError: If WeasyPrint is not available.
            TemplateError: If template rendering fails.
        """
        if not WEASYPRINT_AVAILABLE:
            error_msg = "PDF generation requires weasyprint with Pango. Install with: brew install pango (macOS) or apt-get install pango1.0-tools (Linux)"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        # resolve template
        jinja_template = self._resolve_template(template)

        # render HTML
        html_content = jinja_template.render(**context)

        # generate PDF
        try:
            html_obj = HTML(string=html_content, base_url=base_url if base_url else ".")

            stylesheets = []
            if css:
                stylesheets.append(CSS(string=css))

            pdf_bytes = html_obj.write_pdf(stylesheets=stylesheets)
            return pdf_bytes
        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}")
            raise RuntimeError(f"Failed to generate PDF: {e}")

    def _resolve_template(self, template: Union[str, Template]) -> Template:
        """Helper to resolve template input to a Jinja2 Template object."""
        if isinstance(template, Template):
            return template

        if self.template_dir and isinstance(template, str) and os.path.exists(os.path.join(self.template_dir, template)):
            return self.env.get_template(template)

        # Assume it's a raw template string if not found in directory or no directory set
        return self.env.from_string(template)
