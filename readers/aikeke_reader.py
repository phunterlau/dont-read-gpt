import requests
from bs4 import BeautifulSoup
import html2text
import re
import json

def extract_aikeke_content(url):
    """
    Extract content from 爱可可 WeChat articles, converting to markdown and extracting arxiv/github links.
    
    Args:
        url (str): WeChat article URL
        
    Returns:
        dict: JSON object containing markdown text and lists of arxiv and github links
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Fetch the article
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the main article content
        article_content = soup.find('div', id='js_content')
        if not article_content:
            raise ValueError("Could not find article content")
            
        # Convert HTML to markdown
        h2t = html2text.HTML2Text()
        h2t.ignore_links = False
        h2t.body_width = 0  # Disable line wrapping
        markdown_text = h2t.handle(str(article_content))
        
        # Extract arxiv links using regex
        arxiv_pattern = r'(?:arxiv\.org/(?:abs|pdf)/|arxiv:)([0-9]+\.[0-9]+)'
        arxiv_links = list(set(re.findall(arxiv_pattern, markdown_text)))
        
        # Create full arxiv URLs for any bare IDs
        arxiv_urls = [
            f"https://arxiv.org/abs/{link}" if not link.startswith('http') else link
            for link in arxiv_links
        ]
        
        # Extract GitHub links using regex
        github_pattern = r'(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9-]+/[a-zA-Z0-9._-]+'
        github_links = list(set(re.findall(github_pattern, markdown_text)))
        
        # Ensure all GitHub links have https://
        github_urls = [
            f"https://{link}" if not link.startswith('http') else link
            for link in github_links
        ]
        
        # Create output dictionary
        output = {
            'markdown': markdown_text,
            'arxiv_links': arxiv_urls,
            'github_links': github_urls
        }
        
        return output
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None
    except Exception as e:
        print(f"Error processing article: {e}")
        return None
