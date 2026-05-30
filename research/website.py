
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from core.helper.files import process_double_newlines
from research.helper.scraper import Scraper, website_saver


class WebsiteScraper(Scraper):

    def __init__(self, keep_open: bool = False, save_directory: str = None):
        super().__init__(keep_open=keep_open)
        self.save_directory = save_directory

    def scrape(self, url):
        if "business.adobe.com" in url:
            return None
        page_source = self.process(url)
        if page_source is None:
            return None
        soup = BeautifulSoup(page_source, 'html.parser')
        text = process_double_newlines(str(soup.get_text()))
        print("saving", self.save_directory)
        if self.save_directory:
            website_saver({url: text}, self.save_directory)
        return text


class WebsitesScraper(WebsiteScraper):

    def __init__(self, keep_open: bool = False, save_directory: str = None):
        super().__init__(keep_open=keep_open, save_directory=save_directory)

    def scrape(self, urls):
        visited = {}
        for url in urls:
            if "business.adobe.com" in url:
                continue
            page_source = self.process(url)
            if page_source is None:
                continue
            soup = BeautifulSoup(page_source, 'html.parser')
            text = process_double_newlines(str(soup.get_text()))
            visited[url] = text

        if self.save_directory:
            website_saver(visited, self.save_directory)

        return visited


class RecursiveWebsiteScraper(Scraper):

    def __init__(self, headless: bool = True, max_depth: int = 5):
        super().__init__(headless=headless, keep_open=True)
        self.max_depth: int = max_depth

    def scrape(self, url):
        if "business.adobe.com" in url:
            return None
        return self.subpage_recursive(url, url)

    def subpage_recursive(self, base_url, current_url, visited=None):

        if visited is None:
            visited = {}

        try:
            page_source = self.process(current_url)

            soup = BeautifulSoup(page_source, 'html.parser')
            text = process_double_newlines(str(soup.get_text()))
            visited[current_url] = text
            hrefs = [link.get('href') for link in soup.find_all('a')]

            for href in hrefs:
                if not href:
                    continue

                if "tel:" in href:
                    continue

                if "javascript" in href:
                    continue

                if "https://" not in href:
                    if base_url.endswith("/"):
                        href = base_url[:-1] + href
                    else:
                        href = base_url + href

                    if not href.endswith("/"):
                        href += "/"
                if base_url.replace("https://www.", "https://") in href.replace("https://www.", "https://") \
                        and not href.endswith(".pdf") and not "#" in href:
                    subpage_url = urljoin(current_url, href)
                    if subpage_url not in visited:
                        if len(visited) > self.max_depth:
                            break

                        visited = self.subpage_recursive(base_url, subpage_url, visited)

        except Exception as e:
            print(f"An error occurred: {e}")

        return visited
