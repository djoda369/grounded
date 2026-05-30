import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from core.gpt.chatgpt import llm_chat
from core.gpt.history import History
from core.helper.files import json_read_file

CSV_FILE = "../communication/data/gaia_slack.csv"
JSON_FILE = "../communication/data/weekly_summaries.json"


def find_closest_newsletter(company_data):
    json_data = json_read_file(JSON_FILE)
    documents = []
    for channel in json_data:
        documents.append(Document(page_content=json_data[channel], metadata={"id": channel}))
    new_db = FAISS.from_documents(documents, OpenAIEmbeddings())

    for _, document in enumerate(new_db.similarity_search(company_data, k=1)):
        print(document.page_content)
        history = History()
        history.user("Newsletter: " + document.page_content)
        history.user("Customer: " + company_data)
        history.system("Customize the Newsletter to highlight the most relevant aspects to customer.")
        history.system("This newsletter is being written by Gaia from GroundedWorld.")
        return llm_chat(history)
    return None


if __name__ == "__main__":

    st.title("Newsletter Generator")

    # Text box to input customer information
    customer_info = st.text_area("Enter customer information:")

    # Button to show a message
    if st.button("Submit"):
        if customer_info:
            with st.spinner("Loading..."):
                answer = find_closest_newsletter(customer_info)
                st.markdown(answer)
        else:
            st.error("Please enter customer information before submitting.")