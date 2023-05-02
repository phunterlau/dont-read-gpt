from bs4 import BeautifulSoup
import github3
import requests

def get_html_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    content = soup.get_text()

    # Remove all empty lines from the content
    content = '\n'.join([line for line in content.split('\n') if line.strip()])

    return content

def get_arxiv_content(url):
    if '/pdf/' in url:
        # If the URL is a PDF link, construct the corresponding abstract link
        url = url.replace('/pdf/', '/abs/', 1)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('h1', class_='title mathjax').text.strip()
    abstract = soup.find('blockquote', class_='abstract mathjax').text.strip()
    content = f'{title}\n\n{abstract}'

    # Remove all empty lines from the content
    content = '\n'.join([line for line in content.split('\n') if line.strip()])

    return content

def get_github_content(url):
    if url.endswith('/'):
        url = url[:-1]
    if url.endswith('.git'):
        url = url[:-4]
    parts = url.split('/')
    username = parts[3]
    repo_name = parts[4]
    gh = github3.GitHub()
    repo = gh.repository(username, repo_name)

    readme_file = None
    branches = ['master', 'main']
    readme_variants = ['README.md', 'readme.md', 'Readme.md', 'readMe.md', 'README.MD']

    for branch in branches:
        for readme_variant in readme_variants:
            try:
                readme_file = repo.file_contents(readme_variant, ref=branch)
                break
            except github3.exceptions.NotFoundError:
                pass
        if readme_file:
            break

    if readme_file:
        content = readme_file.decoded.decode('utf-8')
    else:
        raise ValueError('README.md not found in GitHub repository')

    # Convert the content to text and remove all empty lines
    lines = content.split('\n')
    content = ''
    for line in lines:
        line = line.strip()
        if line:
            content += line + '\n'

    return content

def get_url_content(url):
    # Check if the URL includes a scheme, and add "https://" by default if not
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url

    # Check if the URL is an arXiv link and get its title and abstract
    if 'arxiv.org/abs/' in url or 'arxiv.org/pdf/' in url:
        return get_arxiv_content(url)
    # Check if the URL is a GitHub repository and get the README file content
    elif 'github.com' in url:
        return get_github_content(url)
    else:
        # Get the content for the URL as text-only HTML response
        return get_html_content(url)
