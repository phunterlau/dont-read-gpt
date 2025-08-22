import requests
from bs4 import BeautifulSoup
import html2text
import re
import json
from urllib.parse import urlparse, parse_qs
from .aikeke_reader import extract_aikeke_content

def wechat_to_markdown(url):
    """
    Load WeChat article, convert to markdown, extract arxiv links and save as JSON.
    
    Args:
        url (str): WeChat article URL (e.g., https://mp.weixin.qq.com/s/YBfzwU1PfQVl9Po0xITJCA)
        
    Returns:
        dict: JSON object containing markdown text and list of arxiv links
    """
    # Extract article ID from URL
    parsed_url = urlparse(url)
    article_id = parsed_url.path.split('/')[-1]
    
    # Configure headers to mimic browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Fetch the article
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Check if it's an 爱可可 article
        if "爱可可" in response.text:
            print(f"[DEBUG] Found 爱可可 article, using aikeke_reader for: {url}")
            result = extract_aikeke_content(url)
            if result:
                print(f"[DEBUG] Extracted {len(result['arxiv_links'])} arxiv links and {len(result['github_links'])} github links")
                print("[DEBUG] ArXiv links:", result['arxiv_links'])
                print("[DEBUG] GitHub links:", result['github_links'])
            return result
            
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
        
        # Create output JSON
        output = {
            'markdown': markdown_text,
            'arxiv_links': arxiv_urls,
            'github_links': github_urls
        }
        
        # Save to file
        output_file = f"{article_id}_output.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
            
        return output
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None
    except Exception as e:
        print(f"Error processing article: {e}")
        return None

if __name__ == "__main__":
    # Example usage
    url = "https://mp.weixin.qq.com/s/Aiz45Zon3fYsu8-yBqeGrg"
    result = wechat_to_markdown(url)
    if result:
        print(f"Successfully processed article")
        print(f"Found {len(result['arxiv_links'])} arxiv links and {len(result['github_links'])} github links")
