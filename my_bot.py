import discord
import re
import time
import os
import socket
import json

from ai_func import generate_summary
from wget_func import get_url_content

#client = discord.Client()
intents = discord.Intents.default()
intents.members = True # Enable the privileged members intent

discord_token = os.environ['DISCORD_TOKEN']

client = discord.Client(intents=intents)


def get_file_path(url):
    # Generate the file name based on the URL and the current timestamp
    prefix = ''
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
    file_name += '_' + str(int(time.time())) + '.json'

    # Get the current date and create the directory path
    date_time = time.localtime(time.time())
    year, month, day = str(date_time.tm_year), str(date_time.tm_mon).zfill(2), str(date_time.tm_mday).zfill(2)
    path = f'saved_text/{year}_{month}_{day}'

    # Create the directory if it doesn't exist
    os.makedirs(path, exist_ok=True)

    file_type = prefix
    if not file_type in ('github', 'arxiv'):
        file_type = 'general'
    # Return the file type and file path
    return (file_type, f'{path}/{file_name}')

# save the content into a JSON file
def save_content(file_type, file_path, content, url, summary, keywords):
    # Create a dictionary for the content
    content_dict = {
        'url': url,
        'content': content,
        'summary': summary,
        'keywords': keywords
    }
    # Save the content to a JSON file
    with open(file_path, 'w') as file:
        json.dump(content_dict, file, indent=4)

@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!wget'):
        url = message.content.split(' ', 1)[1] # get the URL from the message content after the command

        # Get the content for the URL
        try:
            content = get_url_content(url)
            # Save the content to a local file
            file_type, file_path = get_file_path(url)
            #with open(file_path, 'w') as file:
            #    file.write(content)
            summary_dict = generate_summary(content, summary_type=file_type)
            save_content(file_type, file_path, content, url, summary_dict['summary'], summary_dict['keywords'])
            await message.channel.send(f'Text content saved to {file_path}\n\n{summary_dict["summary"]}\n\nKeywords: {summary_dict["keywords"]}')
        except socket.gaierror as e:
            print(f'Error downloading URL "{url}": {str(e)}')

if __name__ == '__main__':
    client.run(discord_token)