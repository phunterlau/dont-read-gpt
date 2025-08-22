import os
import re
import requests
import tempfile
from .base_reader import BaseReader

def download_pdf(pdf_url, local_directory):
    """
    Download a PDF from a URL to a local directory.
    """
    pdf_filename = pdf_url.split("/")[-1]
    
    # Ensure filename has .pdf extension
    if not pdf_filename.endswith('.pdf'):
        pdf_filename += '.pdf'
    
    local_file_path = os.path.join(local_directory, pdf_filename)

    response = requests.get(pdf_url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    response.raise_for_status()

    with open(local_file_path, "wb") as f:
        f.write(response.content)

    print(f"PDF downloaded to: {local_file_path}")
    return local_file_path

def extract_text_from_pdf(pdf_path):
    """
    Extract text content from a PDF file using pdfplumber.
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber is required for PDF processing. Install it with: pip install pdfplumber")
    
    text_content = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    # Clean up the text
                    page_text = clean_pdf_text(page_text)
                    text_content.append(f"**Page {page_num}**\n{page_text}")
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    return '\n\n'.join(text_content)

def clean_pdf_text(text):
    """
    Clean up extracted PDF text by removing excessive whitespace and artifacts.
    """
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove weird artifacts common in PDFs
    text = re.sub(r'[^\x00-\x7F]+', '', text)  # Remove non-ASCII characters
    text = re.sub(r'\x0c', '\n', text)  # Replace form feed with newline
    
    # Clean up spacing around punctuation
    text = re.sub(r'\s+([.!?;,])', r'\1', text)
    text = re.sub(r'([.!?])\s*\n\s*', r'\1\n\n', text)  # Better paragraph breaks
    
    # Remove excessive line breaks
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    return text.strip()

def is_pdf_url(url):
    """
    Check if a URL points to a PDF file.
    """
    # Check file extension
    if url.lower().endswith('.pdf'):
        return True
    
    # Check content-type header (for URLs without .pdf extension)
    try:
        response = requests.head(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }, timeout=10)
        content_type = response.headers.get('content-type', '').lower()
        return 'application/pdf' in content_type
    except:
        # If we can't check headers, fall back to URL inspection
        return False

def get_pdf_content(url):
    """
    Download and extract content from a PDF URL.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Download the PDF
            pdf_path = download_pdf(url, temp_dir)
            
            # Extract text content
            content = extract_text_from_pdf(pdf_path)
            
            if not content.strip():
                return "PDF appears to be empty or contains only images/non-text content."
            
            # Add metadata header
            filename = os.path.basename(pdf_path)
            header = f"**PDF Document: {filename}**\n**Source URL:** {url}\n\n"
            
            return header + content
            
        except Exception as e:
            return f"Error processing PDF: {str(e)}"

class PDFReader(BaseReader):
    """
    Reader for extracting content from PDF files via direct URLs.
    """
    
    def read(self, url: str) -> str:
        """
        Read and extract text content from a PDF URL.
        
        Args:
            url: The URL pointing to a PDF file
            
        Returns:
            The extracted text content from the PDF
        """
        return get_pdf_content(url)
