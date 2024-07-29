from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
import re

# updated youtube URL pattern
def if_youtube(url):
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/|youtube\.com/user/[^/]+#p/a/u/1/|youtube\.com/channel/[^/]+/videos|youtube\.com/playlist\?list=|youtube\.com/user/[^/]+#p/c/[^/]+/[^/]+/[^/]+|youtube\.com/user/[^/]+#p/u/[^/]+/[^/]+)'
        '([^&=%\?]{11})')
    youtube_regex_match = re.search(youtube_regex, url)
    if youtube_regex_match:
        return True
    else:
        return False


# updated youtube ID regex pattern 
def extract_video_id(url):
    """
    Extracts the video ID from a YouTube URL.
    """
    youtube_regex_patterns = [
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})',
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?.*v=([^&=%\?]{11}))'
    ]

    for pattern in youtube_regex_patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(6)
    return None

def get_youtube_transcript_content(url):
    video_id = extract_video_id(url)

    if video_id is None:
        return "Video ID not found."

    try:
        # Fetching the transcript
        transcripts_list = YouTubeTranscriptApi.list_transcripts(video_id)

        preferred_languages = ['en', 'en-US', 'zh-Hans', 'zh-Hant']  # English, Simplified Chinese, Traditional Chinese
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

if __name__ == "__main__":
    # Test the function
    #url = "https://www.youtube.com/watch?v=GKr5URJvNDQ&ab_channel=PromptEngineer"
    #url = "https://www.youtube.com/watch?app=desktop&v=AayZuuDDKP0&ab_channel=JointMathematicsMeetings"
    #url = "https://youtu.be/uRya4zRrRx4?si=_9qF6vrqJ3NXJDWv"
    #url = "https://m.youtube.com/watch?v=AayZuuDDKP0"
    #url = "https://m.youtube.com/watch?v=k5Txq5C_AWA&feature=youtu.be"
    url = "https://www.youtube.com/watch?si=wVR1JEjxPuror_8y&v=-fopYsgFdzc&feature=youtu.be"
    print(get_youtube_transcript_content(url))