import time

from selenium.webdriver import Keys
from selenium.webdriver.common.by import By

from analyzer.scrape.scraper import Scraper
from core.helper.files import process_double_newlines


class GoogleScraper(Scraper):
    def __init__(self, limit: int = 3):
        super().__init__()
        self.limit = limit

    def scrape(self, request: dict):
        if "query" not in request:
            request["error"] = "Query not in request"
            return request

        blocked = []
        if "blocked" in request:
            blocked = request["blocked"]

        search = {}
        driver = self.init_driver()
        try:
            print("Searching on Google")
            driver.get("https://www.google.com")
            time.sleep(3)

            driver.find_element(By.XPATH, '//*[@id="APjFqb"]').click()
            time.sleep(1)

            search_box = driver.find_element(By.NAME, "q")
            search_box.send_keys(request["query"])
            search_box.send_keys(Keys.RETURN)
            time.sleep(3)  # This can be adjusted based on your internet speed

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)  # Wait for any additional content to load

            google_results = driver.find_elements(By.CLASS_NAME, 'N54PNb')
            print(len(google_results))
            for google_result in google_results:
                text = google_result.text
                link = google_result.find_element(By.TAG_NAME, "a").get_property("href")
                text_segments = text.split("\n")
                if link not in search and link not in blocked:
                    search[link] = {"url": link, "title": process_double_newlines(text_segments[0]),
                                    "name": text_segments[1], "description": text_segments[3]}

        except Exception as ex:
            print(ex)
            time.sleep(1000)
        finally:
            # Close the WebDriver
            driver.quit()
        return search


# Example usage
if __name__ == '__main__':
    # Initialize the Google scrape node
    google_scraper = GoogleScraper()
    results = google_scraper.scrape({"query": "Grounded World"})
    print(results)
