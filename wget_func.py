from bs4 import BeautifulSoup
import github3
import requests
import os
import re
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound

def get_html_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    response = requests.get(url,headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    content = soup.get_text()

    # Remove all empty lines from the content
    content = '\n'.join([line for line in content.split('\n') if line.strip()])

    return content

def download_arxiv_pdf(arxiv_link, local_directory):
    if arxiv_link.startswith("https://arxiv.org/abs/"):
        pdf_link = arxiv_link.replace("https://arxiv.org/abs/", "https://arxiv.org/pdf/") + ".pdf"
    elif arxiv_link.startswith("https://arxiv.org/pdf/") and arxiv_link.endswith(".pdf"):
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

def get_arxiv_content(url):
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


def extract_video_id(url):
    """
    Extracts the video ID from a YouTube URL.
    """
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')

    youtube_regex_match = re.match(youtube_regex, url)
    if youtube_regex_match:
        return youtube_regex_match.group(6)
    return None

def get_youtube_transcript_content(url):
    video_id = extract_video_id(url)

    if video_id is None:
        return "Video ID not found."

    try:
        # Fetching the transcript
        transcripts_list = YouTubeTranscriptApi.list_transcripts(video_id)

        preferred_languages = ['en', 'zh-Hans', 'zh-Hant']  # English, Simplified Chinese, Traditional Chinese
        transcript = None

        for lang in preferred_languages:
            if lang in [transcript.language_code for transcript in transcripts_list]:
                transcript = transcripts_list.find_transcript([lang])
                break

        if not transcript:
            return "No suitable transcript found."

        # Fetching the actual transcript data
        transcript_data = transcript.fetch()

        # Formatting the transcript text
        formatted_transcript = ', '.join([item['text'] for item in transcript_data])
        return formatted_transcript

    except NoTranscriptFound:
        return "No transcript found for this video."

def if_youtube(url):
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    youtube_regex_match = re.match(youtube_regex, url)
    if youtube_regex_match:
        return True

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
    # Check if the URL is a YouTube video and get the transcript
    elif if_youtube(url):
        return get_youtube_transcript_content(url)
    else:
        # Get the content for the URL as text-only HTML response
        return get_html_content(url)

if __name__ == '__main__':
    # Test the function
    url = "https://www.youtube.com/watch?v=GKr5URJvNDQ&ab_channel=PromptEngineer"
    print(get_youtube_transcript_content(url))
