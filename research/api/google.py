import time

from selenium.webdriver import Keys
from selenium.webdriver.common.by import By

from research.helper.scraper import Scraper


class GoogleScraper:
    def __init__(self):
        self.scraper = Scraper()

    def scrape_google(self, query, limit=10):
        links = []
        driver = self.scraper.init_driver()
        try:
            # Open Google
            # Set up the WebDriver (ensure you have the correct path to your webdriver executable)
            driver.get("https://www.google.com")
            time.sleep(3)
            driver.find_element(By.XPATH, '//*[@id="APjFqb"]').click()
            time.sleep(3)
            # Find the search box and enter the search term
            search_box = driver.find_element(By.NAME, "q")
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)

            # Wait for the results to load
            time.sleep(3)  # This can be adjusted based on your internet speed
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)  # Wait for any additional content to load
            # Get the links from the search results
            results = driver.find_elements(By.XPATH, '//div[@class="yuRUbf"]/div/span/a')
            links = [result.get_attribute('href') for index, result in enumerate(results) if index < limit]
        except Exception as ex:
            print(ex)
            time.sleep(1000)
        finally:
            # Close the WebDriver
            driver.quit()
        return links


# Example usage
if __name__ == '__main__':
    # Provide the path to your ChromeDriver

    # Initialize the Google scraper node
    google_scraper = GoogleScraper('google_scraper_node')

