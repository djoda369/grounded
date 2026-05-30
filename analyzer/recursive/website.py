from bs4 import BeautifulSoup

from analyzer.recursive.scraper import RecursiveScraper, valid_url
from core.helper.files import process_double_newlines


class RecursiveWebsiteScraper(RecursiveScraper):

    def __init__(self, headless: bool = True, max_depth: int = 5):
        super().__init__(headless=headless, max_depth=max_depth)

    def _subpage_recursive(self, base_url, current_url, visited=None):

        if visited is None:
            visited = {}

        try:
            page_source = self.process(current_url)

            soup = BeautifulSoup(page_source, 'html.parser')
            text = process_double_newlines(str(soup.get_text()))
            visited[current_url] = text
            hrefs = [link.get('href') for link in soup.find_all('a')]

            for href in hrefs:
                url = valid_url(href, base_url)
                if not url:
                    continue

                if url not in visited and len(visited) < self.max_depth:
                    visited = self._subpage_recursive(base_url, url, visited)

        except Exception as e:
            print(f"An error occurred: {e}")

        return visited


if __name__ == "__main__":
    scraper = RecursiveWebsiteScraper()
    print(scraper.scrape("https://grounded.world/"))