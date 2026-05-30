import copy
import os

from dotenv import load_dotenv
from pyairtable import Base

load_dotenv()

BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
base = Base(AIRTABLE_API_KEY, BASE_ID)

COMPANY_TABLE_NAME = 'tblnICpfM49FKpyIu'
MEDIA_TABLE_NAME = 'tbl4LdxZrXBjfUckC'
company_table = base.table(COMPANY_TABLE_NAME)
media_table = base.table(MEDIA_TABLE_NAME)


def create_if_not_exists(table, key, value, data):
    matching_companies = table.all(formula="{" + key + "} = '" + value + "'")
    # Check if the company already exists
    if not matching_companies:
        # If no match is found, create the new company
        table_data = copy.deepcopy(data)
        table_data[key] = value
        new_company = table.create(table_data)
        print("Created:", new_company)
        return new_company["id"]
    else:
        print("Already exists:", matching_companies[0])
        return None


if __name__ == "__main__":
    create_if_not_exists(company_table, "Name", "Crescent Mall", {})
