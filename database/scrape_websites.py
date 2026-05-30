
from database.company import Company
from database.connector import company_table, media_table, create_if_not_exists
from database.tools import summarizer
from research.website import RecursiveWebsiteScraper


def todo_website_companies(status_keyword):
    company_responses = company_table.all(formula="{" + status_keyword + "}='Todo'")

    companies = []
    for company in company_responses:
        companies.append(Company(company["id"], company["createdTime"], company["fields"]))

    return companies


def record_website_media(company: Company):
    recursive_scraper = RecursiveWebsiteScraper()
    scraped_media = recursive_scraper.scrape(company.website)

    data = {"URL": company.website, "Content": summarizer(scraped_media), "Type": "Website", "Company": [company.id]}
    create_if_not_exists(media_table, "URL", data["URL"], data)


def process_websites_companies():
    status_key = "Website Scraped"
    companies = todo_website_companies(status_key)
    for company in companies:
        company_table.update(company.id, {status_key: "In progress"})
        #try:
        record_website_media(company)
        company_table.update(company.id, {status_key: "Done"})
        #except Exception as ex:
        #    print(ex)
        #    company_table.update(company.id, {status_key: "Error"})


if __name__ == "__main__":
    process_websites_companies()
