import glob
import json
import os

import rootpath as rootpath
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel, Field

from core.gpt.chatgpt import llm_strict
from core.gpt.history import History
from core.helper.files import json_read_file, read_file, write_to_file
from path import DETECTED_PATH

conversation_files = os.path.join(DETECTED_PATH, "data", "conversations.json").replace("\\", "/")
companies_file = os.path.join(DETECTED_PATH, "data", "companies.json").replace("\\", "/")
industries_file = os.path.join(DETECTED_PATH, "data", "industries.json").replace("\\", "/")
encoding = "utf-8"

index_path = os.path.join(DETECTED_PATH, "data", "index").replace("\\", "/")
embeddings_function = OpenAIEmbeddings()


def load_existing_conversations():
    """Load existing notes from a JSON file if it exists."""
    if os.path.exists(conversation_files):
        with open(conversation_files, "r", encoding=encoding) as file:
            return json.load(file)
    return {}


def save_conversations(conversations_dict):
    conversations_json = json.dumps(conversations_dict, indent=4)
    with open(conversation_files, "w", encoding=encoding) as file:
        file.write(conversations_json)


def load_existing_industries():
    """Load existing notes from a JSON file if it exists."""
    if os.path.exists(industries_file):
        with open(industries_file, "r", encoding=encoding) as file:
            return json.load(file)
    return {}


def save_industries(industries_dict):
    industries_json = json.dumps(industries_dict, indent=4)
    with open(industries_file, "w", encoding=encoding) as file:
        file.write(industries_json)


def load_existing_companies():
    """Load existing notes from a JSON file if it exists."""
    if os.path.exists(companies_file):
        with open(companies_file, "r", encoding=encoding) as file:
            return json.load(file)
    return {}


def save_companies(companies_dict):
    companies_json = json.dumps(companies_dict, indent=4)
    with open(companies_file, "w", encoding=encoding) as file:
        file.write(companies_json)


def read_company_meetings(company_id):
    companies = load_existing_companies()
    meeting_info = []
    for company_key in companies:
        company = companies[company_key]
        if company["company_id"] != company_id:
            continue

        if "notes" not in company:
            continue

        for note in company["notes"]:
            if "summary" in note:
                text = note['summary']
            elif "message" in note:
                text = note['message']
            else:
                print("unknown note format", note)
                continue
            meeting_info.append(f"Meeting with {company['name']}: {text}")

        # given that this is the company_id we don't have to find any other anymore.
        break

    return meeting_info


def webpage_pages(company_folder: str = "grounded_world"):
    paths = os.path.join(DETECTED_PATH, "data", "website", company_folder, "*.txt").replace("\\", "/")
    pages = []
    for path in glob.glob(paths):
        loader = TextLoader(path, encoding="utf-8")
        pages.extend(loader.load_and_split())
    return pages


def slack_pages(selected_channel: str = "C048TBKBBC3"):
    path = os.path.join(DETECTED_PATH, "data", "slack", "slack_links.json").replace("\\", "/")
    data = json_read_file(path)
    pages = []
    for channel in data:
        if channel == selected_channel:
            for link in data[channel]:
                if "text" in data[channel][link]:
                    document = Document(page_content=data[channel][link]["text"], metadata={"url": link, "channel": channel})
                    pages.append(document)
    return pages


def read_slack(path: str):
    path = os.path.join(DETECTED_PATH, path).replace("\\", "/")
    print(path)

    data = json_read_file(path)
    pages = []
    for link in data:
        if "text" in data[link]:
            document = Document(page_content=data[link]["text"], metadata={"url": link})
            pages.append(document)
    return pages


def read_thought_slack():
    path = os.path.join(DETECTED_PATH, "thoughtleadership", "*.txt").replace("\\", "/")
    print(path)

    pages = []
    for path in glob.glob(path):
        loader = TextLoader(path, encoding="utf-8")
        pages.extend(loader.load_and_split())
    return pages


class SummarizeModel(BaseModel):
    summary: str = Field(..., description="Give a summary of the key insights either pertaining to sustainable fashion of grounded.")


def summarize_thoughts():
    path = os.path.join(DETECTED_PATH, "thoughtleadership", "*.txt").replace("\\", "/")

    pages = []
    for path in glob.glob(path):
        print(path)
        text = read_file(path)
        history = History()
        history.system(text)
        answer = llm_strict(history, "gpt-4o", SummarizeModel)
        write_to_file(path, answer.summary)
    return pages

def refresh_index():
    pages = read_thought_slack()
    db = FAISS.from_documents(pages, embeddings_function)
    db.save_local(index_path, "sustainable_fashion")


if __name__ == "__main__":
    pages = read_thought_slack()
    db = FAISS.from_documents(pages, embeddings_function)
    db.save_local(index_path, "sustainable_fashion")
