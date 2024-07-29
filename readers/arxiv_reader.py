import os
import re
import requests
from bs4 import BeautifulSoup

def download_arxiv_pdf(arxiv_link, local_directory):
    if arxiv_link.startswith("https://arxiv.org/abs/"):
        pdf_link = arxiv_link.replace("https://arxiv.org/abs/", "https://arxiv.org/pdf/") + ".pdf"
    elif arxiv_link.startswith("https://arxiv.org/pdf/"):
        pdf_link = arxiv_link
    else:
        raise ValueError("Invalid arXiv link")

    pdf_filename = pdf_link.split("/")[-1]
    local_file_path = os.path.join(local_directory, pdf_filename)

    response = requests.get(pdf_link)
    response.raise_for_status()

    with open(local_file_path, "wb") as f:
        f.write(response.content)

    print(f"PDF downloaded to: {local_file_path}")

def extract_arxiv_id(url, include_version=False):
    # Patterns for different types of Arxiv URLs
    patterns = [
        r'https://browse\.arxiv\.org/html/(\d{4}\.\d{4,5}v?\d*)',  # HTML version
        r'https://arxiv\.org/abs/(\d{4}\.\d{4,5})',                # Abstract page
        # pdf page may or may not have .pdf extension
        r'https://arxiv\.org/pdf/(\d{4}\.\d{4,5}v?\d*)',           # PDF version new
        r'https://arxiv\.org/pdf/(\d{4}\.\d{4,5}v?\d*)\.pdf'       # PDF version old
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            arxiv_id_full = match.group(1)
            # Extract base Arxiv ID without version if not required
            if not include_version:
                arxiv_id_base = re.match(r'(\d{4}\.\d{4,5})', arxiv_id_full).group(1)
                return arxiv_id_base
            return arxiv_id_full

    return None

def get_arxiv_content_old_version(url):
    if '/pdf/' in url:
        # If the URL is a PDF link, construct the corresponding abstract link
        url = url.replace('/pdf/', '/abs/', 1).replace('.pdf', '', 1)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('h1', class_='title mathjax').text.strip()
    abstract = soup.find('blockquote', class_='abstract mathjax').text.strip()
    content = f'{title}\n\n{abstract}'

    # Remove all empty lines from the content
    content = '\n'.join([line for line in content.split('\n') if line.strip()])

    return content

# arxiv HTML page may have a few patterns, so we need to try multiple URLs
def fetch_arxiv_page(arxiv_id):
    # Define a list of URL patterns to try
    url_patterns = [
        f"https://browse.arxiv.org/html/{arxiv_id}v{{version}}",
        f"https://arxiv.org/html/{arxiv_id}v{{version}}"
    ]
    
    # Try fetching from each URL pattern, iterating through versions if necessary
    for version in range(1, 3):  # Assuming you want to check versions 1 and 2; adjust range as needed
        for pattern in url_patterns:
            url = pattern.format(version=version)
            response = requests.get(url)
            if response.status_code == 200:
                return response.text
    return None  # Return None if none of the URLs work

def remove_latex_equations(text):
    # Pattern to match common LaTeX equation delimiters and commands
    # Adjust the pattern as needed to cover more cases
    pattern = r'\\(?:begin\{[a-z]*\}|end\{[a-z]*\}|[a-zA-Z]+\{.*?\}|[a-zA-Z]+)'
    clean_text = re.sub(pattern, '', text)
    
    # Additional cleanup for orphaned markers or commands
    clean_text = re.sub(r'\\[a-zA-Z]+', '', clean_text)
    clean_text = re.sub(r'\{|\}', '', clean_text)
    
    return clean_text

def remove_complex_latex(text):
    # Attempt to catch complex LaTeX-like expressions by looking for extended patterns
    # This pattern is an attempt to match more complex mathematical expressions
    # Adjust and expand upon these patterns based on observed structures in your text
    patterns = [
        r'\([^\)]*\)',  # Attempt to catch expressions enclosed in parentheses
        r'\[[^\]]*\]',  # Attempt to catch expressions enclosed in brackets
        r'\\[a-zA-Z]+\[[^\]]*\]',  # Catch LaTeX commands that might use brackets
        r'\\[a-zA-Z]+',  # Catch standalone LaTeX commands
        r'\{[^\}]*\}',  # Attempt to catch expressions enclosed in curly braces
        r'[a-zA-Z]\[[^\]]*\]',  # Catch expressions like X[...]
        r'\^[^\s]+',  # Catch superscript expressions
        r'_\{[^\}]*\}',  # Catch subscript expressions
        r'bold_[a-zA-Z]',  # Specific patterns observed in your example
        r'italic_[a-zA-Z]',
        r'fraktur_[a-zA-Z]',
        r'over\^[^\s]+',  # Catch over^ expressions
        r'start_[A-Z]+',  # Catch start_ expressions
        r'end_[A-Z]+'  # Catch end_ expressions
    ]
    
    clean_text = text
    for pattern in patterns:
        clean_text = re.sub(pattern, '', clean_text)
    
    # Additional cleanup for leftover markers or nonsensical sequences
    clean_text = re.sub(r'[\{\}\[\]\(\)]', '', clean_text)  # Remove leftover braces, brackets, parentheses
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()  # Remove extra spaces
    
    return clean_text

def parse_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    sections = {}

    # Function to clean text by removing non-tokenizable characters
    def clean_text(text):
        # Replace non-tokenizable characters with an empty string
        cleaned_text = re.sub(r'[^\x00-\x7F]+', '', text)
        # Remove LaTeX equations
        cleaned_text = remove_latex_equations(cleaned_text)
        # Remove complex LaTeX-like expressions
        cleaned_text = remove_complex_latex(cleaned_text)
        return cleaned_text
    
    # Extract title from <h1>
    title = soup.find('h1')
    if title:
        sections["Title"] = clean_text(title.get_text(strip=True))

    # Extract abstract
    abstract_div = soup.find('div', class_='ltx_abstract')
    if abstract_div:
        abstract = abstract_div.find('p')
        if abstract:
            sections["Abstract"] = clean_text(abstract.get_text(strip=True))

    # Extract sections from <h2>
    for heading in soup.find_all('h2', class_='ltx_title ltx_title_section'):
        # Removing any <span> elements (like section numbers) from the heading
        for span in heading.find_all('span', class_='ltx_tag ltx_tag_section'):
            span.decompose()
        section_name = clean_text(heading.get_text(strip=True))

        # Extracting content under the section
        content = []
        for sibling in heading.find_next_siblings():
            if sibling.name == 'h2':
                break
            content.append(clean_text(sibling.get_text(strip=True)))
        sections[section_name] = ' '.join(content)

    return sections

# new version of get_arxiv_content by including html version
# now we get the ID first, and then construct the html version link
def get_arxiv_content(url):
    arxiv_id = extract_arxiv_id(url)
    if arxiv_id is None:
        return "Arxiv ID not found."
    arxiv_html_content = fetch_arxiv_page(arxiv_id)
    if arxiv_html_content:
        arxiv_sections = parse_html(arxiv_html_content)
        content = '\n\n'.join([f'**{section_name}**\n{section_content}' for section_name, section_content in arxiv_sections.items()])
        return content
    else: # if the html page is not found, we downgrade the old version
        #return "Arxiv page not found."
        print("Arxiv page not found. Downgrading to old version.")
        return get_arxiv_content_old_version(url)
