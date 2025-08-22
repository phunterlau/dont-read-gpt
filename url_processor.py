import re
import time
import os
from readers.base_reader import BaseReader
from readers.arxiv_reader import ArxivReader
from readers.github_reader import GithubReader, GithubIpynbReader
from readers.huggingface_reader import HuggingfaceReader
# from readers.youtube_reader import YoutubeReader  # Temporarily disabled
from readers.webpage_reader import WebpageReader

def get_url_type_and_reader(url) -> tuple[str, BaseReader]:
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url
    
    # Temporarily disable YouTube functionality
    # youtube_regex = (
    #     r'(https?://)?(www\.)?'
    #     '(youtube|youtu|youtube-nocookie)\.(com|be)/'
    #     '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    huggingface_regex = (r'https?:\/\/huggingface\.co\/([^\/]+\/[^\/]+)')

    if 'github.com' in url and not 'ipynb' in url:
        return 'github', GithubReader()
    elif 'github.com' in url and 'ipynb' in url:
        return 'github_ipynb', GithubIpynbReader()
    elif 'arxiv.org' in url:
        return 'arxiv', ArxivReader()
    elif 'mp.weixin.qq.com' in url:
        return 'wechat', WebpageReader() # Assuming wechat uses general webpage reader
    # elif re.match(youtube_regex, url):
    #     return 'youtube', YoutubeReader()
    elif re.match(huggingface_regex, url):
        return 'huggingface', HuggingfaceReader()
    else:
        return 'general', WebpageReader()

def generate_file_path(url, file_type):
    time_now = time.time()
    
    if file_type == 'github':
        parts = url.split('/')
        username = parts[3]
        repo_name = parts[4]
        file_name = f'github_{username}_{repo_name}'
    elif file_type == 'github_ipynb':
        parts = url.split('/')
        username = parts[3]
        repo_name = parts[4]
        ipynb_file_name = parts[-1].replace('.ipynb', '')
        file_name = f'github_ipynb_{username}_{repo_name}_{ipynb_file_name}_ipynb'
    elif file_type == 'arxiv':
        parts = url.split('/')
        arxiv_id = parts[-1]
        file_name = f'arxiv_{arxiv_id}'
    elif file_type == 'wechat':
        prefix = re.findall('/s/([^/]+)', url)[0]
        file_name = f'{prefix}'
    # elif file_type == 'youtube':
    #     youtube_regex = (
    #         r'(https?://)?(www\.)?'
    #         '(youtube|youtu|youtube-nocookie)\.(com|be)/'
    #         '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    #     youtube_id = re.match(youtube_regex, url).group(6)
    #     file_name = f'youtube_{youtube_id}'
    elif file_type == 'huggingface':
        huggingface_regex = (r'https?:\/\/huggingface\.co\/([^\/]+\/[^\/]+)')
        huggingface_id = re.match(huggingface_regex, url).group(1).replace('/', '-')
        file_name = f'huggingface_{huggingface_id}'
    else:
        file_name = re.sub('[^0-9a-zA-Z]+', '', url)
        if len(file_name) > 100:
            file_name = file_name[:100]
            
    file_name += '_' + str(int(time_now)) + '.json'

    date_time = time.localtime(time_now)
    year, month, day = str(date_time.tm_year), str(date_time.tm_mon).zfill(2), str(date_time.tm_mday).zfill(2)
    path = f'saved_text/{year}_{month}_{day}'

    os.makedirs(path, exist_ok=True)

    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url

    return f'{path}/{file_name}', str(int(time_now)), url
