import json
import os
import time

import rootpath
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By

from core.util.files import sanitize_filename

from path import DETECTED_PATH
from research.helper.scraper import Scraper


class NewsScraper:
    def __init__(self, headless: bool = True):
        self.scraper = Scraper(headless)

    def scrape(self, query, limit=10):
        links = []
        driver = self.scraper.init_driver()
        try:
            # Open Google
            # Set up the WebDriver (ensure you have the correct path to your webdriver executable)
            driver.get("https://www.news.google.com")
            time.sleep(3)
            # Find the search box and enter the search term
            search_box = driver.find_element(By.CLASS_NAME, "Ax4B8")
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)

            # Wait for the results to load
            time.sleep(3)  # This can be adjusted based on your internet speed
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)  # Wait for any additional content to load
            # Get the links from the search results

            results_page = driver.find_element(By.XPATH, '//*[@id="yDmH0d"]/c-wiz[2]/div/main/div[2]/c-wiz')
            results = results_page.find_elements(By.CLASS_NAME, 'JtKRv')
            links = [{"link": result.get_attribute('href'), "title": result.text, "summary": ""} for index, result in enumerate(results) if index < limit]
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
    search_query = 'conscious capitalism'
    # Initialize the Google scraper node
    links = NewsScraper().scrape('conscious capitalism')
    for link in links:
        print(link)
    # Write the list to a JSON file
    path = os.path.join(DETECTED_PATH, "data", "news", f"{sanitize_filename(search_query)}.json").replace("\\", "/")
    with open(path, "w") as json_file:
        json.dump(links, json_file, indent=4)

    print("JSON file has been created successfully!")