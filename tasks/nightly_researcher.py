import json

from research.researcher import IndustryResearcher


# Nightly Researcher surveys for new insights from industry:
class NightlyResearcher(IndustryResearcher):

    def __init__(self, node_name):
        super().__init__(node_name)

    def request_google_results(self, query, request_topic='scrape_google'):
        request_data = {"query": query, "topic": self.result_topic}
        self.publish(request_topic, json.dumps(request_data))
        print(f"Requested Google scrape for query: '{query}' on topic: '{request_topic}'")

    def request_youtube_news(self, query, request_topic='youtube_news'):
        request_data = {"query": query, "topic": self.result_topic}
        self.publish(request_topic, json.dumps(request_data))
        print(f"Requested Google scrape for query: '{query}' on topic: '{request_topic}'")

    def request_research_papers(self, query, request_topic='research_papers'):
        request_data = {"query": query, "topic": self.result_topic}
        self.publish(request_topic, json.dumps(request_data))
        print(f"Requested Google scrape for query: '{query}' on topic: '{request_topic}'")


if __name__ == "__main__":
    owl = NightlyResearcher("OWL")