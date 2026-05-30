import time

from selenium.webdriver.common.by import By

from research.helper.scraper import Scraper


class PlanetPercentScraper(Scraper):

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

        elements = self.driver.find_elements(By.CLASS_NAME, "search-result__title")
        texts = [element.text for element in elements]

        if not self.keep_open:
            self.close()

        return texts


def check_planet_percent(company_name: str):
    scraper = PlanetPercentScraper()
    escaped_name = company_name.replace(" ", "%20").lower()
    url = f"https://directories.onepercentfortheplanet.org/?accountType=business&q={escaped_name}&viewMode=list"
    texts = scraper.scrape(url)
    print(len(texts), texts)
    scraper.close()
    return company_name in texts


if __name__ == "__main__":
    print(check_planet_percent("google"))