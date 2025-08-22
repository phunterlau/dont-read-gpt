from .base_reader import BaseReader
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
import re

class YoutubeReader(BaseReader):
    def read(self, url: str) -> str:
        video_id = self._extract_video_id(url)

        if video_id is None:
            return "Video ID not found."

        try:
            # Priority list: English first, then Chinese variants
            language_priority = ['en', 'en-US', 'en-GB', 'zh-Hans', 'zh-Hant', 'zh', 'zh-CN', 'zh-TW']
            
            # Create API instance
            api = YouTubeTranscriptApi()
            
            # Try to get transcript list for this video
            transcript_list = api.list(video_id)
            
            # First, try to find transcripts in priority order (either manual or generated)
            for lang in language_priority:
                try:
                    # Try to find any transcript (manual or generated) in this language
                    transcript = transcript_list.find_transcript([lang])
                    transcript_data = transcript.fetch()
                    formatted_transcript = ' '.join([item['text'] for item in transcript_data])
                    return formatted_transcript
                except NoTranscriptFound:
                    continue
            
            # If no direct transcripts found, try to get any available transcript and translate to English
            try:
                # Get any available transcript (manual or generated)
                available_transcripts = list(transcript_list)
                if available_transcripts:
                    # Take the first available transcript
                    transcript = available_transcripts[0]
                    
                    # Try to translate to English if it's not already in English
                    if transcript.language_code not in ['en', 'en-US', 'en-GB']:
                        try:
                            # Try to translate to English
                            translated_transcript = transcript.translate('en')
                            transcript_data = translated_transcript.fetch()
                            formatted_transcript = ' '.join([item['text'] for item in transcript_data])
                            return formatted_transcript
                        except Exception as e:
                            # If translation fails, use the original transcript
                            transcript_data = transcript.fetch()
                            formatted_transcript = ' '.join([item['text'] for item in transcript_data])
                            return f"Original language ({transcript.language_code}): {formatted_transcript}"
                    else:
                        # Already in English
                        transcript_data = transcript.fetch()
                        formatted_transcript = ' '.join([item['text'] for item in transcript_data])
                        return formatted_transcript
            except Exception as inner_e:
                return f"Could not process available transcripts: {inner_e}"
            
            return "No suitable transcript found for this video."
            
        except NoTranscriptFound:
            return "No transcript found for this video."
        except Exception as e:
            return f"An error occurred: {e}"

    def _extract_video_id(self, url):
        """
        Extracts the video ID from a YouTube URL.
        """
        # This regex is designed to handle a variety of YouTube URL formats.
        match = re.search(r"(?<=v=)[^&#]+", url) or \
                re.search(r"(?<=be/)[^&#]+", url) or \
                re.search(r"(?<=embed/)[^&#]+", url)
        return match.group(0) if match else None
