from abc import abstractmethod

from analyzer.scrape.scraper import Scraper


def valid_url(href, base_url):
    if not href:
        return

    if "tel:" in href or "#" in href:
        return

    if "javascript" in href:
        return

    if href.endswith(".pdf"):
        return

    if "business.adobe.com" in href:
        return

    if "https://" not in href:
        if base_url.endswith("/"):
            href = base_url[:-1] + href
        else:
            href = base_url + href

        if not href.endswith("/"):
            href += "/"

    if base_url not in href:
        return

    return href.replace("https://www.", "https://")


class RecursiveScraper(Scraper):

    def __init__(self, headless: bool = True, max_depth: int = 5):
        super().__init__(headless=headless, keep_open=True)
        self.max_depth: int = max_depth

    def scrape(self, url):
        url = valid_url(url, url)
        if url:
            return self._subpage_recursive(url, url)

    @abstractmethod
    def _subpage_recursive(self, base_url, current_url, visited=None):
        pass
