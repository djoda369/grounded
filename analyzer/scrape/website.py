

from bs4 import BeautifulSoup

from analyzer.recursive.scraper import valid_url
from analyzer.scrape.scraper import Scraper
from core.helper.files import process_double_newlines


class WebsiteScraper(Scraper):

    def __init__(self):
        super().__init__(keep_open=True)

    def scrape(self, request: dict):
        if "url" not in request:
            return request, []

        url = request["url"]
        if not valid_url(url, url):
            return request, []

        page_source = self.process(url)
        if page_source is None:
            return request, []

        soup = BeautifulSoup(page_source, 'html.parser')
        request["text"] = process_double_newlines(str(soup.get_text()))
        links = []
        for link in soup.find_all("a"):
            href = link.get('href')
            checked_href = valid_url(href, url)
            if checked_href:
                links.append({"url": checked_href})
        return request, links


class WebsitesScraper(WebsiteScraper):

    def __init__(self):
        super().__init__()

    def scrape(self, scrape_requests: dict):
        visited = scrape_requests["visited"]
        for url in scrape_requests["scrape"]:
            if url not in visited:
                visited[url], _ = super().scrape(scrape_requests["scrape"][url])
        return visited


if __name__ == "__main__":
    scrape_request = {"https://grounded.world": {"url": "https://grounded.world"}}
    scraper = WebsitesScraper()
    print(scraper.scrape(scrape_request))