import time

from selenium.webdriver.common.by import By

from research.helper.scraper import Scraper


class BCorpScraper(Scraper):

    def __init__(self):
        super().__init__()

    def scrape(self, url):
        if self.driver is None:
            self.driver = self.init_driver()
        try:
            self.driver.get(url)
        except:
            return None
        time.sleep(3)  # Wait for the page to load

        elements = self.driver.find_elements(By.CLASS_NAME, "text-xl")
        texts = [element.text for element in elements]

        if not self.keep_open:
            self.close()

        return texts


def check_bcorp_status(company_name: str):
    scraper = BCorpScraper()
    escaped_name = company_name.replace(" ", "%20")
    url = f"https://www.bcorporation.net/en-us/find-a-b-corp/?query={escaped_name}&sortBy=companies-production-en-us"
    texts = scraper.scrape(url)
    print(len(texts), texts)
    scraper.close()
    return company_name in texts


if __name__ == "__main__":
    print(check_bcorp_status("GroundedWorld"))