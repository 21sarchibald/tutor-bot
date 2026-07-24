"""
File: server/services/text_extraction.py
Description: Extracts raw text out of multiple university document file extensions.
"""

import io

from fastapi import UploadFile

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - optional dependency handling
    PdfReader = None

try:
    from docx import Document
except ImportError:  # pragma: no cover - optional dependency handling
    Document = None

class TextExtractionService:
    """
    A service class tracking parsing mechanics for standard educational file assets.
    """

    @staticmethod
    def extract_text(file: UploadFile):
        """
        Main routing function. Inspects file name extensions to trigger correct sub-parsers.
        """
        filename = file.filename.lower()

        try:
            # Siphon the binary byte array out of the network transmission object stream
            file_bytes = file.file.read()

            # Pass the binary variable asset to specialized file type processing systems
            if filename.endswith('.pdf'):
                return TextExtractionService._extract_from_pdf(file_bytes)
            elif filename.endswith('.docx'):
                return TextExtractionService._extract_from_docx(file_bytes)
            elif filename.endswith('.txt'):
                return TextExtractionService._extract_from_txt(file_bytes)
            else:
                return "Error: Unsupported format. Please upload a .pdf, .docx, .txt file."
        
        except Exception as error:
            # Handle reading problems smoothly
            print(f"Extraction Pipeline Failure: {str(error)}")
            return f"Error processing file: {str(error)}"
        
        finally:
            # Re-wind the internal data read pointer back to index position 0 for safety
            file.file.seek(0)

    @staticmethod
    def _extract_from_pdf(file_bytes: bytes):
        """Helper tool parsing characters out of standard Portable Document Format streams."""
        if PdfReader is None:
            return "Error: pypdf is not installed."

        text = ""
        # Transform raw binary numbers into a virtual, readable in-memory file instance
        pdf_stream = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_stream)

        # Scroll through pages one by one to pluck out characters
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    
    @staticmethod
    def _extract_from_docx(file_bytes: bytes):
        """Helper tool parsing sentences out of standard Microsoft Office files."""
        if Document is None:
            return "Error: python-docx is not installed."

        text = ""
        docx_stream = io.BytesIO(file_bytes)
        doc = Document(docx_stream)

        # Loop through every structural text paragraph division
        for paragraph in doc.paragraphs:
            if paragraph.text:
                text += paragraph.text + "\n"
        return text
    
    @staticmethod
    def _extract_from_txt(file_bytes: bytes):
        """Helper tool converting basic text files into standard unicode strings."""
        return file_bytes.decode("utf-8")


def extract_text_from_pdf(file: UploadFile) -> str:
    """Compatibility wrapper for the router and existing callers."""
    return TextExtractionService.extract_text(file)