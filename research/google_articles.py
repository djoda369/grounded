from core.helper.knowledge import load_existing_industries, save_industries
from research.api.google import GoogleScraper
from research.helper.summary import insights_summary
from research.onboarding import scrape_website_text


class GoogleArticles:
    def __init__(self):
        self.google_scraper = GoogleScraper()
        self.industry_data = load_existing_industries()

    def process(self):
        for key, industry in self.industry_data.items():
            links = self.google_scraper.scrape_google("Industry insights for " + key)
            if "google" not in industry:
                industry["google"] = {}

            for link in links:
                if link in industry["google"]:
                    continue
                self.save_link(industry, link)

        save_industries(self.industry_data)

    def save_link(self, industry, link):
        text = scrape_website_text(link)
        insights = insights_summary(text)
        industry["google"][link] = insights
        save_industries(self.industry_data)


# Example usage
if __name__ == '__main__':
    google_scraper = GoogleArticles()
    google_scraper.process()
