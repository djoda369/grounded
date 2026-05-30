from typing import List

from pydantic import BaseModel, Field

from core.helper.chatgpt import llm_strict
from core.helper.history import History
from database.company import Company
from database.connector import create_if_not_exists, company_table
from research.api.google import GoogleScraper
from research.website import WebsitesScraper


class CompetitorModel(BaseModel):
    name: str
    website: str


class CompanyModel(BaseModel):
    name: str
    competitors: List[CompetitorModel]


class AlternativeSearch(BaseModel):
    query: str = Field(..., description="Google Search query for finding alternative competitors for company")


def extract_competitors(visited, company_name):
    history = History()
    for _, value in visited.items():
        history.system(value)
    history.user("What are the top 5 alternatives for " + company_name)
    return llm_strict(history, base_model=CompanyModel)


# run find competitors every month
class InformationDecision(BaseModel):
    answer: bool = Field(..., description="Boolean to answer if you have enough information about the company.")


def find_alternatives(company_name, website):
    visited = WebsitesScraper().scrape([website])
    text = ""
    for key, value in visited.items():
        text += value

    history = History()
    history.system(f"{company_name} website: " + text)
    history.system(f"What is the search query for finding other website like {company_name}:")
    search = llm_strict(history, base_model=AlternativeSearch)
    return search


def scrape_competitor(competitor):
    # download website and check if it is downloable.
    print(competitor.website)
    scraped = WebsitesScraper().scrape([competitor.website])
    if len(scraped) == 0:
        return None

    text = ""
    for key, value in scraped.items():
        text += value

    # Check if you have enough information to get a clear idea of company X
    history = History()
    history.system(f"{competitor.name} website: " + text)
    history.system("Do you understand what the company does and have enough information about their website?")
    decision = llm_strict(history, base_model=InformationDecision)
    return decision


# run find competitors every month
def find_competitors(company: Company):

    search: AlternativeSearch = find_alternatives(company.name, company.website)

    # search on google for industry and company alternatives
    links = GoogleScraper().scrape_google(search.query, 5)

    # gather some pages
    visited = WebsitesScraper().scrape(links)

    # let chatgpt decide which names are competitors using strict inputs using name, website, instagram
    company_model = extract_competitors(visited, company.name)

    # for any missing website find the website using google
    competitor_ids = []
    for competitor in company_model.competitors:
        # TODO competitor website search
        # if competitor.website is None:
        #    competitor.website = search_google("What is the website for " + competitor.name)

        # put the competitors into the table
        # TODO what to do when the company already exists, can I add the competitor for this company then?
        competitor_data = {"Name": competitor.name, "Website": competitor.website, "Competitors": [company.id], "Competitors Scraped": "Skip"}
        competitor_id = create_if_not_exists(company_table, "Name", competitor.name, competitor_data)
        if competitor_id:
            competitor_ids.append(competitor_id)

    company_table.update(company.id, {"Competitors": competitor_ids, "Competitors Scraped": "Done"})


def todo_competitors():
    company_responses = company_table.all(formula="{Competitors Scraped}='Todo'")

    # Initialize an empty list to store companies with valid websites
    companies = []
    # Loop through each response and filter for valid URLs
    for company in company_responses:
        companies.append(Company(company["id"], company["createdTime"], company["fields"]))

    return companies


if __name__ == "__main__":
    companies = todo_competitors()
    for company in companies:
        find_competitors(company)
