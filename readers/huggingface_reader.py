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

def get_huggingface_content(url):
    model_html_content = fetch_huggingface_model_page(url)
    if model_html_content:
        model_sections = parse_huggingface_html(model_html_content)
        content = '\n\n'.join([f'**{section_name}**\n{section_content}' for section_name, section_content in model_sections.items()])
        return content
    else:
        return "Hugging Face model page not found."
