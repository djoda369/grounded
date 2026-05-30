import json


class IndustryResearcher:
    def __init__(self, node_name):
        super().__init__(node_name)
        self.result_topic = "market_research"

    def handle(self, message):
        data = json.loads(message['data'])
        print(f"Received scraped data on topic '{self.result_topic}': {data}")


# Example usage
if __name__ == '__main__':
    # Initialize the Google scraper client
    google_client = IndustryResearcher('google_tester_node')

    # Request Google scrape with the desired query
    query = "What are the trends for the automotive industry?"
    google_client.request_google_scrape(query)

    # Start listening for results on the specified topic
    google_client.start_listening_for_results()
