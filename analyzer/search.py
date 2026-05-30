from analyzer.review.summary import summarize_and_answer
from analyzer.scrape.google import GoogleScraper
from analyzer.scrape.website import WebsitesScraper
from analyzer.smart.google import SmartGoogler


class Search:
    def __init__(self, google_scraper: GoogleScraper = GoogleScraper()):
        self.google_scraper: GoogleScraper = google_scraper
        self.web_scraper: WebsitesScraper = WebsitesScraper()

    def scrape(self, request):
        search = self.google_scraper.scrape(request)
        print("search", search)
        print("Googled", len(search))
        scrape_request = {"scrape": search, "visited": request["visited"]}
        visited = self.web_scraper.scrape(scrape_request)
        print("Visited", len(visited))
        request["answer"], blocked = summarize_and_answer(request["query"], visited)

        if "blocked" in request:
            del request["blocked"]
        if "visited" in request:
            del request["visited"]

        return request, visited, blocked


class SmartSearch(Search):

    def __init__(self):
        super().__init__(SmartGoogler())


# Example usage
if __name__ == '__main__':
    # Initialize the Google scrape node
    google_scraper = SmartSearch()
    print(google_scraper.scrape({"query": "What makes Grounded World company special?"}))
