"""PDF text extraction utility used by the resume upload endpoint."""

from __future__ import annotations

import io

from pypdf import PdfReader

from app.exceptions.errors import ValidationAppError


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract plain text from an in-memory PDF file.

    Args:
        file_bytes: The raw bytes of the uploaded PDF.

    Returns:
        The concatenated text of every page, separated by newlines.

    Raises:
        ValidationAppError: If the file cannot be parsed as a PDF, or no
            extractable text is found (e.g. a purely scanned/image PDF).
    """

    try:
        reader = PdfReader(io.BytesIO(file_bytes))
    except Exception as exc:  # pypdf raises various low-level errors for corrupt files
        raise ValidationAppError("The uploaded file is not a valid PDF.") from exc

    pages_text = [page.extract_text() or "" for page in reader.pages]
    full_text = "\n".join(pages_text).strip()

    if not full_text:
        raise ValidationAppError(
            "No extractable text was found in the PDF. Scanned/image-only resumes are not supported."
        )

    return full_text
