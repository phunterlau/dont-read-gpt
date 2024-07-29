import github3
import requests

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

# if the link is a github notebook link, we need to get the raw content
def get_github_notebook_content(github_url):
    github_url = github_url.strip()
    raw_url = github_url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
    response = requests.get(raw_url)
    if response.status_code == 200:
        return response.text
    else:
        return None

# convert the notebook content to a list of cells and their types
def parse_notebook(notebook_content):
    notebook_data = json.loads(notebook_content)
    parsed_content = []

    for cell in notebook_data['cells']:
        cell_type = cell['cell_type']
        cell_content = ''.join(cell['source'])
        parsed_content.append({'type': cell_type, 'content': cell_content})

    return parsed_content