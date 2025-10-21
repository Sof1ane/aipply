import io
from typing import Optional


def _try_pypdf2(path: str) -> str:
    try:
        import PyPDF2  # type: ignore
    except Exception:
        return ""
    try:
        text = ""
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                extracted = page.extract_text() or ""
                text += extracted + "\n"
        return text.strip()
    except Exception:
        return ""


def _try_pdfminer(path: str) -> str:
    try:
        from pdfminer.high_level import extract_text  # type: ignore
    except Exception:
        return ""
    try:
        text = extract_text(path) or ""
        return text.strip()
    except Exception:
        return ""


def _try_ocr(path: str, lang: Optional[str]) -> str:
    try:
        from pdf2image import convert_from_path  # type: ignore
        import pytesseract  # type: ignore
    except Exception:
        return ""
    try:
        pages = convert_from_path(path)
        ocr_texts = []
        for img in pages:
            ocr_texts.append(pytesseract.image_to_string(img, lang=lang or 'eng'))
        return "\n".join(ocr_texts).strip()
    except Exception:
        return ""


def extract_pdf_text_any(path: str, ocr_lang: Optional[str] = None) -> str:
    """Try multiple strategies to extract text from a PDF, including OCR fallback.

    Returns best-effort extracted text (may be empty if all strategies fail).
    """
    # 1) PyPDF2 (fast, common)
    text = _try_pypdf2(path)
    if text:
        return text
    # 2) pdfminer.six (handles many vector PDFs)
    text = _try_pdfminer(path)
    if text:
        return text
    # 3) OCR fallback for scanned PDFs
    text = _try_ocr(path, ocr_lang)
    return text


