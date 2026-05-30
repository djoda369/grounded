import os

import rootpath
from pydantic import BaseModel, Field

from analyzer.review.summary import summarize_and_answer
from analyzer.search import Search
from analyzer.self_model import add_metadata
from core.gpt.chatgpt import llm_strict
from core.gpt.history import History
from core.vault.json_vault import JSONVault
from path import DETECTED_PATH


class AnswerModel(BaseModel):
    answer: str = Field(..., description="If you can answer the question, return the answer to the question.")
    known: bool = Field(..., description="Answer True is your answer was based on knowledge that was provided in conversation, otherwise return False.")


class CompanyMetadata(BaseModel):
    company_name: str = Field(..., description="Name of the company.")
    description: str = Field(..., description="Description of the company.")
    website: str = Field(..., description="Website url of the company")
    industry: str = Field(..., description="Industry that the company is operating in.")
    country: str = Field(..., description="Country that company is from.")


def initialize_metadata(text):
    history = History()
    history.system(text)
    return llm_strict(history, "gpt-4o", CompanyMetadata).model_dump()


class EmailAnalyzer:

    def __init__(self, id: str):
        self.vault = JSONVault(id, os.path.join(DETECTED_PATH, "data").replace("\\", "/"))
        self.search = Search()
        self.meta = self.vault.get("metadata", None)
        self.requests = self.vault.get("requests", [])
        self.visited = self.vault.get("visited", {})
        self.blocked = self.vault.get("blocked", [])
        self.website = self.vault.get("website", "https://" + self.vault.id.split("@")[1])

    def _add_request(self, request):
        for r in self.requests:
            if request["query"] == r["query"]:
                return
        self.requests.append(request)
        self.vault.set("requests", self.requests)
        self.meta = add_metadata(str(request), self.meta)
        self.vault.set("metadata", self.meta)

    def _add_blocked(self, blocked):
        for item in blocked:
            if item not in self.blocked:
                self.blocked.append(item)
        self.vault.set("blocked", self.blocked)

    def _add_visited(self, visited):
        for visit in visited:
            if visit not in self.visited:
                self.visited[visit] = visited[visit]
        self.vault.set("visited", self.visited)

    def initialize(self):
        if self.meta:
            return
        print("Initializing")
        scrape_request = {"scrape": {self.website: {"url": self.website}}, "visited": self.visited}
        self.visited = self.search.web_scraper.scrape(scrape_request)

        request = {"query": "Summarize the company of " + self.website}
        print("Visited", len(self.visited))
        request["answer"], blocked = summarize_and_answer(request["query"], self.visited)
        text = ""
        for key, value in request.items():
            text = str(key) + ": " + str(value) + "\n"
        self.meta = initialize_metadata(text)
        self._add_request(request)
        self._add_visited(self.visited)
        self._add_blocked(blocked)

    def is_known(self, query):
        history = History()
        if self.meta:
            for key in self.meta:
                history.system(f"{self.vault.id} - {key}: {self.meta[key]}")

        if self.visited:
            for url in self.visited:
                history.system(self.visited[url]["summary"])

        if len(history.logs) <= 3:
            return {"answer": "", "known": False}

        history.user(query)
        return llm_strict(history, "gpt-4o", AnswerModel).model_dump()

    def ask(self, query):
        question = f"{self.vault.id} company: {query}"
        answer_dict: dict = self.is_known(question)
        if answer_dict["known"]:
            self._add_request({"query": question, "answer": answer_dict["answer"]})
            return answer_dict["answer"]
        else:
            print(answer_dict["answer"], answer_dict["known"])
        request, visited, blocked = self.search.scrape({"query": question,
                                                        "blocked": self.blocked, "visited": self.visited})
        self._add_request(request)
        self._add_visited(visited)
        self._add_blocked(blocked)
        return request["answer"]


if __name__ == "__main__":
    email_analyzer = EmailAnalyzer("phil@grounded.world")
    print(email_analyzer.ask("Who is the founder?"))
