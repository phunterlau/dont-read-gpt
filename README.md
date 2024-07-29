# Dont-Read-GPT: A Discord Bot for Summarizing Web Content

Dont-Read-GPT is my Discord bot designed to help me save time by summarizing web content from many knowledge sources like Arxiv. Instead of saving content that I may never read, let the bot generate a concise summary so I can quickly grasp the key points and insights. It currently supports:

* Arxiv
* Huggingface model
* Github
* Youtube
* Reddit
* WeChat Article
* other blogs or article page

On the roadmap: (contribution welcomed!)
* PDF link
* Medium member blog
* Hackernews
* X/Twitter thread

## Features

- Supports summarization of web content from variety of knowledge sources
- Uses OpenAI GPT model for high-quality summaries tailored for each source
- Easy integration with Discord, just send a link and AI does everything else.

## Installation

1. Clone the repository:
```
git clone https://github.com/phunterlau/dont-read-gpt
```

2. Change to the project directory:
```
cd dont-read-gpt
```

3. Install the required dependencies:
```
pip install -r requirements.txt
```

4. Set up your OpenAI API key:
```
export OPENAI_KEY="your_openai_api_key"
```

5. Set up your Discord bot token and other app tokens:
```
export DISCORD_BOT_TOKEN="your_discord_bot_token"
# get Reddit tokens as https://www.reddit.com/prefs/apps
export REDDIT_APP_ID=ohB-FossX6IdBVBiQdGr7g
export REDDIT_APP_SECRET=WiP1CucU3_gLrvIUJKye1mK1x_c0mw
```

6. Run the bot:
```
python my_bot.py
```

## Usage

Invite the Dont-Read-GPT bot to your Discord server and use the following commands:

- `!wget <URL>`: Summarizes the content from the given URL (webpage, ArXiv paper, or GitHub repository)

## Examples

- Summarize a tech blog post:
```
!wget https://toooold.com/2023/04/08/magnificient_underdogs.html
```

- Summarize an ArXiv paper:
```
!wget https://arxiv.org/abs/1706.03762
```

- Summarize a GitHub repository:
```
!wget https://github.com/phunterlau/dont-read-gpt
```

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests to improve the Dont-Read-GPT bot.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
