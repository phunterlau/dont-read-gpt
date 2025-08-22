from .base_reader import BaseReader
import github3
import requests
import json

class GithubReader(BaseReader):
    def read(self, url: str) -> str:
        if url.endswith('/'):
            url = url[:-1]
        if url.endswith('.git'):
            url = url[:-4]
        parts = url.split('/')
        username = parts[3]
        repo_name = parts[4]
        
        gh = github3.GitHub()
        repo = gh.repository(username, repo_name)

        if 'blob' in parts:
            # It's a file
            branch_index = parts.index('blob') + 1
            branch_name = parts[branch_index]
            file_path = '/'.join(parts[branch_index+1:])
            file_contents = repo.file_contents(file_path, ref=branch_name)
            return file_contents.decoded.decode('utf-8')
        else:
            # It's a repository, get the README
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
            
            return content

class GithubIpynbReader(BaseReader):
    def read(self, url: str) -> dict:
        raw_url = url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
        response = requests.get(raw_url)
        if response.status_code == 200:
            notebook_content = response.text
            notebook_data = json.loads(notebook_content)
            parsed_content = []

            for cell in notebook_data['cells']:
                cell_type = cell['cell_type']
                cell_content = ''.join(cell['source'])
                parsed_content.append({'type': cell_type, 'content': cell_content})

            return {"cells": parsed_content}
        else:
            return None
