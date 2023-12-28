import discord
import re
import time
import os
import socket
import json

from ai_func import generate_summary, extract_keywords_from_summary
from ai_func import summary_to_obsidian_markdown
from ai_func import generate_embedding

from wget_func import get_url_content
from wget_func import download_arxiv_pdf

from mastodon_func import post_masotodon

#client = discord.Client()
intents = discord.Intents.default()
intents.members = True # Enable the privileged members intent

discord_token = os.environ['DISCORD_TOKEN']

client = discord.Client(intents=intents)


def get_file_path(url):
    # Generate the file name based on the URL and the current timestamp
    prefix = ''
    time_now = time.time() 
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url
    if 'github.com' in url:
        prefix = 'github'
        parts = url.split('/')
        username = parts[3]
        repo_name = parts[4]
        file_name = f'{prefix}_{username}_{repo_name}'
    elif 'arxiv.org' in url:
        prefix = 'arxiv'
        parts = url.split('/')
        arxiv_id = parts[-1]
        file_name = f'{prefix}_{arxiv_id}'
    elif 'mp.weixin.qq.com' in url:
        prefix = re.findall('/s/([^/]+)', url)[0]
        file_name = f'{prefix}'
    else:
        file_name = re.sub('[^0-9a-zA-Z]+', '', url)
        if len(file_name) > 100:
            file_name = file_name[:100]
    file_name += '_' + str(int(time_now)) + '.json'

    # Get the current date and create the directory path
    date_time = time.localtime(time_now)
    year, month, day = str(date_time.tm_year), str(date_time.tm_mon).zfill(2), str(date_time.tm_mday).zfill(2)
    path = f'saved_text/{year}_{month}_{day}'

    # Create the directory if it doesn't exist
    os.makedirs(path, exist_ok=True)

    file_type = prefix
    if not file_type in ('github', 'arxiv'):
        file_type = 'general'
    # Return the file type and file path
    return (file_type, f'{path}/{file_name}', str(int(time_now)), url)

# save the content into a JSON file
def save_content(file_type, file_path, timestamp, content, url, summary, keywords, embeddings, obsidian_markdown):
    # Create a dictionary for the content
    content_dict = {
        'url': url,
        'type': file_type, # 'github', 'arxiv', 'general
        'timestamp': timestamp,
        'content': content,
        'summary': summary,
        'keywords': keywords,
        'embeddings': embeddings,
        'obsidian_markdown': obsidian_markdown,
    }
    # Save the content to a JSON file
    with open(file_path, 'w') as file:
        json.dump(content_dict, file, indent=4)

    if file_type == 'arxiv':
        pdf_file_name = file_path.replace('.json', '.pdf')
        download_arxiv_pdf(url, os.path.dirname(pdf_file_name))
    
    # append the metadata above to an index file
    # to support tail function to load the latest content
    with open('saved_text/index.csv', 'a') as index_file:
        index_file.write(f'{file_type},{timestamp},{file_path}\n')

    return 

def post_mastodon_toot(url, summary, keywords):
    # Generate the toot content
    toot_content = f'{url}\n#knowledgeGPT\n{summary}\n\nKeywords: {keywords}\n\n'[:500]
    # Post the toot
    post_masotodon(toot_content)
    return

@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!wget'):
        url = message.content.split(' ', 1)[1] # get the URL from the message content after the command
        post_flag = message.content.split(' ')[-1] # get the post flag from the message content after the command
        # Get the content for the URL
        try:
            content = get_url_content(url)
            # Save the content to a local file
            file_type, file_path, time_now, complete_url = get_file_path(url)
            #with open(file_path, 'w') as file:
            #    file.write(content)
            summary = generate_summary(content, summary_type=file_type)
            keywords = extract_keywords_from_summary(summary)
            embedding = generate_embedding(content)
            obsidian_markdown = summary_to_obsidian_markdown(summary, keywords)
            save_content(file_type=file_type, 
                         file_path=file_path, 
                         timestamp=time_now,
                         content=content, 
                         url=complete_url, 
                         summary=summary, 
                         keywords=keywords, 
                         embeddings=embedding,
                         obsidian_markdown=obsidian_markdown)
            await message.channel.send(f'Saved {complete_url}\n\n{summary}\n\nKeywords: {keywords}'[:2000])
            if not post_flag == 'nopost':
                post_mastodon_toot(complete_url, summary, keywords)
                await message.channel.send(f'Posted to Mastodon')
        except socket.gaierror as e:
            print(f'Error downloading URL "{url}": {str(e)}')

    # tail function to load the latest content
    if message.content.startswith('!tail'):
        # Get the number of lines to load
        num_lines = int(message.content.split(' ', 1)[1])
        # Load the index file
        with open('saved_text/index.csv', 'r') as index_file:
            lines = index_file.readlines()
            # Get the last n lines
            last_lines = lines[-num_lines:]
            # Load the content from the files
            for line in last_lines:
                file_type, timestamp, file_path = line.strip().split(',')
                with open(file_path, 'r') as file:
                    content_dict = json.load(file)
                    # Send the content to the Discord channel
                    await message.channel.send(f'{content_dict["url"]}\n\n{content_dict["summary"]}\n\nKeywords: {content_dict["keywords"]}')
    

if __name__ == '__main__':
    client.run(discord_token)