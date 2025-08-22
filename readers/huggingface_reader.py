import requests
from bs4 import BeautifulSoup

def fetch_huggingface_model_page(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return None

def parse_huggingface_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    sections = {}

    for heading in soup.find_all('h2'):
        heading_text = heading.get_text(strip=True)
        content = []

        for sibling in heading.find_next_siblings():
            if sibling.name == 'h2':
                break
            content.append(sibling.get_text(strip=True))

        sections[heading_text] = ' '.join(content)

    return sections

from .base_reader import BaseReader
from bs4 import BeautifulSoup
import requests

class HuggingfaceReader(BaseReader):
    def read(self, url: str) -> str:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the main content of the page
        main_content = soup.find('div', class_='prose')
        
        if main_content:
            return main_content.get_text()
        else:
            return soup.get_text()
