import re
import logging
from typing import TypedDict, List
from youtube_transcript_api import YouTubeTranscriptApi

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("YouTubeSummarizer")

# ----------- LangGraph State -----------
class SummaryState(TypedDict):
    video_id: str
    transcript: str
    chunks: List[str]
    chunk_summaries: List[str]
    final_summary: str
    current_index: int

# Extract video ID
def extract_video_id(youtube_url: str) -> str:
    match = re.search(r"(?:v=|/shorts/|youtu\.be/)([a-zA-Z0-9_-]{11})", youtube_url)
    return match.group(1) if match else None

# Fetch transcript
def fetch_transcript(state: SummaryState) -> SummaryState:
    try:
        logger.info("Fetching YouTube transcript...")
        transcript = YouTubeTranscriptApi.get_transcript(state["video_id"])
        state["transcript"] = " ".join([t["text"] for t in transcript])
        if not state["transcript"]:
            raise ValueError("Transcript is empty or unavailable.")
    except Exception as e:
        logger.error(f"Transcript fetch failed: {e}")
        state["transcript"] = ""
    return state

# Run test
if __name__ == "__main__":
    link = "https://www.youtube.com/watch?v=GDa8kZLNhJ4"
    video_id = extract_video_id(link)

    video_id = "GDa8kZLNhJ4"

    state: SummaryState = {
        "video_id": video_id,
        "transcript": "",
        "chunks": [],
        "chunk_summaries": [],
        "final_summary": "",
        "current_index": 0
    }

    state = fetch_transcript(state)
    print("\n🎙️ Transcript Preview:\n")
    print(state["transcript"][:1000])  # Print first 1000 characters
    print("\n🎥 Video ID:", state["video_id"])


