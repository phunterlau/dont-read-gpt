from mastodon import Mastodon

instance_url = "https://cmm.fyi"

# Log in with the bot's access token
mastodon = Mastodon(
    access_token="user_secret.txt",
    api_base_url=instance_url
)

def post_masotodon(content):
    if not mastodon.account_verify_credentials():
        print("Invalid access token")
        exit(1)
    # Post a toot
    mastodon.toot(content)

if __name__ == "__main__":
    if not mastodon.account_verify_credentials():
        print("Invalid access token")
        exit(1)
    # Post a toot
    mastodon.toot("Hello, Mastodon! I'm a bot!")