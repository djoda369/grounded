import os

import rootpath
from hubspot.crm.companies import SimplePublicObjectWithAssociations

from core.helper.crm import hubspot_client, get_company_associations_to_notes, get_note_details
from core.helper.fireflies import extract_fireflies_data
from core.helper.knowledge import load_existing_companies, save_companies, load_existing_industries, save_industries

from path import DETECTED_PATH
from research.onboarding import extract_company_industry


def get_companies_industries():
    companies = load_existing_companies()
    industries = load_existing_industries()

    # Get all companies
    companies_data: list[SimplePublicObjectWithAssociations] = hubspot_client.crm.companies.get_all()
    for company_data in companies_data:
        if company_data.id in companies.keys():
            continue

        print(company_data.properties.items())
        company = company_data.properties
        company["company_id"] = company["domain"].split(".")[0]
        company["notes"] = []
        if "industry" not in company:
            company["name"], company["industry"] = extract_company_industry(company["domain"])
            if company["industry"] not in industries:

                industry_path = os.path.join(DETECTED_PATH, "data", "industry", company["industry"]).replace("\\", "/")
                if not os.path.exists(industry_path):
                    os.mkdir(industry_path)

                print(industries)
                industries[company["industry"]] = {
                    "topic": company["industry"],
                    "path": industry_path,
                    "companies": [company_data.id]
                }
            else:
                industry_node = industries[company["industry"]]
                if company_data.id not in industry_node["companies"]:
                    industry_node["companies"].append(company_data.id)

        companies[company_data.id] = company

    return companies, industries


# TODO make more efficient in which the notes are attached to the company, not from the company we check if the note is available for them.
def check_additional_notes(companies):
    # Get company associations to notes
    associations = get_company_associations_to_notes(companies)

    # Loop through each company and its associated notes
    for association in associations.results:
        company_id = association._from.id  # The company ID
        if company_id not in companies:
            # raise Exception("Unknown Company has notes???")
            continue  # potentially deleted contact?

        # Convert existing notes to a set for quick lookup
        existing_note_ids = {note["note_id"] for note in companies[company_id]["notes"]}

        # Loop through each note associated with this company
        for note_id in association.to:
            if note_id.id in existing_note_ids:  # Check if note is already fetched
                continue

            note_details = get_note_details(note_id.id)
            note_data = extract_fireflies_data(note_details.properties.get("hs_note_body"))
            note_data["note_id"] = note_id.id
            companies[company_id]["notes"].append(note_data)
    return companies


if __name__ == "__main__":
    # Load existing notes to avoid re-fetching
    c, i = get_companies_industries()

    c = check_additional_notes(c)

    save_companies(c)
    save_industries(i)
