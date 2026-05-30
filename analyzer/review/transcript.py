from pydantic import BaseModel, Field

from core.gpt.chatgpt import llm_strict
from core.gpt.history import History


class TranscriptModel(BaseModel):
    summary: str = Field(..., description="Summary of transcript")


def summarize_transcript_chunks(transcript: str, chunks: int):
    n = len(transcript)
    z = int(n / chunks)
    summary = ""
    for i in range(chunks):
        segment = transcript[i * z:(i + 1) * z]
        summary += summarize_transcript(segment)
    return summary


def summarize_transcript(transcript: str):
    history = History()
    history.system(transcript)
    return llm_strict(history, "gpt-4o", TranscriptModel)
