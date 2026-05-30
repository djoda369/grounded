
import re

import pandas as pd
import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from core.gpt.chatgpt import llm_chat
from core.gpt.history import History
from core.helper.files import json_read_file
from research.website import WebsiteScraper

CSV_FILE = "communication/data/gaia_slack.csv"


def is_valid_url(text):
    """
    Check if the given text is a valid URL.

    Args:
        text (str): The text to validate as a URL.

    Returns:
        bool: True if the text is a valid URL, False otherwise.
    """
    url_pattern = re.compile(
        r'^(https?://)?'  # Optional scheme (http or https)
        r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'  # Domain name
        r'(:\d+)?'  # Optional port
        r'(/[\w.-]*)*'  # Path
        r'(\?[^\s#]*)?'  # Optional query
        r'(#[^\s]*)?$'  # Optional fragment
    )
    return bool(url_pattern.match(text))


def classify_channel(webpage_information, pages):
    new_db = FAISS.from_documents(pages, OpenAIEmbeddings())

    for index, document in enumerate(new_db.similarity_search(webpage_information, k=1)):
        return document.page_content, document.metadata

    return None, None




if __name__ == "__main__":

    if "channels" not in st.session_state:
        # Step 1: Read the CSV file
        df = pd.read_csv(CSV_FILE)
        st.session_state.pages = []
        # Step 2: Fetch and store messages
        st.session_state.channels = {}
        for _, row in df.iterrows():
            category = row["Category"]
            channel = row["Channel"]
            channel_id = row["ID"]
            st.session_state.channels[channel_id] = category + " - " + channel
            st.session_state.pages.append(Document(page_content=category + " - " + channel, metadata={"id": channel_id}))

    st.title("Gaia: Article Sorter Slack")

    # Dropdown to select a Slack channel
    website_link = st.text_input("Link to interesting article or website")

    if st.button("Submit") and website_link:
        duplicate = False
        scraped = False
        summarized = False
        found = False

        raw_links = json_read_file("communication/data/raw_links.json")["links"]
        if website_link in raw_links:
            duplicate = True

        if not duplicate:
            if is_valid_url(website_link):

                with st.spinner("Scraping Website..."):
                    website = WebsiteScraper()
                    text = website.scrape(website_link)
                    if text:
                        st.success("Scraped the website.")
                        scraped = True
                    else:
                        st.error("Unable to scrape the website.")

                if scraped:
                    with st.spinner("Summarizing Website..."):
                        history = History()
                        history.system("Just scraped the website " + website_link)
                        history.user("Website text: " + text)
                        history.system("Summarize the website:")
                        summary = llm_chat(history)

                        st.info("Summary: " + summary)
                        summarized = True

                if summarized:
                    with st.spinner("Assigning to Slack Channel..."):
                        channel, id = classify_channel(summary, st.session_state.pages)
                        if channel:
                            st.success("Found most fitting slack channel: " + channel)

                            found = True

                        else:
                            st.error("Could not find channel to align with.")

                if found:
                    if st.button("Post directly in slack through Gaia"):
                        # TODO pass
                        pass
            else:
                st.error("I don't recognize this as a valid website page.")
        else:
            st.info("This link has already been published.")
