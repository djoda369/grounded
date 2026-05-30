from pydantic import BaseModel, Field

from core.gpt.chatgpt import llm_strict, llm_chat
from core.gpt.history import History


class WebsiteSummary(BaseModel):
    summary: str = Field(..., description="Summary of website content")
    blocked: bool = Field(..., description="Is the content of the website blocked by a security measure?")
    relevant: bool = Field(..., description="Is the content of the website relevant for the question of the user?")


def summarize(scrape_request):
    history = History()
    print(scrape_request)
    history.system(scrape_request["url"] + ": " + scrape_request["text"])
    return llm_strict(history, "gpt-4o", WebsiteSummary)


def summarize_and_answer(query, visited):
    context = History()
    removed = []
    for url in visited:
        scrape_request = visited[url]
        website_summary: WebsiteSummary = summarize(scrape_request)
        if not website_summary.blocked:
            scrape_request["summary"] = website_summary.summary
            if website_summary.relevant:
                context.system(website_summary.summary)
        else:
            removed.append(url)

    for item in removed:
        del visited[item]

    context.system("Summarize answer to question: " + query)
    return llm_chat(context), removed
