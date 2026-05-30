from database.company import Company
from database.connector import company_table, media_table, create_if_not_exists
from database.tools import summarizer
from research.api.instagram import InstagramDownloader


def todo_instagram(status_key):
    company_responses = company_table.all(formula="{" + status_key + "}='Todo'")

    # Initialize an empty list to store companies with valid websites
    companies = []

    # Loop through each response and filter for valid URLs
    for company in company_responses:
        companies.append(Company(company["id"], company["createdTime"], company["fields"]))

    return companies


def record_instagram_media(company: Company):
    scraper = InstagramDownloader()
    scraped_media = scraper.media(company.instagram)

    data = {"URL": "https://instagram.com/" + company.instagram,
            "Content": summarizer(scraped_media),
            "Type": "Social Media",
            "Company": [company.id]}
    create_if_not_exists(media_table, "URL", data["URL"], data)


def process_instagram():
    status_key = "Instagram Scraped"
    companies = todo_instagram(status_key)
    for company in companies:
        company_table.update(company.id, {status_key: "In progress"})
        record_instagram_media(company)
        company_table.update(company.id, {status_key: "Done"})


if __name__ == "__main__":
    process_instagram()
