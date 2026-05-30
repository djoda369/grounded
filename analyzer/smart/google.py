from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from analyzer.scrape.google import GoogleScraper
from data.topics.GroundedWorld.reader import document_embeddings


class SmartGoogler(GoogleScraper):
    def __init__(self, limit: int = 10, result_count: int = 5):
        super().__init__(limit)
        self.result_count: int = result_count

    def scrape(self, request):
        if "query" not in request:
            request["error"] = "Query not in request"
            return request

        search = super().scrape(request)
        pages = []
        for url in search:
            google_result = search[url]
            text = ""
            for key in google_result:
                if key != "url":
                    text += str(key) + ": " + str(google_result[key])
            pages.append(Document(page_content=text, metadata=google_result))

        return self.find_relevant_pages(pages, request["query"])

    def find_relevant_pages(self, pages: list[Document], query: str):
        print("find relevant", len(pages))
        vectorstore = FAISS.from_documents(pages, document_embeddings)
        docs = vectorstore.similarity_search(query, k=self.result_count)
        links = {}
        for doc in docs:
            print(doc.metadata)
            links[doc.metadata["url"]] = doc.metadata
        return links


# Example usage
if __name__ == '__main__':
    google_scraper = SmartGoogler()
    results = google_scraper.scrape({"query": "What is special about the company Grounded World"})
    print(results)
