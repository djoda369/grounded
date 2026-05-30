
from core.helper.knowledge import load_existing_industries, save_industries
from research.api.youtube import YoutubeScraper
from research.helper.summary import insights_summary


class YoutubeNews:
    def __init__(self):
        self.youtube_scraper = YoutubeScraper()
        self.industry_data = load_existing_industries()

    def process(self):
        for key, industry in self.industry_data.items():
            if "youtube" not in industry:
                industry["youtube"] = {}

            query = key + " news insights"
            print("Youtube query", query)
            links = self.youtube_scraper.scrape_links(query)
            for link in links:
                video_id = link.split("?v=")[1]
                if "&" in video_id:
                    video_id = video_id.split("&")[0]
                self.save_link(industry, video_id)

        save_industries(self.industry_data)

    def save_link(self, industry, link):
        print("Processing ", link)
        text = self.youtube_scraper.get_transcript(link)
        insights = insights_summary(text)
        industry["youtube"][link] = insights
        save_industries(self.industry_data)


# Example usage
if __name__ == '__main__':
    youtube_scraper = YoutubeNews()
    youtube_scraper.process()
