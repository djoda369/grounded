from pydantic import Field, BaseModel

from analyzer.recursive.scraper import valid_url
from analyzer.review.summary import summarize_and_answer
from analyzer.scrape.website import WebsiteScraper
from channel_finder import is_valid_url
from core.gpt.chatgpt import llm_strict
from core.gpt.history import History


class NextWebsite(BaseModel):
    next_link: str = Field(..., description="Link that would make the best choice of scraping next.")


class SmartWebsiteScraper(WebsiteScraper):

    def __init__(self, max_requests: int = 3, max_links: int = 10):
        super().__init__()
        self.links = {}
        self.max_links: int = max_links
        self.max_requests: int = max_requests

    def _process_links(self, requests, visited):
        for request in requests:
            if "url" not in request:
                continue

            url = request["url"]
            if not is_valid_url(url):
                continue

            if url in visited:
                continue

            if url not in self.links:
                self.links[url] = 1
            else:
                self.links[url] += 1

    def visit(self, request):
        if "query" not in request:
            request["error"] = "Query not in request"
            return request

        query = request["query"]

        if "url" not in request:
            request["error"] = "Url not in request"
            return request

        self.links = {}

        url = request["url"]
        url = valid_url(url, url)

        visited = {}
        for index in range(self.max_links + 1):
            visited[url], links = self.scrape({"url": url})

            self._process_links(links, visited)
            url = self._find_relevant_links(query)
            if url:
                del self.links[url]

        request["answer"] = summarize_and_answer(request, visited)
        return request, visited

    def _find_relevant_links(self, query):
        max_index = min(len(self.links), self.max_links)
        top_elements = sorted(self.links.items(), key=lambda x: x[1], reverse=True)[:max_index]
        history = History()
        for link in top_elements:
            history.system(link[0])
        history.system("Which link is most informative to answering the question to: " + query)
        next_website: NextWebsite = llm_strict(history, "gpt-4o", NextWebsite)
        if next_website.next_link not in self.links:
            return top_elements[0][0]
        return next_website.next_link


if __name__ == "__main__":
    scraper = SmartWebsiteScraper()
    request = {"query": "What services does Grounded World provide?", "url": "https://grounded.world"}

    print(scraper.visit(request))
