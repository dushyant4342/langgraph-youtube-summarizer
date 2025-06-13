from langgraph.graph import StateGraph, END
from typing import TypedDict, List
import logging
from youtube_transcript_api import YouTubeTranscriptApi
import networkx as nx
import matplotlib.pyplot as plt
from langchain_core.runnables import RunnableLambda


import os
from dotenv import load_dotenv
import requests

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"


import re
def extract_video_id(youtube_url: str) -> str:
    # Works for shorts, watch, etc.
    match = re.search(r"(?:v=|/shorts/|youtu\.be/)([a-zA-Z0-9_-]{11})", youtube_url)
    return match.group(1) if match else None


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

# ----------- Helper functions -----------
# def gemini_summarize(text: str) -> str:
#     return f"Summary of: {text[:50]}..."

def gemini_summarize(text: str) -> str:
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [
            {
                "parts": [{"text": f"Summarize this: {text}"}]
            }
        ]
    }
    
    try:
        res = requests.post(GEMINI_URL, headers=headers, json=body)
        res.raise_for_status()
        response_text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
        return response_text
    except Exception as e:
        print(f"Gemini API failed: {e}")
        return "Error summarizing"


def summarize_chunk(state: SummaryState) -> SummaryState:
    i = state["current_index"]
    chunk = state["chunks"][i]
    summary = gemini_summarize(chunk)
    state["chunk_summaries"].append(summary)
    state["current_index"] += 1
    return state


def gemini_refine(text: str) -> str:
    return f"Refined Summary: {text[:50]}..."


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

def chunk_transcript(state: SummaryState) -> SummaryState:
    logger.info("Chunking transcript...")
    if not state["transcript"].strip():
        raise ValueError("Transcript is empty. Cannot proceed to chunking.")

    state["chunks"] = chunk_text(state["transcript"])
    state["current_index"] = 0
    state["chunk_summaries"] = []
    return state


def chunk_text(text: str, max_tokens=500) -> List[str]:
    words = text.split()
    return [" ".join(words[i:i + max_tokens]) for i in range(0, len(words), max_tokens)]


def check_chunks_done(state: SummaryState) -> str:
    return "done" if state["current_index"] >= len(state["chunks"]) else "next"

def merge_summaries(state: SummaryState) -> SummaryState:
    logger.info("Merging summaries...")
    state["final_summary"] = "\n".join(state["chunk_summaries"])
    return state


def refine_summary(state: SummaryState) -> SummaryState:
    logger.info("Refining with Gemini...")
    prompt = (
        "Improve this summary for clarity and insight. Add bullet points if appropriate:\n\n"
        + state["final_summary"]
    )
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    try:
        res = requests.post(GEMINI_URL, headers=headers, json=body)
        res.raise_for_status()
        refined = res.json()["candidates"][0]["content"]["parts"][0]["text"]
        state["final_summary"] = refined
    except Exception as e:
        logger.error(f"Gemini refine failed: {e}")
        state["final_summary"] += "\n\n(Note: refinement failed)"
    
    return state

# ----------- Build LangGraph -----------


graph = StateGraph(SummaryState)

# ✅ Add all nodes first
graph.add_node("fetch_transcript", fetch_transcript)
graph.add_node("chunk_transcript", chunk_transcript)
graph.add_node("summarize_chunk", summarize_chunk)
graph.add_node("check_chunks_done", check_chunks_done)
graph.add_node("merge_summaries", merge_summaries)
graph.add_node("refine_summary", refine_summary)

# ✅ THEN set entry point
graph.set_entry_point("fetch_transcript")

# Now connect edges
graph.add_edge("fetch_transcript", "chunk_transcript")
graph.add_edge("chunk_transcript", "summarize_chunk")
graph.add_edge("summarize_chunk", "check_chunks_done")

# Wrap condition as RunnableLambda
condition_runnable = RunnableLambda(check_chunks_done)

# Then pass it to the conditional edge handler
graph.add_conditional_edges("check_chunks_done", condition_runnable, {
    "next": "summarize_chunk",
    "done": "merge_summaries"
})


graph.add_edge("merge_summaries", "refine_summary")
graph.add_edge("refine_summary", END)


app = graph.compile()

#link = "https://youtube.com/shorts/93V5s2rEeQw?si=qoo3Ir_RIUebZ0CK"
link = "https://www.youtube.com/watch?v=GDa8kZLNhJ4"

video_id = extract_video_id(link)
print(f'video_id :{video_id}')

# ----------- Run Locally -----------
if __name__ == "__main__":
    

    # Sample run
    initial_state = app.invoke({
        "video_id": video_id,
        "transcript": "",
        "chunks": [],
        "chunk_summaries": [],
        "final_summary": "",
        "current_index": 0
    })

    output = app.invoke(initial_state)
    print("\n📋 FINAL REFINED SUMMARY:\n")
    print(output["final_summary"])


    print("\n--- FINAL SUMMARY ---\n", output["final_summary"])

    # Optional: visualize
    G = nx.DiGraph()
    G.add_edges_from([
        ("fetch_transcript", "chunk_transcript"),
        ("chunk_transcript", "summarize_chunk"),
        ("summarize_chunk", "check_chunks_done"),
        ("check_chunks_done", "summarize_chunk"),
        ("check_chunks_done", "merge_summaries"),
        ("merge_summaries", "refine_summary"),
        ("refine_summary", "END")
    ])
    plt.figure(figsize=(10, 6))
    nx.draw_networkx(G, with_labels=True, node_size=3000, node_color='skyblue', font_size=10)
    plt.title("LangGraph - YouTube Summarizer")
    plt.show()