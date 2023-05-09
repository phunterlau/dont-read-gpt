from mastodon import Mastodon

# Replace with your own instance URL
instance_url = "your_instance"

# Register the bot
Mastodon.create_app(
    "Knowledge-gpt",
    api_base_url=instance_url,
    to_file="client_secret.txt"
)

# Log in with your bot's account credentials
mastodon = Mastodon(
    client_id="client_secret.txt",
    api_base_url=instance_url
)
email = "YOUR_EMAIL"
password = "YOUR_PASSWORD"
mastodon.log_in(
    email,
    password,
    to_file="user_secret.txt"
)
