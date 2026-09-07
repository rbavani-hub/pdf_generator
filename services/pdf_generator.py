"""PDF generation from structured meeting data using WeasyPrint."""

import os
from pathlib import Path
from typing import Optional
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML


# Base directory for templates
BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"


class MeetingPDFGenerator:
    """Generates professional PDF documents from meeting data."""

    def __init__(self):
        """Initialize the PDF generator with Jinja2 template loader."""
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=True
        )

    def generate_pdf(
        self,
        meeting_data: dict,
        output_path: str,
        template_name: str = "meeting_report.html"
    ) -> str:
        """
        Generate a PDF from meeting data.

        Args:
            meeting_data: Structured meeting data dictionary
            output_path: Path where the PDF will be saved
            template_name: Name of the HTML template to use

        Returns:
            Path to the generated PDF file
        """
        # Load and render the template
        template = self.env.get_template(template_name)
        html_content = template.render(meeting=meeting_data)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Generate PDF from HTML
        HTML(string=html_content).write_pdf(output_path)

        return output_path

    def generate_pdf_bytes(
        self,
        meeting_data: dict,
        template_name: str = "meeting_report.html"
    ) -> bytes:
        """
        Generate a PDF and return it as bytes (for streaming responses).

        Args:
            meeting_data: Structured meeting data dictionary
            template_name: Name of the HTML template to use

        Returns:
            PDF content as bytes
        """
        template = self.env.get_template(template_name)
        html_content = template.render(meeting=meeting_data)

        return HTML(string=html_content).write_pdf()

    def generate_preview_html(
        self,
        meeting_data: dict,
        template_name: str = "meeting_report.html"
    ) -> str:
        """
        Generate preview HTML without converting to PDF.

        Args:
            meeting_data: Structured meeting data dictionary
            template_name: Name of the HTML template to use

        Returns:
            Rendered HTML string
        """
        template = self.env.get_template(template_name)
        return template.render(meeting=meeting_data)


# Singleton instance
_generator: Optional[MeetingPDFGenerator] = None


def get_pdf_generator() -> MeetingPDFGenerator:
    """Get or create a PDF generator instance."""
    global _generator
    if _generator is None:
        _generator = MeetingPDFGenerator()
    return _generator
