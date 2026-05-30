import os
import time
from abc import abstractmethod

import rootpath
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from core.helper.files import sanitize_filename
from path import DETECTED_PATH


def website_saver(visited, directory):
    for url, text in visited.items():
        filepath = os.path.join(directory, f"{sanitize_filename(url)}.txt").replace("\\", "/")
        try:
            # Write HTML content to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Webpage saved to: {filepath}")
        except Exception as e:
            print(f"An error occurred: {e}")
        print("done saving text html")


class Scraper:
    def __init__(self, headless=True, keep_open: bool = False):
        self.driver_path = os.path.join(DETECTED_PATH, "core", "util", "chromedriver.exe").replace("\\", "/")
        self.headless = headless
        self.keep_open = keep_open
        self.driver = None

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    def process(self, url):
        """Handle incoming scrape requests."""
        print(f"Received scrape request for URL: {url}")
        if self.driver is None:
            self.driver = self.init_driver()
        try:
            self.driver.get(url)
        except:
            return None

        time.sleep(3)  # Wait for the page to load

        page_source = self.driver.page_source

        if not self.keep_open:
            self.driver.quit()
            self.driver = None

        return page_source

    def init_driver(self):
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--mute-audio")  # Mute audio

        driver = webdriver.Chrome(service=Service(self.driver_path), options=chrome_options)
        driver.implicitly_wait(30)
        return driver

    @abstractmethod
    def scrape(self, urls):
        pass

    def save(self, urls, directory):
        visited = self.scrape(urls)
        if visited is None:
            return
        for url, text in visited.items():
            filepath = os.path.join(directory, f"{sanitize_filename(url)}.txt").replace("\\", "/")
            try:
                # Write HTML content to file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"Webpage saved to: {filepath}")
            except Exception as e:
                print(f"An error occurred: {e}")
            print("done saving text html")
