import glob
import os
import shutil

import fitz
import rootpath
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

from core.gpt.chatgpt import llm_chat
from core.gpt.history import History, langchain_history
from core.helper.files import write_to_file, read_file
from path import DETECTED_PATH

document_embeddings = OpenAIEmbeddings()


def query_document(pages, query, model="gpt-4o", history=None):
    if len(pages) > 166:
        pages = pages[:165]  # max buffer size
    if history is None:
        history = History()
    print(len(pages))
    vectorstore = FAISS.from_documents(pages, document_embeddings)

    chain = ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(temperature=0.0, model_name=model),
        retriever=vectorstore.as_retriever(),
    )
    logs = langchain_history(history)
    chat = chain.invoke({"question": query, "chat_history": logs})["answer"]
    return chat


def read_pdf_path(file_path):
    document = fitz.open(file_path, filetype="pdf")
    text = ""
    for page_num in range(document.page_count):
        page = document.load_page(page_num)
        text += page.get_text()
    return text


def read_pages(folder):
    pages = []
    paths = os.path.join(folder, "*.pdf").replace("\\", "/")
    print(paths)
    for path in glob.glob(paths):
        print(path)
        text = read_pdf_path(path)
        history = History()
        history.system(text)
        history.system("Summarize content above:")
        summary = llm_chat(history)
        write_to_file(path.replace(".pdf", ".txt").replace(" ", "_"), summary)
    return pages


def read_context_grounded():
    texts = []
    paths = os.path.join(DETECTED_PATH, "data", "topics", "GroundedWorld", "*.txt").replace("\\", "/")
    print(paths)
    for path in glob.glob(paths):
        texts.append(read_file(path))
    return texts


def move_files():
    texts = []
    paths = os.path.join(DETECTED_PATH, "data", "topics", "GroundedWorld", "*.txt").replace("\\", "/")
    print(paths)
    for path in glob.glob(paths):
        if " " in path:
            shutil.move(path, path.replace(" ", "_"))
    return texts


if __name__ == "__main__":
    #read_pages(".")
    move_files()
