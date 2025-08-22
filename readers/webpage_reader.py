from .base_reader import BaseReader
import requests
from bs4 import BeautifulSoup

class WebpageReader(BaseReader):
    def read(self, url: str) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

        response = requests.get(url,headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style tags
        for script in soup(["script", "style"]):
            script.extract()
        
        # Get the text content of the page
        text = soup.get_text()
        
        # Remove leading/trailing whitespace and multiple newlines
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text