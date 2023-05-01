# Dont-Read-GPT: A Discord Bot for Summarizing Web Content

Dont-Read-GPT is a Discord bot designed to help you save time by summarizing web content from URLs, ArXiv papers, and GitHub repositories. Instead of saving content that you may never read, let the bot generate a concise summary so you can quickly grasp the key points and insights.

## Features

- Supports summarization of web content from URLs, ArXiv papers, and GitHub repositories
- Uses OpenAI GPT model for generating high-quality summaries
- Easy integration with Discord via the "!wget" command

## Installation

1. Clone the repository:
\```
git clone https://github.com/your_username/dont-read-gpt.git
\```

2. Change to the project directory:
\```
cd dont-read-gpt
\```

3. Install the required dependencies:
\```
pip install -r requirements.txt
\```

4. Set up your OpenAI API key:
\```
export OPENAI_KEY="your_openai_api_key"
\```

5. Set up your Discord bot token:
\```
export DISCORD_BOT_TOKEN="your_discord_bot_token"
\```

6. Run the bot:
\```
python bot.py
\```

## Usage

Invite the Dont-Read-GPT bot to your Discord server and use the following commands:

- `!wget <URL>`: Summarizes the content from the given URL (webpage, ArXiv paper, or GitHub repository)

## Examples

- Summarize a tech blog post:
\```
!wget https://example.com/blog-post
\```

- Summarize an ArXiv paper:
\```
!wget https://arxiv.org/abs/2109.00001
\```

- Summarize a GitHub repository:
\```
!wget https://github.com/your_username/repository
\```

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests to improve the Dont-Read-GPT bot.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
