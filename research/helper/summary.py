from core.helper.chatgpt import llm_chat
from core.helper.history import History


def summarize_texts(texts=None):
    history = History()
    for text in texts:
        history.system(text)
    history.system("Summarize the above texts into 3 paragraphs:")
    return llm_chat(history)


def insights_summary(summary: str):
    history = History()
    history.system("Summary: " + summary)
    history.system("Generate three insights from the Summary:")
    return llm_chat(history)


if __name__ == "__main__":
    texts = []
    summarize_texts()
