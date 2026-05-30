
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from youtube_transcript_api import YouTubeTranscriptApi

from research.helper.scraper import Scraper

load_dotenv()


class YoutubeScraper:
    def __init__(self, n_links=5):
        self.scraper = Scraper()
        self.n_links = n_links

    def scrape_links(self, query):
        driver = self.scraper.init_driver()
        # Open YouTube
        url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        driver.get(url)

        # Find video elements by XPath or CSS selectors
        video_elements = driver.find_elements(By.XPATH, '//a[@id="video-title"]')[:self.n_links]

        # Extract the URLs
        video_links = []
        for video in video_elements:
            link = video.get_attribute('href')
            if "/shorts/" in link:
                continue
            video_links.append(link)

        driver.quit()

        return video_links

    # Replace 'video_id' with the actual ID of the YouTube video
    def get_transcript(self, video_id: str = 'inPTbZ5YDsI'):
        text = ""

        try:
            # Fetch transcript
            transcript = YouTubeTranscriptApi.get_transcript(video_id)

            # Print the transcript
            for line in transcript:
                text += line['text'] + " "

        except Exception as e:
            print(f"An error occurred: {e}")
        return text


if __name__ == '__main__':
    webhook = YoutubeScraper('youtube_news')
    answer = webhook.process("Crypto news")
    print(answer)
