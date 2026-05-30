from core.gpt.chatgpt import llm_chat
from core.gpt.history import History
from research.website import WebsiteScraper


def scrape_website_text(domain):
    scraper = WebsiteScraper()

    if domain.startswith("http"):
        website_url = domain
    else:
        website_url = "https://" + domain

    return scraper.process(website_url)


def extract_company_industry(domain):
    text = scrape_website_text(domain)

    history = History()
    history.system(text)
    history.system(f"What is the company name of this website? Only return the name of the company:")
    company_name = llm_chat(history)

    history = History()
    history.system(text)
    history.system(f"What is the industry is {company_name} operating in? Only return the name of the industry:")
    industry_answer = llm_chat(history).replace(".", "")
    return company_name, industry_answer


if __name__ == "__main__":
    print(extract_company_industry("buena.com"))
