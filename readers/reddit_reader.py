import praw
import os
import requests

def resolve_reddit_url(short_url):
    # FIXME: This is a temporary solution to resolve the short URL
    # Reddit may block server IP for simple redictions while local laptop was OK
    response = requests.get(short_url, allow_redirects=True)
    return response.url

def extract_submission_id(url):
    parts = url.split('/')
    # Ensure we have a valid submission ID part
    if len(parts) > 6:
        return parts[6]
    else:
        return None

def fetch_reddit_thread_content(thread_url, client_id, client_secret, user_agent):
    # Check if the URL needs to be resolved
    if '/s/' in thread_url:
        final_url = resolve_reddit_url(thread_url)
    else:
        final_url = thread_url

    # Extract the submission ID from the final URL
    submission_id = extract_submission_id(final_url)
    if not submission_id:
        raise ValueError("Invalid Reddit URL or unable to extract submission ID")

    # Initialize the Reddit client
    reddit = praw.Reddit(client_id=client_id,
                         client_secret=client_secret,
                         user_agent=user_agent)

    # Fetch the submission
    submission = reddit.submission(id=submission_id)

    # Extract the main content
    title = submission.title
    selftext = submission.selftext
    comments = []
    submission.comments.replace_more(limit=None)  # To get all comments
    for top_level_comment in submission.comments.list():
        comments.append(top_level_comment.body)

    return {
        'title': title,
        'selftext': selftext,
        #'comments': comments
    }

def get_reddit_content(thread_url):
    # go get them here https://www.reddit.com/prefs/apps
    client_id = os.getenv('REDDIT_APP_ID')
    client_secret = os.getenv('REDDIT_APP_SECRET')
    user_agent = 'dont read GPT client'
    json_content = fetch_reddit_thread_content(thread_url, client_id, client_secret, user_agent)
    content = "##" + json_content['title'] + '\n\n' + json_content['selftext']
    return content


def main():
    thread_url = 'https://www.reddit.com/r/math/s/VPSP8rplcl'  # Example shortened URL
    #thread_url = 'https://www.reddit.com/r/math/comments/19fg9rx/some_perspective_on_alphageometry/'
    test_content = get_reddit_content(thread_url)
    print(test_content)

if __name__ == "__main__":
    main()