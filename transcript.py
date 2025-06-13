from youtube_transcript_api import YouTubeTranscriptApi

video_id = "GDa8kZLNhJ4"

try:
    transcripts = YouTubeTranscriptApi.get_transcript(video_id)
    print("✅ Transcripts found. Available languages:")
    for t in transcripts:
        print(f"- {t.language_code}")
except Exception as e:
    print("❌ Transcript listing failed:", e)


from youtube_transcript_api import YouTubeTranscriptApi

import urllib.request

opener = urllib.request.build_opener()
opener.addheaders = [
    ('User-Agent', 'Mozilla/5.0'),
    ('Accept-Language', 'en-US,en;q=0.9'),
]
urllib.request.install_opener(opener)

def fetch_transcript_safe(video_id: str) -> str:
    try:
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript_obj = transcripts.find_transcript(['en'])  # or .find_manually_created_transcript()
        transcript = transcript_obj.fetch()
        full_text = " ".join([entry['text'] for entry in transcript])
        return full_text
    except Exception as e:
        print(f"❌ Full transcript fetch failed: {e}")
        return ""
    

fetch_transcript_safe(video_id)