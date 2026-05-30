import glob
import os

from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from core.gpt.history import History


def get_pages(folder):
    paths = os.path.join(folder, "*.txt").replace("\\", "/")
    pages = []
    for path in glob.glob(paths):
        loader = TextLoader(path, encoding="utf-8")
        pages.append(Document(page_content=" ".join([document.page_content for document in loader.load()]), metadata={"path": path}))
    return pages


def get_named_history(folder, name: str = "article"):
    paths = os.path.join(folder, "*.txt").replace("\\", "/")
    history = History()
    for index, path in enumerate(glob.glob(paths)):
        loader = TextLoader(path, encoding="utf-8")
        history.system(name + " " + str(index) + ": " + " ".join([document.page_content for document in loader.load()]))
    return history


def langchain_history(history: History):
    logs = []
    for log in history.logs:
        if log["role"] == "user":
            logs.append(HumanMessage(log["content"]))
        elif log["role"] == "assistant":
            logs.append(AIMessage(log["content"]))
        elif log["role"] == "system":
            logs.append(SystemMessage(log["content"]))
    return logs


def query_document(pages, query, embeddings, model="gpt-4o", history=None):
    if len(pages) > 166:
        pages = pages[:165]  # max buffer size

    vectorstore = FAISS.from_documents(pages, embeddings)
    chain = ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(temperature=0.0, model_name=model),
        retriever=vectorstore.as_retriever(),
    )

    if history is None:
        history = History()
    logs = langchain_history(history)

    chat = chain.invoke({"question": query, "chat_history": logs})["answer"]
    return chat
