from pydantic import BaseModel

from core.gpt.chatgpt import llm_chat, llm_strict
from core.gpt.history import History


class SummarizedModel(BaseModel):
    summary: str
    exception_reason: str


def summarize(text):
    history = History()
    history.system(text)
    history.user("Summarize the text above:")
    return llm_chat(history)


def summarizer(text_items):
    history = History()
    for key, value in text_items.items():
        history.system(value)
    history.user("Summarize the text above:")
    return llm_strict(history, "gpt-4o", SummarizedModel)


if __name__ == "__main__":
    test = {"aaa": ""}
    print(summarizer(test))



