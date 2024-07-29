from bs4 import BeautifulSoup
import github3
import requests
import os
import re
import json
from readers.reddit_reader import get_reddit_content
from readers.huggingface_reader import get_huggingface_content
from readers.youtube_reader import get_youtube_transcript_content, if_youtube
from readers.github_reader import get_github_content, get_github_notebook_content, parse_notebook
from readers.arxiv_reader import get_arxiv_content
from readers.webpage_reader import get_html_content


def get_url_content(url):
    # Check if the URL includes a scheme, and add "https://" by default if not
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url

    # Check if the URL is an arXiv link and get its title and abstract
    if 'arxiv.org/abs/' in url or 'arxiv.org/pdf/' in url or 'browse.arxiv.org/html/' in url:
        return get_arxiv_content(url)
    # Check if the URL is a GitHub repository and get the README file content
    elif 'github.com' in url and not url.endswith('.ipynb'):
        return get_github_content(url)
    # Check if the URL is a GitHub notebook and get the content
    elif 'github.com' in url and url.endswith('.ipynb'):
        notebook_content = get_github_notebook_content(url)
        notebook_cells = parse_notebook(notebook_content)
        content = '\n\n'.join([f'**{cell["type"]}**\n{cell["content"]}' for cell in notebook_cells])
        return content
    # Check if the URL is a YouTube video and get the transcript
    elif if_youtube(url):
        return get_youtube_transcript_content(url)
    # Check if the URL is a Hugging Face model page and get the content
    elif 'huggingface.co' in url:
        return get_huggingface_content(url)
    # Check if the URL is a Reddit thread and get the content
    elif 'reddit.com' in url:
        return get_reddit_content(url)
    else:
        # Get the content for the URL as text-only HTML response
        return get_html_content(url)

if __name__ == '__main__':
    # Test the function
    url = " https://www.reddit.com/r/math/s/VPSP8rplcl/"
    #print(get_youtube_transcript_content(url))
    print(get_url_content(url))
