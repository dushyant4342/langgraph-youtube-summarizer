# 🕸️ Graph Overview

START
  ↓
[FetchTranscript]
  ↓
[ChunkTranscript]
  ↓
[SummarizeChunks] ⇄ [CheckChunkSummaryDone?]
  ↓
[MergeSummaries]
  ↓
[RefineSummary]
  ↓
END


| Node Name                  | Description                                                      |
| -------------------------- | ---------------------------------------------------------------- |
| **FetchTranscript**        | Uses YouTube Transcript API to fetch raw transcript text.        |
| **ChunkTranscript**        | Splits transcript into \~500–1000 token chunks.                  |
| **SummarizeChunks**        | Summarizes each chunk using Gemini API (LLM call per chunk).     |
| **CheckChunkSummaryDone?** | Checks if all chunks have been processed; loops back otherwise.  |
| **MergeSummaries**         | Combines all chunk summaries into a single intermediate summary. |
| **RefineSummary**          | Final polishing step (TL;DR / bullet points / highlights).       |


| From                   | To                     | Condition          |
| ---------------------- | ---------------------- | ------------------ |
| Start                  | FetchTranscript        | Always             |
| FetchTranscript        | ChunkTranscript        | Success            |
| ChunkTranscript        | SummarizeChunks        | Always             |
| SummarizeChunks        | CheckChunkSummaryDone? | Always             |
| CheckChunkSummaryDone? | SummarizeChunks        | If chunks remain   |
| CheckChunkSummaryDone? | MergeSummaries         | If all chunks done |
| MergeSummaries         | RefineSummary          | Always             |
| RefineSummary          | End                    | Always             |


